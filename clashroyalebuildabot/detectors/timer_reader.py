"""Read the battle timer with a small vision model.

The top-right corner of a battle shows "Time left:" above the minutes and
seconds, or "Overtime:" once regulation time runs out with the towers level.
A crop of it is sent to the same model the screen detector uses, and its
answer is constrained to a schema: whether it's overtime, then the minutes
and seconds.

It's read in the background, at most once per ``interval`` seconds, so a
reading is about a second old. Until the first reading of a battle, the time
left is ``UNKNOWN_TIME``.
"""

from loguru import logger
from PIL import Image
from pydantic import BaseModel, Field

from clashroyalebuildabot.constants.screenshot import TIMER_BOX
from clashroyalebuildabot.detectors.background import LatestResult
from clashroyalebuildabot.detectors.vlm_client import VisionClient, VisionError
from clashroyalebuildabot.game.numbers import Timer

# The crop is enlarged before it's sent, so the digits are easy to read.
CROP_SCALE = 4


class TimerReading(BaseModel):
    # The label comes first, so the model has read it before the digits.
    overtime: bool = Field(
        description='true if the label says "Overtime", '
        'false if it says "Time left"'
    )
    minutes: int = Field(ge=0, le=5, description="the minutes, before the :")
    seconds: int = Field(ge=0, le=59, description="the seconds, after the :")


PROMPT = (
    "This crop shows the battle timer from the game Clash Royale: a label, "
    'either "Time left:" or "Overtime:", above a time such as 1:57. Answer '
    "in JSON with `overtime`: true if the label says Overtime, `minutes`: "
    "the number before the colon, and `seconds`: the number after it."
)


class TimerReader:
    def __init__(self, client: VisionClient, interval=1.0):
        self.client = client
        # The timer only runs during a battle, so the last reading stays
        # until reset() at the end of it.
        self._latest = LatestResult(
            self.read,
            default=Timer(),
            interval=interval,
            max_age=None,
            name="timer-reader",
        )

    def read(self, image: Image.Image) -> Timer:
        """Blocking reading of the timer. If it fails, the previous reading
        is kept."""
        left, top, right, bottom = TIMER_BOX
        crop = image.crop(TIMER_BOX).resize(
            ((right - left) * CROP_SCALE, (bottom - top) * CROP_SCALE),
            Image.Resampling.LANCZOS,
        )
        try:
            answer = self.client.ask(crop, PROMPT, TimerReading)
        except VisionError as e:
            logger.warning(f"Timer reading failed: {e}")
            return self._latest.latest()
        return Timer(
            time_left=answer.minutes * 60 + answer.seconds,
            overtime=answer.overtime,
        )

    def run(self, image: Image.Image) -> Timer:
        """Return the latest reading, refreshing it in the background."""
        return self._latest.run(image)

    def latest(self) -> Timer:
        """The latest reading, without asking for a new one."""
        return self._latest.latest()

    def reset(self):
        """Forget the reading, ready for the next battle."""
        self._latest.reset()

    def wait(self, timeout: float | None = None):
        self._latest.wait(timeout)

    def close(self):
        self._latest.close()
