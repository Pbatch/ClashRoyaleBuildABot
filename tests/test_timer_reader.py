import math
import os

import numpy as np
import pytest

from clashroyalebuildabot.constants.screenshot import TIMER_BOX
from clashroyalebuildabot.detectors.timer_reader import TimerReader
from clashroyalebuildabot.game.numbers import UNKNOWN_TIME, Timer
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


def read_in_background(reader, image):
    reader.run(image)
    reader.wait(5)
    return reader.latest()


@pytest.mark.parametrize(
    ("timer", "expected"),
    [
        ("timer_2_29", Timer(time_left=149, overtime=False)),
        # Zeros, which a wider font's 0 would read as two 1s.
        ("timer_1_01", Timer(time_left=61, overtime=False)),
        ("timer_overtime_1_59", Timer(time_left=119, overtime=True)),
    ],
)
def test_reads_the_timer(timer, expected):
    reader = TimerReader()
    assert reader.read(frame(timer), Timer()) == expected
    reader.close()


def test_unknown_until_first_reading():
    reader = TimerReader()
    assert reader.latest().time_left == UNKNOWN_TIME
    assert reader.latest().overtime is False
    reader.close()


def test_unreadable_frame_keeps_the_previous_reading():
    reader = TimerReader(interval=0)
    read_in_background(reader, frame("timer_2_29"))
    assert read_in_background(reader, frame()).time_left == 149
    reader.close()


def test_unreadable_first_frame_stays_unknown():
    reader = TimerReader()
    assert math.isinf(reader.read(frame(), Timer()).time_left)
    reader.close()


def test_reset_forgets_the_reading():
    reader = TimerReader(interval=0)
    read_in_background(reader, frame("timer_2_29"))
    reader.reset()
    assert reader.latest().time_left == UNKNOWN_TIME
    reader.close()
