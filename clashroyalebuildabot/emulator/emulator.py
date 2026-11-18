import base64
import re
import subprocess
import threading
import time

import av
from loguru import logger
from PIL.Image import Image

from clashroyalebuildabot.constants.paths import ADB_PATH, APP_DIR
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.install import adb_installed
from clashroyalebuildabot.utils.error_handling import WikifiedError


def parse_wm_size(output: str) -> tuple[int, int]:
    """Read the screen size from ``adb shell wm size``.

    With an override set (``wm size 720x1280``) it prints both the physical
    and the override size; apps render at the override, so that one wins.
    """
    sizes = dict(
        (kind, (int(w), int(h)))
        for kind, w, h in re.findall(r"(\w+) size: (\d+)x(\d+)", output)
    )
    if "Override" in sizes:
        return sizes["Override"]
    if "Physical" in sizes:
        return sizes["Physical"]
    raise ValueError(f"Can't read the screen size from {output!r}")


def recording_size(width: int, height: int) -> tuple[int, int]:
    """The size the device records at: as small as the bot's screenshots
    while keeping the screen's shape, so the device doesn't encode and send
    pixels that would only be thrown away.

    Both sides are multiples of 16, the block size of H.264, since some
    phones' encoders reject anything else.
    """
    scale = SCREENSHOT_WIDTH / width
    return (
        _round_to_16(SCREENSHOT_WIDTH),
        _round_to_16(height * scale),
    )


def _round_to_16(n: float) -> int:
    return max(16, round(n / 16) * 16)


def recording_script(width: int, height: int) -> str:
    """The shell script that streams the screen as H.264 to stdout.

    screenrecord stops after at most 3 minutes, so it runs in a loop. If the
    device can't record at the small size, it records at full size instead,
    and the bot scales the frames down itself. If that fails too, the sleep
    stops the loop from spinning.
    """
    small_w, small_h = recording_size(width, height)
    record = (
        "screenrecord --output-format=h264 --time-limit 179 "
        '--bit-rate "5M" --size "{}x{}" -'
    )
    return (
        "#!/bin/bash\n"
        "while true; do\n"
        f"    {record.format(small_w, small_h)} ||\n"
        f"    {record.format(width, height)} ||\n"
        "    sleep 1\n"
        "done\n"
    )


