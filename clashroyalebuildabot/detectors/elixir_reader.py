"""Read how much elixir the player has.

The game writes it beside the elixir drop, in the same font as tower HP,
and a small CNN reads it (see digit_model). That number fades out for a
moment each time elixir ticks over, and the model skips a number it isn't
sure of; then it's read from how far the bar's pink fill reaches instead.

Selecting a card draws a white outline on the bar, showing what the card
costs. The fill is measured by its pink, so the outline doesn't count, and
small breaks in the pink where the outline crosses it are bridged. A wider
break can still cut the fill short, so the bar may read low, never high: the
bot then waits a moment for elixir it has, rather than playing a card it
can't afford, which the game refuses and leaves the card selected.
"""

import os

import numpy as np

from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import (
    ELIXIR_BOX,
    ELIXIR_NUMBER_BOX,
)
from clashroyalebuildabot.detectors import digit_model
from clashroyalebuildabot.utils.image import crop

MODEL_PATH = os.path.join(MODELS_DIR, "elixir_digits.onnx")
MAX_ELIXIR = 10

# Where the fill starts, and how far each elixir takes it, in screenshot
# pixels from the left of ELIXIR_BOX. Measured on battle frames against the
# number beside the drop.
FILL_START = 4
PIXELS_PER_ELIXIR = 24.3
# The fill is measured from here, right of the number written over the bar's
# left end.
FILL_PROBE = 25
# The widest break in the pink that's bridged, in pixels.
MAX_GAP = 4


def _pink_columns(bar: np.ndarray) -> np.ndarray:
    """Whether each column of the bar is mostly the fill's pink: its usual
    pink, or the pale pink the elixir a selected card would cost turns. (A
    selected card's cost outline is near white, and doesn't count.)"""
    r, g, b = (bar[..., i].astype(np.int16) for i in range(3))
    pink = (r > 140) & (b > 150) & (g < 150) & (r - g > 50)
    pale = (r > 220) & (b > 220) & (g > 160) & (g < 242)
    return (pink | pale).mean(axis=0) > 0.5


def bar_shows(image: np.ndarray) -> bool:
    """Whether any of the elixir bar's pink fill is on screen."""
    return bool(_pink_columns(crop(image, ELIXIR_BOX)).any())


def elixir_from_bar(image: np.ndarray) -> int:
    """Elixir from how far the pink fill reaches."""
    pink = _pink_columns(crop(image, ELIXIR_BOX))
    if not pink[FILL_PROBE]:
        return 0
    # Walk right from the probe, bridging breaks of up to MAX_GAP columns.
    end = FILL_PROBE
    for x in range(FILL_PROBE + 1, len(pink)):
        if x - end > MAX_GAP:
            break
        if pink[x]:
            end = x
    # Fill that has just passed an elixir's mark counts as that elixir.
    elixir = (end + 1 - FILL_START) / PIXELS_PER_ELIXIR + 0.1
    return int(np.clip(elixir, 0, MAX_ELIXIR))


class ElixirReader:
    def __init__(self, model_path: str = MODEL_PATH) -> None:
        self._model = digit_model.load(model_path)

    def run(self, image: np.ndarray) -> int:
        (number,) = self._model.read([crop(image, ELIXIR_NUMBER_BOX)])
        if number is not None and number <= MAX_ELIXIR:
            return number
        return elixir_from_bar(image)
