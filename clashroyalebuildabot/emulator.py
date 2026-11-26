import re
import subprocess
import threading
import time
from collections.abc import Sequence

import numpy as np
from loguru import logger

from clashroyalebuildabot.constants.device_screen import (
    DISPLAY_DENSITY,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
)
from clashroyalebuildabot.constants.paths import ADB_PATH, APP_DIR
from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.install import (
    ADB_VERSION,
    adb_installed,
    adb_up_to_date,
    install_adb,
)
from clashroyalebuildabot.jpeg_screen import (
    DISPLAY_OFF,
    JpegScreen,
    ScreenServerError,
)
from clashroyalebuildabot.utils.error_handling import WikifiedError


def parse_wm_setting(output: str, setting: str) -> tuple[str | None, str]:
    """(override, physical) from ``adb shell wm size`` or ``wm density``,
    e.g. (None, "1080x2400") or ("240", "420"). Override is None if there's
    none."""
    found = dict(re.findall(rf"(Physical|Override) {setting}: (\S+)", output))
    if "Physical" not in found:
        raise ValueError(f"Can't read the screen {setting} from {output!r}")
    return found.get("Override"), found["Physical"]


# The screen server mirrors the display with a call Android added in 14.
MIN_SDK = 34


class Emulator:
    # How long the screen server may go without a picture: before the first
    # one, and once the bot has had one.
    FIRST_FRAME_TIMEOUT = 15
    FRAME_TIMEOUT = 5
    # How often to ask again while the JPEG server has no picture yet, or
    # the screen is off.
    JPEG_RETRY_DELAY = 0.05
    SCREEN_OFF_RETRY_DELAY = 0.5

    def __init__(self, device_serial: str) -> None:
        self.device_serial = device_serial

        # Sends the frames: see jpeg_screen.py.
        self.screen: JpegScreen | None = None
        # (setting, value) to put back on close: what the device had before
        # _set_display changed it, or "reset" for its own.
        self._display_restore: list[tuple[str, str]] = []
        # A shell on the device that taps are written to, opened on the
        # first tap. Guarded by the lock, as close() may run on another
        # thread.
        self.input_shell: subprocess.Popen | None = None
        self._input_lock = threading.Lock()
        self._closed = threading.Event()
        self._last_frame: np.ndarray | None = None

        self._check_adb()
        self._restart_server()
        self.device_serial = self._get_valid_device_serial()
        self._check_android_version()
        try:
            self._set_display()
            self._start_screen()
        except BaseException:
            # Puts the display back, and stops whatever had started.
            self.close()
            raise

    def _set_display(self) -> None:
        """Set the device's screen to the size and density the bot reads it
        at, remembering what it had to put back on close. Changing them
        makes the game reload, so they're left alone if already right."""
        targets = {
            "size": f"{DISPLAY_WIDTH}x{DISPLAY_HEIGHT}",
            "density": str(DISPLAY_DENSITY),
        }
        for setting, target in targets.items():
            output = self._run_command(["shell", "wm", setting])
            override, physical = parse_wm_setting(output, setting)
            current = override or physical
            if current == target:
                continue
            self._run_command(["shell", "wm", setting, target])
            self._display_restore.append((setting, override or "reset"))
            logger.info(
                f"Set the device's screen {setting} to {target} while the "
                f"bot runs (it was {current})."
            )

    def _restore_display(self) -> None:
        """Undo _set_display. Never raises: it runs as the bot stops."""
        restore, self._display_restore = self._display_restore, []
        for setting, value in reversed(restore):
            try:
                self._run_command(["shell", "wm", setting, value])
            except Exception as e:
                logger.warning(
                    f"Couldn't put the device's screen {setting} back "
                    f"({e}). Run `platform-tools/adb shell wm {setting} "
                    f"{value}` to do it yourself."
                )

    def _check_android_version(self) -> None:
        output = self._run_command(
            ["shell", "getprop", "ro.build.version.sdk"]
        )
        sdk = int(output.strip())
        if sdk < MIN_SDK:
            release = self._run_command(
                ["shell", "getprop", "ro.build.version.release"]
            ).strip()
            raise WikifiedError(
                "013",
                f"The device runs Android {release} (API {sdk}), but the bot "
                f"needs Android 14 (API {MIN_SDK}) or newer.",
            )

    def _start_screen(self) -> None:
        try:
            self.screen = self._start_jpeg_screen()
        except ScreenServerError as e:
            raise WikifiedError(
                "008", f"Couldn't start the screen server on the device: {e}"
            ) from e

    def _start_jpeg_screen(self) -> JpegScreen:
        return JpegScreen(self.device_serial)

    def _get_valid_device_serial(self) -> str:
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
                f"Device '{self.device_serial}' not found or not accessible: {e!s}"
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
                logger.error(f"Failed to execute adb devices: {adb_error!s}")
                raise WikifiedError(
                    "006", "Could not find a valid device to connect to."
                ) from adb_error

    def _check_adb(self) -> None:
        if adb_up_to_date():
            return
        try:
            install_adb()
        except Exception as e:
            if adb_installed():
                logger.warning(
                    f"Couldn't update ADB to {ADB_VERSION} ({e}), "
                    "using the installed version"
                )
                return
            raise WikifiedError(
                "011",
                f"ADB isn't installed at {ADB_PATH} and installing it "
                f"failed: {e}. Run "
                "`uv run python -m clashroyalebuildabot.install` in the "
                "project folder.",
            ) from e

    def _run_command(self, command: list[str]) -> str:
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
                check=False,
                cwd=APP_DIR,
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _restart_server(self) -> None:
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

    def close(self) -> None:
        """Stop the screen server and the input shell, and put the display
        back. Safe to call twice, and from another thread."""
        if self._closed.is_set():
            return
        self._closed.set()

        # Unblocks a take_screenshot() waiting on it.
        if self.screen is not None:
            self.screen.close()

        with self._input_lock:
            self._stop_input_shell()

        self._restore_display()
        logger.debug("Emulator closed.")

    def stop_game(self) -> None:
        self._run_command(
            ["shell", "am", "force-stop", "com.supercell.clashroyale"]
        )

    def start_game(self) -> None:
        self._run_command(
            [
                "shell",
                "am",
                "start",
                "-n",
                "com.supercell.clashroyale/com.supercell.titan.GameApp",
            ]
        )

    def click(self, x: float, y: float) -> None:
        self.tap_sequence([(x, y)])

    def tap_sequence(self, points: Sequence[tuple[float, float]]) -> None:
        """Tap each point in turn, as one line to a shell on the device.

        Starting an adb command costs a process and a connection to the
        device, so the shell is opened once and kept. Each ``input`` costs a
        process start on the device, so playing a card (tap the card, then
        the tile) is sent as one line. It returns as soon as the line is
        sent, without waiting for the taps to finish.
        """
        taps = [f"input tap {round(x)} {round(y)}" for x, y in points]
        command = " && ".join(taps)
        with self._input_lock:
            if self._closed.is_set():
                return
            # A shell that died, e.g. when wireless adb dropped, is replaced
            # once. If the new one fails too, a one-off command reports why.
            for _ in range(2):
                if self._send_to_input_shell(command):
                    return
                logger.warning("The input shell stopped, restarting it.")
                self._stop_input_shell()
        self._run_command(["shell", command])

    def _send_to_input_shell(self, command: str) -> bool:
        """Write a command line to the input shell, opening it if needed.
        Returns False if the shell isn't running."""
        if self.input_shell is None:
            self.input_shell = self._start_input_shell()
        stdin = self.input_shell.stdin
        if self.input_shell.poll() is not None or stdin is None:
            return False
        try:
            stdin.write(f"{command}\n".encode())
            stdin.flush()
        except OSError:  # BrokenPipeError: the shell has gone
            return False
        return True

    def _start_input_shell(self) -> subprocess.Popen:
        # -T: no terminal, so the shell runs each line it reads from stdin.
        return subprocess.Popen(
            [ADB_PATH, "-s", self.device_serial, "shell", "-T"],
            cwd=APP_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_input_shell(self) -> None:
        """Close the input shell, if open. Call with the lock held."""
        shell, self.input_shell = self.input_shell, None
        if shell is None:
            return
        try:
            if shell.stdin is not None:
                shell.stdin.close()  # the shell exits at end of input
        except OSError:
            pass
        try:
            shell.wait(timeout=2)
        except subprocess.TimeoutExpired:
            shell.kill()
            shell.wait()

    def take_screenshot(self) -> np.ndarray | None:
        """The newest frame, as a (height, width, 3) RGB array, from the
        screen server. If the screen hasn't changed since the last one,
        that's still the newest. While the screen is off, waits for it to
        come on.

        Returns None once the emulator is closed. Raises WikifiedError if
        the connection to the server is lost, or no picture comes.
        """
        screen = self.screen
        if screen is None:
            return None
        timeout = (
            self.FRAME_TIMEOUT
            if self._last_frame is not None
            else self.FIRST_FRAME_TIMEOUT
        )
        deadline = time.monotonic() + timeout
        warned_off = False
        while not self._closed.is_set():
            try:
                frame = screen.frame()
            except (OSError, EOFError, ScreenServerError) as e:
                if self._closed.is_set():
                    return None
                raise WikifiedError(
                    "008", "Lost the connection to the screen server."
                ) from e
            if frame.image is not None:
                self._last_frame = frame.image
                return frame.image
            if frame.status == DISPLAY_OFF:
                if not warned_off:
                    logger.warning(
                        "The device's screen is off. Waiting for it to "
                        "come on."
                    )
                    warned_off = True
                self._closed.wait(self.SCREEN_OFF_RETRY_DELAY)
                deadline = time.monotonic() + timeout
                continue
            if self._last_frame is not None:
                return self._last_frame
            if time.monotonic() >= deadline:
                raise WikifiedError(
                    "008",
                    f"No picture from the device after {timeout} seconds.",
                )
            self._closed.wait(self.JPEG_RETRY_DELAY)
        return None

    def load_deck(self, cards: Sequence[Card]) -> None:
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