class Emulator:
    # screenrecord only sends a frame when the screen changes, so a quiet
    # stream usually means a static screen, not a dead one.
    FRAME_TIMEOUT = 5
    # The first frame arrives as soon as recording starts.
    FIRST_FRAME_TIMEOUT = 15

    def __init__(self, device_serial):
        self.device_serial = device_serial

        self.frame_thread = None
        self.video_process = None
        self._closed = threading.Event()
        self._stream_ended = threading.Event()
        self._last_frame = None
        self.frame = None
        self.codec = av.codec.CodecContext.create("h264", "r")

        self._check_adb()
        self._restart_server()
        self.device_serial = self._get_valid_device_serial()
        self.width, self.height = self._get_width_and_height()
        self._start_recording()
        self._start_updating_frame()

    def _get_valid_device_serial(self):
        try:
            logger.info(
                f"Trying to connect to device '{self.device_serial}' from config."
            )
            self._run_command(["get-state"])
            logger.info(
                f"Successfully connected to the device '{self.device_serial}' from config."
            )
            return self.device_serial
        except Exception as e:
            logger.warning(
                f"Device '{self.device_serial}' not found or not accessible: {str(e)}"
            )
            logger.warning(
                "Trying to find a connected device via adb devices..."
            )

            try:
                devices_output = subprocess.check_output(
                    [ADB_PATH, "devices"]
                ).decode("utf-8")
                available_devices = [
                    line.split()[0]
                    for line in devices_output.splitlines()
                    if "\tdevice" in line
                ]

                if not available_devices:
                    raise WikifiedError(
                        "006", "No connected devices found"
                    ) from e

                fallback_device_serial = available_devices[0]
                logger.info(
                    f"Using the first available device: {fallback_device_serial}"
                )
                return fallback_device_serial
            except subprocess.CalledProcessError as adb_error:
                logger.error(
                    f"Failed to execute adb devices: {str(adb_error)}"
                )
                raise WikifiedError(
                    "006", "Could not find a valid device to connect to."
                ) from adb_error

    def _start_recording(self):
        cmd = recording_script(self.width, self.height)
        cmd = base64.standard_b64encode(cmd.encode("utf-8")).decode("utf-8")
        cmd = ["echo", cmd, "|", "base64", "-d", "|", "sh"]
        cmd = " ".join(cmd) + "\n"
        self.video_process = subprocess.Popen(
            [ADB_PATH, "-s", self.device_serial, "shell", cmd],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            bufsize=0,
        )

    def _check_adb(self):
        if not adb_installed():
            raise WikifiedError(
                "011",
                f"ADB isn't installed at {ADB_PATH}. Run "
                "`uv run python -m clashroyalebuildabot.install` in the "
                "project folder.",
            )

    def _run_command(self, command):
        command = [ADB_PATH, "-s", self.device_serial, *command]
        logger.debug(" ".join(command))
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                cwd=APP_DIR,
                capture_output=True,
                check=True,
                text=True,
            )
            end_time = time.time()
            logger.debug(
                f"Command executed in {end_time - start_time} seconds"
            )
        except subprocess.CalledProcessError as e:
            logger.error(str(e))
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise WikifiedError("007", "ADB command failed.") from e

        return result.stdout

    def _device_reachable(self) -> bool:
        try:
            result = subprocess.run(
                [ADB_PATH, "-s", self.device_serial, "get-state"],
                cwd=APP_DIR,
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _restart_server(self):
        # Restarting the server drops wireless-debugging connections, which
        # don't always come back, so only do it when the device isn't
        # already reachable.
        if self._device_reachable():
            return
        self._run_command(
            [
                "kill-server",
            ]
        )
        self._run_command(["start-server"])

    def _update_frame(self):
        try:
            self._read_frames()
        finally:
            self._stream_ended.set()
            if not self._closed.is_set():
                logger.error("The video stream from the device stopped.")

    def _read_frames(self):
        logger.debug("Starting to update frames...")
        if self.video_process is None:
            logger.error("Video process is None")
            return

        video_stdout = self.video_process.stdout
        if video_stdout is None:
            logger.error("Video process stdout is None")
            return

        for line in iter(video_stdout.readline, b""):
            try:
                last_frame = self._get_last_frame(line)
                if not last_frame:
                    continue

                image = last_frame.reformat(
                    width=SCREENSHOT_WIDTH,
                    height=SCREENSHOT_HEIGHT,
                    format="rgb24",
                ).to_image()
                self._last_frame = image
                self.frame = image
            except Exception as e:
                logger.error(f"Unexpected error in frame update: {str(e)}")

    def _get_last_frame(self, line):
        if not line:
            return None

        # Every packet must be decoded, even if only the newest frame is
        # kept: H.264 frames depend on earlier ones, and the first packet
        # carries the stream headers.
        frames = []
        for packet in self.codec.parse(line):
            frames.extend(self.codec.decode(packet))
        return frames[-1] if frames else None

    def _start_updating_frame(self):
        self.frame_thread = threading.Thread(target=self._update_frame)
        self.frame_thread.daemon = True
        self.frame_thread.start()

    def _get_width_and_height(self):
        return parse_wm_size(self._run_command(["shell", "wm", "size"]))

    def close(self):
        """Stop the screen recording and the frame thread. Safe to call twice."""
        if self._closed.is_set():
            return
        self._closed.set()

        if self.video_process is not None:
            self.video_process.terminate()
            try:
                self.video_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.video_process.kill()
                self.video_process.wait()

        # Terminating the process closes its stdout, which ends _update_frame.
        if self.frame_thread is not None:
            self.frame_thread.join(timeout=5)
        logger.debug("Emulator closed.")

    def stop_game(self):
        self._run_command(
            ["shell", "am", "force-stop", "com.supercell.clashroyale"]
        )

    def start_game(self):
        self._run_command(
            [
                "shell",
                "am",
                "start",
                "-n",
                "com.supercell.clashroyale/com.supercell.titan.GameApp",
            ]
        )

    def click(self, x, y):
        self.tap_sequence([(x, y)])

    def tap_sequence(self, points):
        """Tap each point in turn, in one adb command.

        Each adb command costs a round trip to the device, and each
        ``input`` a process start on it, so playing a card (tap the card,
        then the tile) is sent as one.
        """
        taps = [f"input tap {round(x)} {round(y)}" for x, y in points]
        self._run_command(["shell", " && ".join(taps)])

    def take_screenshot(self) -> Image | None:
        """
        Wait for the next frame.

        If no new frame arrives within FRAME_TIMEOUT, the screen hasn't
        changed, so the last frame is returned. Returns None once the
        emulator is closed. Raises WikifiedError if the stream has stopped
        or the first frame never arrives.
        """
        logger.debug("Starting to take screenshot...")
        timeout = (
            self.FRAME_TIMEOUT
            if self._last_frame is not None
            else self.FIRST_FRAME_TIMEOUT
        )
        deadline = time.monotonic() + timeout
        while self.frame is None:
            if self._closed.is_set():
                return None
            if self._stream_ended.is_set():
                raise WikifiedError(
                    "008", "Lost the video stream from the device."
                )
            if time.monotonic() >= deadline:
                if self._last_frame is None:
                    raise WikifiedError(
                        "008",
                        f"No video from the device after {timeout} seconds.",
                    )
                logger.debug("No new frame, reusing the last one.")
                return self._last_frame
            time.sleep(0.01)

        screenshot, self.frame = self.frame, None

        return screenshot

    def load_deck(self, cards):
        id_str = ";".join([str(card.id_) for card in cards])
        slot_str = ";".join("0" for _ in range(len(cards)))
        url = "&".join(
            [
                f"https://link.clashroyale.com/en/?clashroyale://copyDeck?deck={id_str}",
                f"slots={slot_str}",
                "tt=159000000",
                "l=Royals",
                "id=JR2RU0L90",
            ]
        )

        self._run_command(
            [
                "shell",
                "am",
                "start",
                "-n",
                "com.android.chrome/com.google.android.apps.chrome.Main",
                "-d",
                f"'{url}'",
            ]
        )
        input("Press a key when you've finished copying the deck ")
