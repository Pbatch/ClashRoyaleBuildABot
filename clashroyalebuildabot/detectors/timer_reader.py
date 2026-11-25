"""Read the battle timer, on every frame.

The top-right corner of a battle shows "Time left:" above the minutes and
seconds, or, once regulation time runs out with the towers level, a red box
with "Overtime" above them. A small CNN reads the crop (see digit_model) as
"m:ss", with a "+" in front in overtime.

If the timer can't be read (covered, or not a battle), the last reading
stands. Until the first reading of a battle, the time left is
``UNKNOWN_TIME``.
"""

import os
import re

import numpy as np

from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import TIMER_BOX
from clashroyalebuildabot.detectors import digit_model
from clashroyalebuildabot.game.timer import Timer
from clashroyalebuildabot.utils.image import crop

MODEL_PATH = os.path.join(MODELS_DIR, "timer_digits.onnx")
# The model's characters: a "+" leads in overtime.
CHARS = "0123456789:+"
_TIME = re.compile(r"(\+?)(\d):([0-5]\d)")


def parse(text: str | None) -> Timer | None:
    """The Timer that "m:ss" or "+m:ss" stands for, or None."""
    match = _TIME.fullmatch(text or "")
    if match is None:
        return None
    overtime, minutes, seconds = match.groups()
    return Timer(
        time_left=int(minutes) * 60 + int(seconds), overtime=bool(overtime)
    )


class TimerReader:
    def __init__(self, model_path: str = MODEL_PATH) -> None:
        self._model = digit_model.load(model_path, CHARS)
        self._timer = Timer()

    def run(self, image: np.ndarray) -> Timer:
        """Read the timer in this frame; keep the last reading if it can't
        be read."""
        (text,) = self._model.read_text([crop(image, TIMER_BOX)])
        timer = parse(text)
        if timer is not None:
            self._timer = timer
        return self._timer

    def latest(self) -> Timer:
        """The latest reading, without reading a frame."""
        return self._timer

    def reset(self) -> None:
        """Forget the reading, ready for the next battle."""
        self._timer = Timer()
