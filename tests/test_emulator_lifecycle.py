import subprocess
import sys
import threading

import pytest

from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.utils.error_handling import WikifiedError

# Stand-in for `adb shell screenrecord`: a process that never ends on its own.
_ENDLESS_STREAM = "import time\nwhile True:\n    time.sleep(1)"


@pytest.fixture
def emulator(monkeypatch):
    def fake_start_recording(self):
        self.video_process = subprocess.Popen(
            [sys.executable, "-c", _ENDLESS_STREAM],
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )

    monkeypatch.setattr(Emulator, "_install_adb", lambda self: None)
    monkeypatch.setattr(Emulator, "_restart_server", lambda self: None)
    monkeypatch.setattr(
        Emulator, "_get_valid_device_serial", lambda self: self.device_serial
    )
    monkeypatch.setattr(
        Emulator, "_get_width_and_height", lambda self: (720, 1280)
    )
    monkeypatch.setattr(Emulator, "_start_recording", fake_start_recording)

    emu = Emulator(device_serial="test-device")
    yield emu
    emu.close()


def test_close_stops_recording_and_frame_thread(emulator):
    assert emulator.video_process.poll() is None
    assert emulator.frame_thread.is_alive()

    emulator.close()

    assert emulator.video_process.poll() is not None
    assert not emulator.frame_thread.is_alive()


def test_close_is_idempotent(emulator):
    emulator.close()
    emulator.close()


def test_take_screenshot_returns_none_after_close(emulator):
    emulator.close()
    assert emulator.take_screenshot() is None


def test_close_unblocks_a_waiting_take_screenshot(emulator):
    result = []
    waiter = threading.Thread(
        target=lambda: result.append(emulator.take_screenshot())
    )
    waiter.start()

    emulator.close()
    waiter.join(timeout=2)

    assert not waiter.is_alive()
    assert result == [None]


def test_stream_death_raises(emulator):
    emulator.video_process.kill()  # e.g. adb or the device went away
    emulator.frame_thread.join(timeout=2)

    with pytest.raises(WikifiedError, match="E008"):
        emulator.take_screenshot()


def test_no_first_frame_raises(emulator):
    emulator.FIRST_FRAME_TIMEOUT = 0.1

    with pytest.raises(WikifiedError, match="E008"):
        emulator.take_screenshot()


def test_static_screen_reuses_last_frame(emulator):
    emulator.FRAME_TIMEOUT = 0.1
    last_frame = object()
    emulator._last_frame = last_frame  # a frame arrived, then none since

    assert emulator.take_screenshot() is last_frame
