# pylint: disable=R1732

import atexit
from contextlib import contextmanager
import os
import platform
import socket
import subprocess
import time
import zipfile

import av
from get_free_port import get_dynamic_ports
import kthread
from loguru import logger
import requests
from subprocesskiller import kill_pid
from subprocesskiller import kill_process_children_parents
from subprocesskiller import kill_subprocs
import yaml

from clashroyalebuildabot.constants import ADB_DIR
from clashroyalebuildabot.constants import ADB_PATH
from clashroyalebuildabot.constants import EMULATOR_DIR
from clashroyalebuildabot.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.constants import SCREENSHOT_WIDTH
from clashroyalebuildabot.constants import SRC_DIR


@atexit.register
def kill_them_all():
    kill_subprocs()


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


class Emulator:
    def __init__(self):
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)

        adb_config = config["adb"]
        self.serial, self.ip = [adb_config[s] for s in ["device_serial", "ip"]]

        self.video_socket = None
        self.screenshot_thread = None
        self.frame = None
        self.scrcpy_proc = None
        self.codec = av.codec.CodecContext.create("h264", "r")
        self.forward_port = get_dynamic_ports(qty=1)[0]

        self._install_adb()
        self.width, self.height = self._get_width_and_height()
        self._copy_scrcpy()
        self._forward_port()
        self._start_scrcpy()
        self._connect_to_server()
        self._start_capturing()

    @staticmethod
    def _install_adb():
        if os.path.isdir(ADB_DIR):
            return

        os_name = platform.system().lower()
        adb_url = f"https://dl.google.com/android/repository/platform-tools-latest-{os_name}.zip"
        zip_path = f"platform-tools-latest-{os_name}.zip"

        response = requests.get(adb_url, stream=True, timeout=60)
        response.raise_for_status()

        with open(zip_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(EMULATOR_DIR)

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()

    def quit(self):
        while self.screenshot_thread.is_alive():
            with ignored(Exception):
                self.screenshot_thread.kill()
        self.video_socket.close()

        with ignored(Exception):
            self.scrcpy_proc.stdout.close()

        with ignored(Exception):
            self.scrcpy_proc.stdin.close()

        with ignored(Exception):
            self.scrcpy_proc.stderr.close()

        with ignored(Exception):
            self.scrcpy_proc.wait(timeout=2)

        with ignored(Exception):
            self.scrcpy_proc.kill()

        with ignored(Exception):
            kill_process_children_parents(
                pid=self.scrcpy_proc.pid, max_parent_exe="adb.exe", dontkill=()
            )
            time.sleep(2)

        with ignored(Exception):
            kill_pid(pid=self.scrcpy_proc.pid)

    def _run_command(self, command):
        command = [ADB_PATH, "-s", self.serial, *command]
        logger.debug(" ".join(command))
        try:
            result = subprocess.run(
                command,
                cwd=EMULATOR_DIR,
                capture_output=True,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command: {e}")
            logger.error(f"Output: {e.stdout}")
            logger.error(f"Error output: {e.stderr}")
            self.quit()
            raise

        if result.returncode != 0:
            logger.error(f"Error executing command: {result.stderr}")
            self.quit()
            raise RuntimeError("ADB command failed")

        return result.stdout

    def _copy_scrcpy(self):
        self._run_command(["push", "scrcpy-server.jar", "/data/local/tmp/"])

    def _start_scrcpy(self):
        command = [
            ADB_PATH,
            "-s",
            self.serial,
            "shell",
            "CLASSPATH=/data/local/tmp/scrcpy-server.jar",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            "2.0",
            "tunnel_forward=true",
            "control=false",
            "cleanup=true",
            "clipboard_autosync=false",
            "video_bit_rate=8000000",
            "audio=false",
            "lock_video_orientation=0",
            "downsize_on_error=false",
            "send_dummy_byte=true",
            "raw_video_stream=true",
            f"max_size={self.width}",
        ]
        self.scrcpy_proc = subprocess.Popen(
            command,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=EMULATOR_DIR,
        )

    def _forward_port(self):
        self._run_command(
            ["forward", f"tcp:{self.forward_port}", "localabstract:scrcpy"]
        )

    def _connect_to_server(self):
        dummy_byte = b""
        while not dummy_byte:
            with ignored(Exception):
                self.video_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM
                )
                self.video_socket.connect((self.ip, self.forward_port))

                self.video_socket.setblocking(False)
                self.video_socket.settimeout(1)
                dummy_byte = self.video_socket.recv(1)
                if len(dummy_byte) == 0:
                    self.video_socket.close()

    def _start_capturing(self):
        self.screenshot_thread = kthread.KThread(
            target=self._update_screenshot, name="update_screenshot_thread"
        )
        self.screenshot_thread.start()

    def _update_screenshot(self):
        while True:
            with ignored(Exception):
                packets = self.codec.parse(self.video_socket.recv(131072))
                if len(packets) == 0:
                    continue

                frames = self.codec.decode(packets[-1])
                if len(frames) == 0:
                    continue

                self.frame = frames[-1]

    def _get_width_and_height(self):
        window_size = self._run_command(["shell", "wm", "size"])
        window_size = window_size.replace("Physical size: ", "")
        width, height = tuple(int(i) for i in window_size.split("x"))
        return width, height

    def click(self, x, y):
        self._run_command(["shell", "input", "tap", str(x), str(y)])

    def take_screenshot(self):
        logger.debug("Starting to take screenshot...")
        while self.frame is None:
            time.sleep(0.001)
        frame, self.frame = self.frame, None
        screenshot = frame.reformat(
            width=SCREENSHOT_WIDTH, height=SCREENSHOT_HEIGHT, format="rgb24"
        ).to_image()

        return screenshot
