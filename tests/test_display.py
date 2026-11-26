"""The emulator sets the device's screen to the size and density the bot
reads it at, and puts back what was there when it closes."""

import pytest

from clashroyalebuildabot.emulator import Emulator, parse_wm_setting
from clashroyalebuildabot.utils.error_handling import WikifiedError


class FakeWm:
    """`adb shell wm size|density [value|reset]` on a fake device."""

    def __init__(self, size=None, density=None, fail_on_set=False):
        self.physical = {"size": "1080x2400", "density": "420"}
        self.override = {"size": size, "density": density}
        self.sets: list[tuple[str, str]] = []
        self.fail_on_set = fail_on_set

    def __call__(self, command):
        assert command[:2] == ["shell", "wm"]
        setting, *value = command[2:]
        if not value:
            out = f"Physical {setting}: {self.physical[setting]}\n"
            if self.override[setting]:
                out += f"Override {setting}: {self.override[setting]}\n"
            return out
        if self.fail_on_set:
            raise WikifiedError("007", "ADB command failed.")
        self.sets.append((setting, value[0]))
        self.override[setting] = None if value[0] == "reset" else value[0]
        return ""


def make(wm):
    emulator = Emulator.__new__(Emulator)
    emulator._display_restore = []
    emulator._run_command = wm
    return emulator


def test_parse_wm_setting():
    assert parse_wm_setting("Physical size: 1080x2400\n", "size") == (
        None,
        "1080x2400",
    )
    output = "Physical density: 420\nOverride density: 240\n"
    assert parse_wm_setting(output, "density") == ("240", "420")
    with pytest.raises(ValueError, match="density"):
        parse_wm_setting("error: closed", "density")


def test_sets_the_bots_screen_and_resets_it_after():
    wm = FakeWm()
    emulator = make(wm)

    emulator._set_display()
    assert wm.override == {"size": "720x1280", "density": "240"}

    emulator._restore_display()
    assert wm.override == {"size": None, "density": None}
    assert wm.sets[2:] == [("density", "reset"), ("size", "reset")]


def test_puts_back_the_users_own_overrides():
    wm = FakeWm(size="1080x1920", density="320")
    emulator = make(wm)
    emulator._set_display()
    emulator._restore_display()
    assert wm.override == {"size": "1080x1920", "density": "320"}


def test_leaves_a_screen_thats_already_right_alone():
    # Changing them makes the game reload, so it's only done when needed.
    wm = FakeWm(size="720x1280", density="240")
    emulator = make(wm)
    emulator._set_display()
    emulator._restore_display()
    assert wm.sets == []


def test_only_changes_what_differs():
    wm = FakeWm(size="720x1280")
    emulator = make(wm)
    emulator._set_display()
    emulator._restore_display()
    assert wm.sets == [("density", "240"), ("density", "reset")]


def test_restoring_twice_does_nothing_the_second_time():
    wm = FakeWm()
    emulator = make(wm)
    emulator._set_display()
    emulator._restore_display()
    emulator._restore_display()
    assert len(wm.sets) == 4


def test_a_failed_restore_doesnt_raise():
    wm = FakeWm()
    emulator = make(wm)
    emulator._set_display()
    wm.fail_on_set = True  # e.g. the device has gone
    emulator._restore_display()


def test_a_failed_start_puts_the_display_back(monkeypatch):
    wm = FakeWm()
    monkeypatch.setattr(Emulator, "_check_adb", lambda self: None)
    monkeypatch.setattr(Emulator, "_restart_server", lambda self: None)
    monkeypatch.setattr(
        Emulator, "_get_valid_device_serial", lambda self: self.device_serial
    )
    monkeypatch.setattr(Emulator, "_run_command", lambda self, c: wm(c))
    monkeypatch.setattr(Emulator, "_check_android_version", lambda self: None)

    def broken(self):
        raise RuntimeError("no screen")

    monkeypatch.setattr(Emulator, "_start_screen", broken)
    with pytest.raises(RuntimeError):
        Emulator(device_serial="test-device")
    assert wm.override == {"size": None, "density": None}
