import atexit
import os
import socket
import subprocess
from collections import deque

import av
import kthread
import numpy as np
from get_free_port import get_dynamic_ports
from kthread_sleep import sleep
from loguru import logger
from subprocesskiller import kill_process_children_parents, kill_pid, kill_subprocs

startupinfo = subprocess.STARTUPINFO()
creationflags = 0 | subprocess.CREATE_NO_WINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE
invisibledict = {
    "startupinfo": startupinfo,
    "creationflags": creationflags,
    "start_new_session": True,
}


@atexit.register
def kill_them_all():
    kill_subprocs(dontkill=())


def mainprocess(cmd):
    if isinstance(cmd, str):
        cmd = [cmd]
    exefile = cmd[0]
    exefile = exefile.strip().strip('"').strip()
    exefile = os.path.normpath(exefile)
    exefile = f'"{exefile}"'
    try:
        arguments = cmd[1:]
    except Exception:
        arguments = []

    args_command = " ".join(arguments).strip()
    wholecommand = f'start /min "" {exefile} {args_command}'
    p = subprocess.Popen(wholecommand, shell=True, **invisibledict)
    return p


class AdbShotTCP:
    def __init__(
        self,
        device_serial,
        adb_path,
        max_video_width,
        ip="127.0.0.1",
        port=5555,
        scrcpy_server_version="2.0",
        forward_port=None,
        frame_buffer=4,
        byte_package_size=131072,
        sleep_after_exception=0.005,
        log_level="info",
        lock_video_orientation=0,
    ):
        r"""Class for capturing screenshots from an Android device over TCP/IP using ADB.

        Args:
            device_serial (str): Serial number or IP address of the target device.
            adb_path (str): Path to the ADB executable.
            ip (str, optional): IP address of the device. Defaults to "127.0.0.1".
            port (int, optional): Port number to connect to the device. Defaults to 5555.
            scrcpy_server_version (str, optional): Version of the scrcpy server to use. Defaults to "2.0".
            forward_port (int, optional): Port number to forward to the scrcpy server. Defaults to None.
            frame_buffer (int, optional): Number of frames to keep in the buffer. Defaults to 4.
            byte_package_size (int, optional): Size of each byte package to receive from the server. Defaults to 131072.
            sleep_after_exception (float, optional): Sleep time after encountering an exception. Defaults to 0.005.
            log_level (str, optional): Log level for the scrcpy server. Defaults to "info".
            lock_video_orientation (int, optional): Orientation of the video to lock. Defaults to 0 (unlocked).

        Raises:
            Exception: If connection to the device fails.

        Methods:
            quit(): Stops capturing and closes the connection to the device.
            get_one_screenshot(copy_ndarray=False): Retrieves a single screenshot from the device.
            __enter__(): Context manager entry point.
            __exit__(exc_type, exc_value, traceback): Context manager exit point.
            __iter__(): Returns the iterator object.
            __next__(): Returns the next frame in the iteration.
        """
        self.device_serial = device_serial
        self.adb_path = adb_path
        self.max_video_width = max_video_width
        self.ip = ip
        self.port = port

        if "/" in self.adb_path or "\\" in self.adb_path:
            self.adb_path = os.path.normpath(adb_path)

        if not forward_port:
            forward_port = get_dynamic_ports(qty=1)[0]

        self.video_bitrate = 8000000  # ignored
        self.loop_finished = True
        self.getting_screenshot = False
        self.sleep_after_exception = sleep_after_exception
        self.stop_capturing = False
        self.pause_capturing = False
        self.byte_size = byte_package_size

        self.scrcpy_server_version = scrcpy_server_version
        self.forward_port = forward_port
        self.folder_here = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
        self.scrcpy_path = os.path.normpath(
            os.path.join(self.folder_here, "scrcpy-server.jar")
        )
        self.all_raw_data264 = []
        self.log_level = log_level
        self.lock_video_orientation = lock_video_orientation
        self.real_width, self.real_height = 0, 0

        self.cmdservercommand = [
            self.adb_path,
            "-s",
            self.device_serial,
            "shell",
            "CLASSPATH=/data/local/tmp/scrcpy-server.jar",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            self.scrcpy_server_version,
            "tunnel_forward=true",
            "control=false",
            "cleanup=true",
            "clipboard_autosync=false",
            f"video_bit_rate={self.video_bitrate}",
            "audio=false",
            f"log_level={self.log_level}",
            f"lock_video_orientation={self.lock_video_orientation}",
            "downsize_on_error=false",
            "send_dummy_byte=true",
            "raw_video_stream=true",
            f"max_size={self.max_video_width}"
        ]
        self.video_socket = None
        self.t = None
        self.t2 = None
        self.t3 = None
        self.lastframes = deque([], frame_buffer)
        self.codec = av.codec.CodecContext.create("h264", "r")

        self._copy_scrcpy()
        self._forward_port()

        self.scrcpy_proc = None
        self._start_scrcpy()
        self._connect_to_server()
        self._start_capturing()

    def __enter__(self):
        self.stop_capturing = False
        self.pause_capturing = False
        while self.real_width == 0 or self.real_height == 0:
            _x = self.get_one_screenshot(copy_ndarray=False)
            try:
                self.real_height, self.real_width, *_ = _x.shape
            except Exception:
                continue
        self.stop_capturing = False
        self.pause_capturing = False
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit()

    def __iter__(self):
        self.pause_capturing = False
        self.stop_capturing = False
        return self

    def __next__(self):
        return self._iter_frames()

    def quit(self):
        self.stop_capturing = True
        while self.t.is_alive() or self.t2.is_alive():
            try:
                if self.t.is_alive:
                    self.t.kill()
            except Exception:
                pass
            try:
                if self.t2.is_alive:
                    self.t2.kill()
            except Exception:
                pass
        self.video_socket.close()

        try:
            self.scrcpy_proc.stdout.close()
        except Exception:
            pass
        try:
            self.scrcpy_proc.stdin.close()
        except Exception:
            pass
        try:
            self.scrcpy_proc.stderr.close()
        except Exception:
            pass
        try:
            self.scrcpy_proc.wait(timeout=2)
        except Exception:
            pass
        try:
            self.scrcpy_proc.kill()
        except Exception:
            pass

        try:
            kill_process_children_parents(
                pid=self.scrcpy_proc.pid, max_parent_exe="adb.exe", dontkill=()
            )
            sleep(2)
        except Exception:
            pass

        try:
            kill_pid(pid=self.scrcpy_proc.pid)
        except Exception:
            pass

    def _copy_scrcpy(self):
        subprocess.run(
            [
                self.adb_path,
                "-s",
                self.device_serial,
                "push",
                self.scrcpy_path,
                "/data/local/tmp/",
            ],
            check=True,
            capture_output=True,
            cwd=self.folder_here,
            **invisibledict,
        )

    def _start_scrcpy(self):
        self.scrcpy_proc = subprocess.Popen(
            self.cmdservercommand,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            cwd=self.folder_here,
            **invisibledict,
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
            cwd=self.folder_here,
            capture_output=True,
            check=True,
            **invisibledict,
        )

    def _connect_to_server(self):
        dummy_byte = b""
        cont = 0
        while not dummy_byte:
            try:
                cont += 1
                if self.stop_capturing:
                    break
                self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.video_socket.connect((self.ip, self.forward_port))

                self.video_socket.setblocking(False)
                self.video_socket.settimeout(1)
                dummy_byte = self.video_socket.recv(1)
                if len(dummy_byte) == 0:
                    try:
                        self.video_socket.close()
                    except Exception:
                        continue
            except Exception as fe:
                logger.info(fe)

    def _start_capturing(self):
        self.t = kthread.KThread(target=self._all_raw_data, name="all_raw_data_thread")
        self.t.start()

        self.t2 = kthread.KThread(target=self._parse_frames, name="parse_frames_thread")
        self.t2.start()

    def _get_infos2(self):
        while True:
            try:
                self.real_height, self.real_width, *_ = self.lastframes[-1].shape
                logger.info(self.real_width, self.real_height)
                break
            except Exception:
                sleep(0.1)
                continue

    def get_one_screenshot(self, copy_ndarray=False):
        onescreenshot = []
        try:
            thelastframe = self.lastframes[-1]
        except Exception:
            thelastframe = np.array([], dtype=np.uint16)
        self.lastframes.clear()
        self.getting_screenshot = True
        self.pause_capturing = False
        self.loop_finished = False
        while len(onescreenshot) == 0:
            while not self.loop_finished:
                sleep(0.001)
                continue
            try:
                if not copy_ndarray:
                    onescreenshot = self.lastframes[-1]
                else:
                    onescreenshot = self.lastframes[-1].copy()

            except Exception:
                if len(thelastframe) > 0:
                    self.lastframes.append(thelastframe)
                    onescreenshot = thelastframe
                    break
                continue
        self.getting_screenshot = False

        self.pause_capturing = True
        return onescreenshot

    def _iter_frames(self):
        try:
            return self.lastframes[-1].copy()
        except Exception:
            return np.array([], dtype=np.uint16)

    def _all_raw_data(self):
        self.pause_capturing = True
        self.stop_capturing = False
        while not self.stop_capturing:
            if not self.pause_capturing:
                try:
                    ra = self.video_socket.recv(self.byte_size)
                    self.all_raw_data264.append(ra)
                except Exception:
                    sleep(self.sleep_after_exception)
                    continue
            else:
                try:
                    ra = self.video_socket.recv(self.byte_size)
                    self.all_raw_data264.append(ra)
                    sleep(0.01)
                    continue
                except Exception:
                    sleep(0.1)
                    continue

    def _parse_frames(self):
        self.pause_capturing = True
        self.stop_capturing = False
        while not self.stop_capturing:
            if self.pause_capturing:
                sleep(0.01)
                continue
            packets = None
            try:
                thistime = len(self.all_raw_data264)
                joinedall = b"".join(self.all_raw_data264[:thistime])
                packets = self.codec.parse(joinedall)
                _ = [self.all_raw_data264.pop(0) for _ in range(thistime)]
            except Exception:
                sleep(self.sleep_after_exception)
            try:
                packlen = len(packets)
                for ini, pack in enumerate(packets):
                    try:
                        frames = self.codec.decode(pack)
                        if self.getting_screenshot:
                            if packlen - ini > 3:
                                continue
                        for frame in frames:
                            new_frame = frame.to_rgb().reformat(
                                width=frame.width, height=frame.height, format="bgr24"
                            )
                            self.lastframes.append(new_frame.to_ndarray())
                    except Exception as fa:
                        logger.info(fa)
                        continue
                self.loop_finished = True
            except Exception as fe:
                logger.info(fe, end="\r")
                sleep(self.sleep_after_exception)
