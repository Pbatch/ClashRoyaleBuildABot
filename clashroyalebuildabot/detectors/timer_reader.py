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
from clashroyalebuildabot.detectors.background import LatestResult
from clashroyalebuildabot.detectors.digit_reader import read_timer
from clashroyalebuildabot.game.numbers import Timer
from clashroyalebuildabot.utils.image import crop


class TimerReader:
    def __init__(self, interval: float = 1.0) -> None:
        # The timer only runs during a battle, so the last reading stays
        # until reset() at the end of it.
        self._latest = LatestResult(
            self.read,
            default=Timer(),
            interval=interval,
            max_age=None,
            name="timer-reader",
        )

    def read(self, image: np.ndarray) -> Timer:
        """Blocking reading of the timer. If it can't be read (covered, or
        not a battle), the previous reading is kept."""
        reading = read_timer(crop(image, TIMER_BOX))
        if reading is None:
            return self._latest.latest()
        time_left, overtime = reading
        return Timer(time_left=time_left, overtime=overtime)

    def run(self, image: np.ndarray) -> Timer:
        """Return the latest reading, refreshing it in the background."""
        return self._latest.run(image)

    def latest(self) -> Timer:
        """The latest reading, without asking for a new one."""
        return self._latest.latest()

    def reset(self) -> None:
        """Forget the reading, ready for the next battle."""
        self._latest.reset()

    def wait(self, timeout: float | None = None) -> None:
        self._latest.wait(timeout)

    def close(self) -> None:
        self._latest.close()
