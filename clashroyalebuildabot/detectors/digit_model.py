"""Read numbers drawn in the game's font with a small CNN.

The model reads a batch of crops at once. Each crop is pasted at the top
left of a black canvas the model's size, and the model gives, for each of
a row of columns across it, the chance of a blank or of each digit (CTC).
The reading is the best column-by-column path, with repeats merged and
blanks dropped, so it can be any number of digits, or none.

Tower HP, the timer and elixir each have a model, trained in dev/digits on
crops drawn from the game's font onto real backgrounds, plus real crops
(train_digits.py for tower HP, train_hud.py for the timer and elixir).
"""

from collections.abc import Sequence
from functools import cache

import numpy as np

from clashroyalebuildabot.detectors.onnx_model import OnnxModel

# The model's classes: blank, then these characters.
CHARS = "0123456789"
# A reading counts from this confidence: its least sure digit's best
# column. Below it, the number is taken as unreadable, rather than guessed.
MIN_CONFIDENCE = 0.8


def decode(probs: np.ndarray, chars: str = CHARS) -> tuple[str, float]:
    """(text, confidence) from one crop's (columns, classes) probabilities,
    class 0 being the blank and class i the (i-1)th of ``chars``.
    A digit's confidence is its surest column, since a digit can span
    several; a reading's is its least sure digit, and 1 for no number."""
    best = probs.argmax(-1)
    text, prev, conf, run = "", 0, 1.0, 0.0
    for c, p in zip(best, probs.max(-1), strict=True):
        if c != prev:
            if prev:
                conf = min(conf, run)
            run = 0.0
            if c:
                text += chars[c - 1]
        if c:
            run = max(run, float(p))
        prev = c
    if prev:
        conf = min(conf, run)
    return text, conf


class DigitModel:
    """A digit-reading model, and the characters its classes stand for."""

    def __init__(
        self,
        path: str,
        chars: str = CHARS,
        min_confidence: float = MIN_CONFIDENCE,
    ) -> None:
        self.model = OnnxModel(path)
        self.chars = chars
        self.min_confidence = min_confidence

    def canvas(self, crops: Sequence[np.ndarray]) -> np.ndarray:
        """The crops, each at the top left of its own black canvas."""
        height, width = self.model.input_size
        batch = np.zeros((len(crops), height, width, 3), np.uint8)
        for image, crop in zip(batch, crops, strict=True):
            h, w = crop.shape[:2]
            if h > height or w > width:
                raise ValueError(
                    f"A {w}x{h} crop doesn't fit the model's "
                    f"{width}x{height} canvas"
                )
            image[:h, :w] = crop
        return batch

    def read_scored(
        self, crops: Sequence[np.ndarray]
    ) -> list[tuple[str, float]]:
        """(text, confidence) for each crop, however unsure; "" for no
        number."""
        if not crops:
            return []
        return [decode(p, self.chars) for p in self.model(self.canvas(crops))]

    def read_text(self, crops: Sequence[np.ndarray]) -> list[str | None]:
        """The text in each crop, or None where there's none, or it can't
        be read for sure."""
        return [
            text if text and conf >= self.min_confidence else None
            for text, conf in self.read_scored(crops)
        ]

    def read(self, crops: Sequence[np.ndarray]) -> list[int | None]:
        """The number in each crop, or None where there's none, or it
        can't be read for sure."""
        return [None if t is None else int(t) for t in self.read_text(crops)]


@cache
def load(path: str, chars: str = CHARS) -> DigitModel:
    """One model per file and process, shared by every reader: loading it
    isn't free, and a session can run from any thread."""
    return DigitModel(path, chars)
