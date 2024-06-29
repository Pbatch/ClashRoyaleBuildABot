# pylint: disable=R1732

import atexit
from contextlib import contextmanager
import socket
import subprocess
import time

import av
from get_free_port import get_dynamic_ports
import kthread
from subprocesskiller import kill_pid
from subprocesskiller import kill_process_children_parents
from subprocesskiller import kill_subprocs

from clashroyalebuildabot.constants import EMULATOR_DIR


@atexit.register
def kill_them_all():
    kill_subprocs(dontkill=())


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


class AdbShotTCP:
    def __init__(
        self,
        device_serial,
        adb_path,
        max_video_width,
        ip="127.0.0.1",
        port=5555,
    ):
        r"""Class for capturing screenshots from an Android device over TCP/IP using ADB.

        Args:
            device_serial (str): Serial number or IP address of the target device.
            adb_path (str): Path to the ADB executable.
            ip (str, optional): IP address of the device. Defaults to "127.0.0.1".
            port (int, optional): Port number to connect to the device. Defaults to 5555.

        Raises:
            Exception: If connection to the device fails.

        Methods:
            quit(): Stops capturing and closes the connection to the device.
            take_screenshot(): Retrieves a screenshot from the device.
            __exit__(exc_type, exc_value, traceback): Context manager exit point.
        """
        self.device_serial = device_serial
        self.adb_path = adb_path
        self.max_video_width = max_video_width
        self.ip = ip
        self.port = port

        self.video_socket = None
        self.screenshot_thread = None
        self.screenshot = None
        self.scrcpy_proc = None
        self.codec = av.codec.CodecContext.create("h264", "r")
        self.forward_port = get_dynamic_ports(qty=1)[0]

        self._copy_scrcpy()
        self._forward_port()
        self._start_scrcpy()
        self._connect_to_server()
        self._start_capturing()

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()

    def _copy_scrcpy(self):
        subprocess.run(
            [
                self.adb_path,
                "-s",
                self.device_serial,
                "push",
                "scrcpy-server.jar",
                "/data/local/tmp/",
            ],
            check=True,
            capture_output=True,
            cwd=EMULATOR_DIR,
        )

    def _start_scrcpy(self):
        command = [
            self.adb_path,
            "-s",
            self.device_serial,
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
            f"max_size={self.max_video_width}",
        ]
        self.scrcpy_proc = subprocess.Popen(
            command,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=EMULATOR_DIR,
        )

    def _forward_port(self):
        subprocess.run(
            [
                self.adb_path,
                "-s",
                self.device_serial,
                "forward",
                f"tcp:{self.forward_port}",
                "localabstract:scrcpy",
            ],
            cwd=EMULATOR_DIR,
            capture_output=True,
            check=True,
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

                frame = frames[-1]
                self.screenshot = (
                    frame.to_rgb()
                    .reformat(
                        width=frame.width, height=frame.height, format="rgb24"
                    )
                    .to_ndarray()
                )

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

    def take_screenshot(self):
        while self.screenshot is None:
            time.sleep(0.01)
        screenshot = self.screenshot
        self.screenshot = None

        return screenshot
