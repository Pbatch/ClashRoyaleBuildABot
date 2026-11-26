"""Frames from the device as JPEG images, one per request.

The bot runs a small server on the device (jpeg_server/, shipped built as
data/jpeg-server.jar). It mirrors the screen at exactly the bot's
screenshot size and, each time it's asked, JPEG-encodes the newest image.
So a frame is only as old as it takes to encode and send it (about 50 ms
over Wi-Fi), the device only encodes the frames the bot uses, and there's
no video to decode. See jpeg_server/src/JpegServer.java for the protocol.
"""

import contextlib
import socket
import struct
import subprocess
import threading
import time
from dataclasses import dataclass

import cv2
import numpy as np
from loguru import logger

from clashroyalebuildabot.constants.paths import ADB_PATH, JPEG_SERVER_PATH
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)

REMOTE_PATH = "/data/local/tmp/crbab-jpeg-server.jar"
SOCKET_NAME = "jpeg_server"
VERSION = 1
QUALITY = 80
# How long the server may take to start listening.
START_TIMEOUT = 10
# A reply should take well under a second; this only catches a dead link.
REPLY_TIMEOUT = 5

HEADER = struct.Struct(">4siiiii")
FRAME = struct.Struct(">qqi")
NO_NEW_IMAGE = 0
DISPLAY_OFF = -1


class ScreenServerError(Exception):
    """The server couldn't be started or reached."""


@dataclass(frozen=True)
class Frame:
    # (height, width, 3) RGB, or None when status isn't a JPEG length.
    image: np.ndarray | None
    # When the device captured it, on its own monotonic clock, in seconds.
    captured: float
    # The JPEG's length, or NO_NEW_IMAGE or DISPLAY_OFF.
    status: int


class JpegScreenClient:
    """Asks a running server for frames over a socket. Separate from
    starting the server, so it can be tested against a fake one."""

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(REPLY_TIMEOUT)
        magic, version, width, height, display_w, display_h = HEADER.unpack(
            self._read(HEADER.size)
        )
        if magic != b"JPGS" or version != VERSION:
            raise ScreenServerError(
                f"Unexpected screen server: {magic!r}, version {version}"
            )
        self.size = (width, height)
        self.display_size = (display_w, display_h)

    def _read(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise EOFError("The screen server closed the connection.")
            buf += chunk
        return bytes(buf)

    def ping(self) -> int:
        """The device's monotonic clock, in nanoseconds."""
        self.sock.sendall(b"p")
        return struct.unpack(">q", self._read(8))[0]

    def frame(self) -> Frame:
        self.sock.sendall(b"f")
        captured_ns, _sent_ns, status = FRAME.unpack(self._read(FRAME.size))
        image = None
        if status > 0:
            data = np.frombuffer(self._read(status), np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR_RGB)
            if image is None:
                raise ScreenServerError("The screen server sent a bad JPEG.")
        return Frame(image, captured_ns / 1e9, status)

    def close(self) -> None:
        # shutdown() wakes a recv() blocked on another thread; close()
        # alone may not.
        with contextlib.suppress(OSError):  # already closed
            self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


class JpegScreen:
    """Starts the server on a device and connects to it."""

    def __init__(self, device_serial: str) -> None:
        self.device_serial = device_serial
        self.process: subprocess.Popen | None = None
        self.port: int | None = None
        self.client: JpegScreenClient | None = None
        try:
            self._start()
        except BaseException:
            self.close()
            raise

    def _adb(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [ADB_PATH, "-s", self.device_serial, *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def _start(self) -> None:
        # A server left by a bot that didn't shut down cleanly still holds
        # the socket name.
        self._adb("shell", "pkill -f JpegServer")
        pushed = self._adb("push", JPEG_SERVER_PATH, REMOTE_PATH)
        if pushed.returncode:
            raise ScreenServerError(
                f"Couldn't copy the screen server to the device: "
                f"{pushed.stderr.strip()}"
            )
        forward = self._adb("forward", "tcp:0", f"localabstract:{SOCKET_NAME}")
        if forward.returncode:
            raise ScreenServerError(
                f"Couldn't forward a port: {forward.stderr.strip()}"
            )
        self.port = int(forward.stdout.strip())
        command = (
            f"CLASSPATH={REMOTE_PATH} app_process / JpegServer "
            f"{SCREENSHOT_WIDTH} {SCREENSHOT_HEIGHT} {QUALITY}"
        )
        self.process = subprocess.Popen(
            [ADB_PATH, "-s", self.device_serial, "shell", command],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # Read its output as it comes, so a full pipe can't stall it.
        threading.Thread(
            target=self._log_output, args=(self.process,), daemon=True
        ).start()
        self.client = self._connect()
        logger.info(
            f"Reading the screen with the JPEG server, "
            f"{SCREENSHOT_WIDTH}x{SCREENSHOT_HEIGHT} frames of a "
            f"{self.client.display_size[0]}x{self.client.display_size[1]} "
            "display."
        )

    @staticmethod
    def _log_output(process: subprocess.Popen) -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            logger.debug(f"Screen server: {line.rstrip()}")

    def _connect(self) -> JpegScreenClient:
        """adb accepts a connection to the forwarded port even before the
        server listens, then drops it, so a connection only counts once the
        server's header arrives."""
        deadline = time.monotonic() + START_TIMEOUT
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                raise ScreenServerError(
                    "The screen server stopped as it started (its output is "
                    "in the debug log)."
                )
            try:
                sock = socket.create_connection(
                    ("127.0.0.1", self.port), timeout=REPLY_TIMEOUT
                )
            except OSError as e:
                last_error = e
                time.sleep(0.1)
                continue
            try:
                return JpegScreenClient(sock)
            except (EOFError, OSError) as e:
                sock.close()
                last_error = e
                time.sleep(0.1)
        raise ScreenServerError(
            f"The screen server didn't start within {START_TIMEOUT} "
            f"seconds: {last_error}"
        )

    def frame(self) -> Frame:
        assert self.client is not None
        return self.client.frame()

    def close(self) -> None:
        """Disconnect and stop the server. Safe to call twice, and from
        another thread while frame() waits."""
        if self.client is not None:
            self.client.close()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.port is not None:
            self._adb("forward", "--remove", f"tcp:{self.port}")
            self.port = None
        # Terminating adb doesn't always stop the server on the device.
        self._adb("shell", "pkill -f JpegServer")
