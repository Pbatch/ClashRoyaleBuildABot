"""Taps go to the device as lines written to one long-lived shell."""

import subprocess
import sys
import time

import pytest

from clashroyalebuildabot.emulator import Emulator
from tests.test_emulator_lifecycle import emulator  # noqa: F401 (fixture)

# Stand-in for `adb shell -T`: writes each line it reads to a file, and
# exits at the end of its input, as the device's shell does.
_RECORDING_SHELL = (
    "import sys\n"
    "with open(sys.argv[1], 'a') as f:\n"
    "    for line in sys.stdin:\n"
    "        f.write(line)\n"
    "        f.flush()\n"
)


@pytest.fixture
def shells(emulator, monkeypatch, tmp_path):  # noqa: F811
    """Replaces the device shell with recording ones. Returns the list of
    shells started and a function that reads the lines they received."""
    log = tmp_path / "lines.txt"
    started: list[subprocess.Popen] = []

    def start(self):
        shell = subprocess.Popen(
            [sys.executable, "-c", _RECORDING_SHELL, str(log)],
            stdin=subprocess.PIPE,
        )
        started.append(shell)
        return shell

    monkeypatch.setattr(Emulator, "_start_input_shell", start)

    def lines(expected):
        # The taps are sent without waiting, so give the shell a moment.
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            got = log.read_text().splitlines() if log.exists() else []
            if len(got) >= expected:
                return got
            time.sleep(0.01)
        return got

    return started, lines


def test_a_card_play_is_one_line(emulator, shells):  # noqa: F811
    _, lines = shells
    emulator.tap_sequence([(10.4, 20.6), (30, 40)])
    assert lines(1) == ["input tap 10 21 && input tap 30 40"]


def test_the_shell_is_kept_between_taps(emulator, shells):  # noqa: F811
    started, lines = shells
    emulator.click(5, 6)
    emulator.click(7, 8)
    assert lines(2) == ["input tap 5 6", "input tap 7 8"]
    assert len(started) == 1


def test_a_dead_shell_is_replaced(emulator, shells):  # noqa: F811
    started, lines = shells
    emulator.click(5, 6)
    lines(1)
    started[0].kill()  # e.g. wireless adb dropped
    started[0].wait()

    emulator.click(7, 8)

    assert lines(2) == ["input tap 5 6", "input tap 7 8"]
    assert len(started) == 2


def test_falls_back_to_one_command_if_no_shell_runs(emulator, monkeypatch):  # noqa: F811
    def started_dead(self):
        # A shell that exits at once, e.g. adb can't reach the device.
        shell = subprocess.Popen(
            [sys.executable, "-c", ""], stdin=subprocess.PIPE
        )
        shell.wait()
        return shell

    commands = []
    monkeypatch.setattr(Emulator, "_start_input_shell", started_dead)
    monkeypatch.setattr(
        Emulator, "_run_command", lambda self, c: commands.append(c)
    )

    emulator.click(5, 6)

    assert commands == [["shell", "input tap 5 6"]]


def test_close_stops_the_shell(emulator, shells):  # noqa: F811
    started, lines = shells
    emulator.click(5, 6)
    lines(1)

    emulator.close()

    assert started[0].poll() is not None
    assert emulator.input_shell is None


def test_no_taps_after_close(emulator, shells):  # noqa: F811
    started, _ = shells
    emulator.close()
    emulator.click(5, 6)
    assert started == []
