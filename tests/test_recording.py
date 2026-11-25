import shutil
import subprocess
import sys

import pytest

from clashroyalebuildabot.constants.screenshot import SCREENSHOT_WIDTH
from clashroyalebuildabot.emulator import (
    recording_script,
    recording_size,
)


@pytest.mark.parametrize(
    ("screen", "expected"),
    [
        ((720, 1280), (368, 656)),
        ((1080, 1920), (368, 656)),
        ((1080, 2400), (368, 816)),
    ],
)
def test_records_at_screenshot_width_keeping_the_shape(screen, expected):
    assert recording_size(*screen) == expected


def test_sizes_are_multiples_of_16():
    for width, height in [(720, 1280), (1080, 2340), (1440, 3200)]:
        w, h = recording_size(width, height)
        assert w % 16 == 0
        assert h % 16 == 0
        assert w == SCREENSHOT_WIDTH


def run_script(tmp_path, fake_screenrecord):
    """Run one pass of the recording loop with a fake screenrecord that
    logs its --size and then behaves as given."""
    log = tmp_path / "calls"
    script = recording_script(720, 1280).replace(
        "while true; do", "for _ in 1; do"
    )
    fake = (
        "screenrecord() {\n"
        '    while [ "$1" != "--size" ]; do shift; done\n'
        f'    echo "$2" >> {log}\n'
        f"    {fake_screenrecord}\n"
        "}\n"
        "sleep() { :; }\n"
    )
    subprocess.run(["sh", "-c", fake + script], check=True, timeout=10)
    return log.read_text().split()


needs_sh = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("sh") is None,
    reason="needs a POSIX shell",
)


@needs_sh
def test_records_small_when_the_device_can(tmp_path):
    assert run_script(tmp_path, "return 0") == ["368x656"]


@needs_sh
def test_falls_back_to_full_size(tmp_path):
    calls = run_script(tmp_path, '[ "$2" = "720x1280" ]')
    assert calls == ["368x656", "720x1280"]
