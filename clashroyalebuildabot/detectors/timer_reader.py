"""Read the battle timer.

The top-right corner of a battle shows "Time left:" above the minutes and
seconds, or "Overtime:" once regulation time runs out with the towers level.
The digits and the label are matched against the game's own font (see
digit_reader).

It's read in the background, at most once per ``interval`` seconds, so a
reading is about a second old. Until the first reading of a battle, the time
left is ``UNKNOWN_TIME``.
"""

import numpy as np

from clashroyalebuildabot.constants.screenshot import TIMER_BOX
from clashroyalebuildabot.detectors.background import BackgroundReader
from clashroyalebuildabot.detectors.digit_reader import read_timer
from clashroyalebuildabot.game.numbers import Timer
from clashroyalebuildabot.utils.image import crop


class TimerReader(BackgroundReader[Timer, Timer]):
    def __init__(self, interval: float = 1.0) -> None:
        super().__init__(Timer(), interval, name="timer-reader")

    def read(self, image: np.ndarray, previous: Timer) -> Timer:
        """If the timer can't be read (covered, or not a battle), the
        previous reading stands."""
        reading = read_timer(crop(image, TIMER_BOX))
        if reading is None:
            return previous
        time_left, overtime = reading
        return Timer(time_left=time_left, overtime=overtime)

    def output(self, state: Timer) -> Timer:
        return state
