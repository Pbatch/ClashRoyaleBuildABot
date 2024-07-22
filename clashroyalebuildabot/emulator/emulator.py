# pylint: disable=consider-using-with

import base64
import os
import platform
import subprocess
import threading
import time
import zipfile

import av
from loguru import logger
import requests
from tqdm import tqdm

from clashroyalebuildabot.constants import ADB_DIR
from clashroyalebuildabot.constants import ADB_PATH
from clashroyalebuildabot.constants import EMULATOR_DIR
from clashroyalebuildabot.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.constants import SCREENSHOT_WIDTH


class Emulator:
    def __init__(self, device_serial, ip):
        self.device_serial = device_serial
        self.ip = ip

        self.frame_thread = None
        self.video_thread = None
        self.frame = None
        self.codec = av.codec.CodecContext.create("h264", "r")
        self.os_name = platform.system().lower()

        self._install_adb()
        self._restart_server()
        self.width, self.height = self._get_width_and_height()
        self._start_recording()
        self._start_updating_frame()

    def _start_recording(self):
        cmd = f"""#!/bin/bash
        while true; do
            screenrecord --output-format=h264 --time-limit "179" --size "{self.width}x{self.height}" --bit-rate "5M" -
        done\n"""
        cmd = base64.standard_b64encode(cmd.encode("utf-8")).decode("utf-8")
        cmd = ["echo", cmd, "|", "base64", "-d", "|", "sh"]
        cmd = " ".join(cmd) + "\n"
        self.video_thread = subprocess.Popen(
            [ADB_PATH, "-s", self.device_serial, "shell", cmd],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            bufsize=0,
        )

    def _install_adb(self):
        if os.path.isdir(ADB_DIR):
            return

        basename = f"platform-tools-latest-{self.os_name}.zip"
        zip_path = os.path.join(EMULATOR_DIR, basename)
        adb_url = f"https://dl.google.com/android/repository/{basename}"

        response = requests.get(adb_url, stream=True, timeout=60)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        chunk_size = 1024 * 1024  # 1 MB chunks
        total_size_mb = total_size / chunk_size

        with open(zip_path, "wb") as file:
            with tqdm(
                unit="MB",
                desc="Downloading ADB",
                unit_scale=True,
                unit_divisor=1024,
                total=total_size_mb,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        size = file.write(chunk)
                        pbar.update(size / chunk_size)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(EMULATOR_DIR)
        os.remove(zip_path)

    def _run_command(self, command):
        command = [ADB_PATH, "-s", self.device_serial, *command]
        logger.debug(" ".join(command))
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                cwd=EMULATOR_DIR,
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
            raise

        if result.returncode != 0:
            logger.error(f"Error executing command: {result.stderr}")
            raise RuntimeError("ADB command failed")

        return result.stdout

    def _restart_server(self):
        self._run_command(
            [
                "kill-server",
            ]
        )
        self._run_command(["start-server"])

    def _update_frame(self):
        for line in iter(self.video_thread.stdout.readline, b""):
            try:
                if not line:
                    continue

                if self.os_name == "windows":
                    line = line.replace(b"\r\n", b"\n")

                packets = self.codec.parse(line)
                if len(packets) == 0:
                    continue

                frames = self.codec.decode(packets[-1])
                if len(frames) == 0:
                    continue

                self.frame = (
                    frames[-1]
                    .reformat(
                        width=SCREENSHOT_WIDTH,
                        height=SCREENSHOT_HEIGHT,
                        format="rgb24",
                    )
                    .to_image()
                )

            except Exception as e:
                logger.error(str(e))

    def _start_updating_frame(self):
        self.frame_thread = threading.Thread(target=self._update_frame)
        self.frame_thread.daemon = True
        self.frame_thread.start()

    def _get_width_and_height(self):
        window_size = self._run_command(["shell", "wm", "size"])
        window_size = window_size.replace("Physical size: ", "")
        width, height = tuple(int(i) for i in window_size.split("x"))
        return width, height

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
        self._run_command(["shell", "input", "tap", str(x), str(y)])

    def take_screenshot(self):
        logger.debug("Starting to take screenshot...")
        while self.frame is None:
            time.sleep(0.01)
            continue

        screenshot, self.frame = self.frame, None

        return screenshot
