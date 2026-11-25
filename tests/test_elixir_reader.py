import os

import numpy as np
import pytest

from clashroyalebuildabot.constants.screenshot import ELIXIR_NUMBER_BOX
from clashroyalebuildabot.detectors.elixir_reader import (
    ElixirReader,
    elixir_from_bar,
)
from clashroyalebuildabot.utils.image import load

DATA = os.path.join(os.path.dirname(__file__), "data", "elixir")
# Each crop covers the elixir number and bar: ELIXIR_NUMBER_BOX and
# ELIXIR_BOX together.
CROP_BOX = (100, 618, 360, 646)
# In these, a card is selected, so the bar has its white cost outline, which
# the old reader counted as elixir.
SELECTED = [0, 1, 3]


def frame(elixir: int) -> np.ndarray:
    """A black frame with a real crop of the elixir bar pasted in."""
    image = np.zeros((652, 368, 3), np.uint8)
    left, top, right, bottom = CROP_BOX
    image[top:bottom, left:right] = load(
        os.path.join(DATA, f"elixir_{elixir}.png")
    )
    return image


@pytest.mark.parametrize("elixir", [0, 1, 3, 7, 10])
def test_reads_elixir(elixir):
    assert ElixirReader().run(frame(elixir)) == elixir


@pytest.mark.parametrize("elixir", [0, 1, 3, 7, 10])
def test_bar_alone_reads_elixir(elixir):
    # While the number fades out as elixir ticks over.
    image = frame(elixir)
    # Black out the number, up to where the bar's fill is measured from.
    left, top, _, bottom = ELIXIR_NUMBER_BOX
    image[top:bottom, left : left + 22] = 0
    assert elixir_from_bar(image) == elixir


@pytest.mark.parametrize("elixir", SELECTED)
def test_selected_cards_outline_isnt_counted(elixir):
    assert elixir_from_bar(frame(elixir)) == elixir


def test_no_bar_is_no_elixir():
    assert ElixirReader().run(np.zeros((652, 368, 3), np.uint8)) == 0
