import pytest

from clashroyalebuildabot.emulator.emulator import parse_wm_size


def test_physical_size():
    assert parse_wm_size("Physical size: 720x1280\n") == (720, 1280)


def test_override_wins():
    output = "Physical size: 1080x2400\nOverride size: 720x1280\n"
    assert parse_wm_size(output) == (720, 1280)


def test_unreadable_output():
    with pytest.raises(ValueError):
        parse_wm_size("error: closed")
