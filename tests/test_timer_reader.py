import math
import os

import numpy as np
import pytest

from clashroyalebuildabot.constants.screenshot import TIMER_BOX
from clashroyalebuildabot.detectors.timer_reader import TimerReader, parse
from clashroyalebuildabot.game.timer import UNKNOWN_TIME, Timer
from clashroyalebuildabot.utils.image import load

DATA = os.path.join(os.path.dirname(__file__), "data", "numbers")


def frame(timer: str | None = None) -> np.ndarray:
    """A black frame, with a real timer crop pasted where the timer is."""
    image = np.zeros((652, 368, 3), np.uint8)
    if timer:
        left, top, right, bottom = TIMER_BOX
        crop = load(os.path.join(DATA, f"{timer}.png"))
        image[top:bottom, left:right] = crop
    return image


@pytest.mark.parametrize(
    ("timer", "expected"),
    [
        ("timer_2_29", Timer(time_left=149, overtime=False)),
        ("timer_1_01", Timer(time_left=61, overtime=False)),
        ("timer_overtime_1_59", Timer(time_left=119, overtime=True)),
    ],
)
def test_reads_the_timer(timer, expected):
    assert TimerReader().run(frame(timer)) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2:29", Timer(time_left=149, overtime=False)),
        ("+1:59", Timer(time_left=119, overtime=True)),
        ("0:00", Timer(time_left=0, overtime=False)),
        # Not a time: too many digits, seconds past 59, a stray "+".
        ("12:29", None),
        ("2:61", None),
        ("2:2+9", None),
        ("", None),
        (None, None),
    ],
)
def test_parse(text, expected):
    assert parse(text) == expected


def test_unknown_until_first_reading():
    reader = TimerReader()
    assert reader.latest().time_left == UNKNOWN_TIME
    assert reader.latest().overtime is False


def test_unreadable_frame_keeps_the_previous_reading():
    reader = TimerReader()
    reader.run(frame("timer_2_29"))
    assert reader.run(frame()).time_left == 149


def test_unreadable_first_frame_stays_unknown():
    assert math.isinf(TimerReader().run(frame()).time_left)


def test_reset_forgets_the_reading():
    reader = TimerReader()
    reader.run(frame("timer_2_29"))
    reader.reset()
    assert reader.latest().time_left == UNKNOWN_TIME
