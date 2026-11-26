"""The emulator reading frames from the screen server (faked here; the
real client is in test_jpeg_screen.py), and closing cleanly."""

import threading

import numpy as np
import pytest

from clashroyalebuildabot.emulator import Emulator
from clashroyalebuildabot.jpeg_screen import (
    DISPLAY_OFF,
    NO_NEW_IMAGE,
    Frame,
    ScreenServerError,
)
from clashroyalebuildabot.utils.error_handling import WikifiedError


class FakeScreen:
    """Hands out Frames from a list; then raises, as a lost link would."""

    def __init__(self, frames):
        self.frames = list(frames)
        self.closed = False

    def frame(self):
        if self.closed:
            raise OSError("closed")
        if not self.frames:
            raise EOFError("server gone")
        return self.frames.pop(0)

    def close(self):
        self.closed = True


def picture(value):
    return Frame(np.full((8, 16, 3), value, np.uint8), 0.0, 100)


NO_NEW = Frame(None, 0.0, NO_NEW_IMAGE)
OFF = Frame(None, 0.0, DISPLAY_OFF)


@pytest.fixture
def make_emulator(monkeypatch):
    """Makes emulators on a fake device and screen server."""
    monkeypatch.setattr(Emulator, "_check_adb", lambda self: None)
    monkeypatch.setattr(Emulator, "_restart_server", lambda self: None)
    monkeypatch.setattr(
        Emulator, "_get_valid_device_serial", lambda self: self.device_serial
    )
    monkeypatch.setattr(Emulator, "_check_android_version", lambda self: None)
    monkeypatch.setattr(Emulator, "_set_display", lambda self: None)
    monkeypatch.setattr(Emulator, "JPEG_RETRY_DELAY", 0.001)
    monkeypatch.setattr(Emulator, "SCREEN_OFF_RETRY_DELAY", 0.001)
    emulators = []

    def make(frames=()):
        screen = FakeScreen(frames)
        monkeypatch.setattr(
            Emulator, "_start_jpeg_screen", lambda self: screen
        )
        emulator = Emulator(device_serial="test-device")
        emulators.append(emulator)
        return emulator, screen

    yield make
    for emulator in emulators:
        emulator.close()


@pytest.fixture
def emulator(make_emulator):
    emulator, _ = make_emulator([picture(1)])
    return emulator


def test_returns_the_servers_frames(make_emulator):
    emulator, _ = make_emulator([picture(1)])
    assert emulator.take_screenshot()[0, 0, 0] == 1


def test_an_unchanged_screen_returns_the_last_frame(make_emulator):
    emulator, _ = make_emulator([picture(1), NO_NEW])
    first = emulator.take_screenshot()
    assert emulator.take_screenshot() is first


def test_waits_for_the_first_picture(make_emulator):
    emulator, _ = make_emulator([NO_NEW, NO_NEW, picture(2)])
    assert emulator.take_screenshot()[0, 0, 0] == 2


def test_no_first_picture_raises_e008(make_emulator, monkeypatch):
    monkeypatch.setattr(Emulator, "FIRST_FRAME_TIMEOUT", 0.05)
    emulator, _ = make_emulator([NO_NEW] * 100_000)
    with pytest.raises(WikifiedError, match="E008"):
        emulator.take_screenshot()


def test_waits_while_the_screen_is_off(make_emulator, monkeypatch):
    monkeypatch.setattr(Emulator, "FRAME_TIMEOUT", 0.01)
    emulator, _ = make_emulator([picture(1), *[OFF] * 50, picture(3)])
    emulator.take_screenshot()
    # Off for longer than FRAME_TIMEOUT, and still no error.
    assert emulator.take_screenshot()[0, 0, 0] == 3


def test_a_lost_server_raises_e008(make_emulator):
    emulator, _ = make_emulator([picture(1)])
    emulator.take_screenshot()
    with pytest.raises(WikifiedError, match="E008"):
        emulator.take_screenshot()


def test_a_server_that_wont_start_raises_e008(make_emulator, monkeypatch):
    def no_server(self):
        raise ScreenServerError("it stopped")

    monkeypatch.setattr(Emulator, "_start_jpeg_screen", no_server)
    with pytest.raises(WikifiedError, match="E008"):
        Emulator(device_serial="test-device")


def test_close_stops_the_server_and_ends_screenshots(make_emulator):
    emulator, screen = make_emulator([picture(1)])
    emulator.close()
    assert screen.closed
    assert emulator.take_screenshot() is None


def test_close_is_idempotent(make_emulator):
    emulator, _ = make_emulator()
    emulator.close()
    emulator.close()


def test_close_unblocks_a_screenshot_waiting_for_the_screen(make_emulator):
    emulator, _ = make_emulator([OFF] * 1_000_000)
    result = []
    thread = threading.Thread(
        target=lambda: result.append(emulator.take_screenshot())
    )
    thread.start()
    emulator.close()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert result == [None]


@pytest.mark.parametrize(("sdk", "ok"), [("33", False), ("34", True)])
def test_needs_android_14(sdk, ok):
    emulator = Emulator.__new__(Emulator)
    props = {"ro.build.version.sdk": sdk, "ro.build.version.release": "13"}
    emulator._run_command = lambda command: props[command[-1]] + "\n"
    if ok:
        emulator._check_android_version()
    else:
        with pytest.raises(WikifiedError, match="E013"):
            emulator._check_android_version()
