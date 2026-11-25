import pytest

from clashroyalebuildabot.emulator import Emulator


@pytest.mark.parametrize(
    ("reachable", "expected"),
    [(True, []), (False, [["kill-server"], ["start-server"]])],
)
def test_server_only_restarts_when_device_unreachable(
    monkeypatch, reachable, expected
):
    emulator = Emulator.__new__(Emulator)
    commands = []
    monkeypatch.setattr(emulator, "_device_reachable", lambda: reachable)
    monkeypatch.setattr(emulator, "_run_command", commands.append)

    emulator._restart_server()

    assert commands == expected
