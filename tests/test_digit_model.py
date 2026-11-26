import os

import numpy as np
import pytest

from clashroyalebuildabot.detectors import digit_model
from clashroyalebuildabot.detectors.digit_model import DigitModel, decode
from clashroyalebuildabot.detectors.tower_hp_reader import MODEL_PATH
from clashroyalebuildabot.utils.image import load

# A real tower crop showing 2030.
TOWER = os.path.join(
    os.path.dirname(__file__),
    "data",
    "numbers",
    "tower_left_enemy_princess.png",
)

BLANK = 0


def probs(*columns: tuple[int, float], classes: int = 11) -> np.ndarray:
    """Per column, the class it picks and how sure it is."""
    out = np.zeros((len(columns), classes), np.float32)
    for row, (c, p) in zip(out, columns, strict=True):
        row[:] = (1 - p) / (classes - 1)
        row[c] = p
    return out


def digit(d: int) -> int:
    return d + 1  # class 0 is the blank


def test_merges_repeats_and_drops_blanks():
    text, _ = decode(
        probs(
            (BLANK, 0.9),
            (digit(2), 0.9),
            (digit(2), 0.9),  # the same 2, over two columns
            (BLANK, 0.9),
            (digit(2), 0.9),  # a second 2, after a blank
            (digit(5), 0.9),
        )
    )
    assert text == "225"


def test_a_digit_is_as_sure_as_its_surest_column():
    # The 2 spans a doubtful column and a sure one; the 5 is the least
    # sure digit.
    _, conf = decode(
        probs((digit(2), 0.6), (digit(2), 0.95), (BLANK, 0.9), (digit(5), 0.8))
    )
    assert conf == pytest.approx(0.8)


def test_no_number_is_sure():
    assert decode(probs((BLANK, 0.5), (BLANK, 0.99))) == ("", 1.0)


def test_reads_a_tower():
    assert digit_model.load(MODEL_PATH).read([load(TOWER)]) == [2030]


def test_unsure_readings_count_as_no_number():
    # Nothing is ever this sure, so every reading is unsure.
    reader = DigitModel(MODEL_PATH, min_confidence=1.01)
    assert reader.read([load(TOWER)]) == [None]


def test_a_crop_too_big_for_the_canvas_fails():
    reader = digit_model.load(MODEL_PATH)
    with pytest.raises(ValueError, match="doesn't fit"):
        reader.read([np.zeros((40, 65, 3), np.uint8)])


def test_decodes_any_characters():
    # Class i is the (i-1)th character, as for the timer's "+" and ":".
    text, _ = decode(
        probs((12, 0.9), (2, 0.9), (11, 0.9), (6, 0.9), (10, 0.9), classes=13),
        "0123456789:+",
    )
    assert text == "+1:59"


def test_models_are_shared():
    assert digit_model.load(MODEL_PATH) is digit_model.load(MODEL_PATH)
