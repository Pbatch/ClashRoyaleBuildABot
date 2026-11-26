"""The JPEG screen server's client, against a fake server. The emulator
using it is in test_emulator_lifecycle.py."""

import socket
import struct
import threading

import cv2
import numpy as np
import pytest

from clashroyalebuildabot.jpeg_screen import (
    DISPLAY_OFF,
    NO_NEW_IMAGE,
    JpegScreenClient,
    ScreenServerError,
)

RED = np.zeros((8, 16, 3), np.uint8)
RED[..., 0] = 255  # RGB


def jpeg(rgb: np.ndarray) -> bytes:
    ok, data = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    assert ok
    return data.tobytes()


class FakeServer:
    """Speaks the server's protocol on a socket pair: sends the header, then
    answers each request from a list of replies."""

    def __init__(self, replies, magic=b"JPGS", version=1, display=(720, 1280)):
        self.ours, theirs = socket.socketpair()
        self.client_sock = theirs
        self.replies = list(replies)
        self.ours.sendall(
            struct.pack(">4siiiii", magic, version, 16, 8, *display)
        )
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while True:
            request = self.ours.recv(1)
            if not request:
                return
            if request == b"p":
                self.ours.sendall(struct.pack(">q", 123_000_000_000))
            elif request == b"f" and self.replies:
                captured, body = self.replies.pop(0)
                status = len(body) if isinstance(body, bytes) else body
                self.ours.sendall(struct.pack(">qqi", captured, 0, status))
                if isinstance(body, bytes):
                    self.ours.sendall(body)
            else:
                self.ours.shutdown(socket.SHUT_RDWR)  # e.g. it went away
                return

    def close(self):
        self.ours.close()
        self.client_sock.close()


@pytest.fixture
def serve():
    """Makes fake servers, and closes their sockets after the test."""
    servers = []

    def make(replies=(), **kwargs):
        server = FakeServer(replies, **kwargs)
        servers.append(server)
        return server.client_sock

    yield make
    for server in servers:
        server.close()


# TCP_NODELAY doesn't apply to a Unix socket pair.
@pytest.fixture(autouse=True)
def _no_nodelay(monkeypatch):
    real = socket.socket.setsockopt

    def setsockopt(self, level, option, value):
        if self.family == socket.AF_UNIX and level == socket.IPPROTO_TCP:
            return None
        return real(self, level, option, value)

    monkeypatch.setattr(socket.socket, "setsockopt", setsockopt)


def test_reads_the_header(serve):
    client = JpegScreenClient(serve([], display=(720, 1280)))
    assert client.size == (16, 8)
    assert client.display_size == (720, 1280)


def test_refuses_another_server(serve):
    with pytest.raises(ScreenServerError):
        JpegScreenClient(serve([], magic=b"NOPE"))
    with pytest.raises(ScreenServerError):
        JpegScreenClient(serve([], version=2))


def test_ping_returns_the_device_clock(serve):
    assert JpegScreenClient(serve([])).ping() == 123_000_000_000


def test_frames_decode_to_rgb(serve):
    frame = JpegScreenClient(serve([(2_500_000_000, jpeg(RED))])).frame()
    assert frame.status > 0
    assert frame.captured == 2.5
    assert frame.image is not None
    assert frame.image.shape == (8, 16, 3)
    # Red stays in the first channel: RGB, as the detectors expect.
    assert frame.image[..., 0].mean() > 200
    assert frame.image[..., 2].mean() < 50


def test_no_new_image_and_display_off_carry_no_picture(serve):
    client = JpegScreenClient(serve([(1, NO_NEW_IMAGE), (1, DISPLAY_OFF)]))
    assert client.frame().image is None
    assert client.frame().status == DISPLAY_OFF


def test_a_closed_server_raises(serve):
    client = JpegScreenClient(serve([]))
    with pytest.raises(EOFError):
        client.frame()
