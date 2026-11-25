"""Tell which screen a frame shows from a few fixed parts of it.

A battle is recognised by its HUD, read with the models the bot reads it
with anyway: the timer shows a time, read for sure, and the elixir bar is
there (its number, or its pink fill). Both are needed. The timer stays on
screen, frozen, through the end-of-battle animation and onto the results
screen, after the card and elixir bars have gone; and menus have pink of
their own. Deciding from the frame itself means the bot plays as soon as a
battle starts and stops as soon as it ends.

Outside a battle, the bot only acts on three screens: the lobby, where it
taps Battle, and the two layouts of the results screen, where it taps Play
Again or OK. Each is recognised by its buttons, which look the same whatever
the arena, event or background behind them. Anything else is UNKNOWN, which
the bot waits through.

Each button check compares a small thumbnail of where the button should be
with its own thumbnail, in constants/screen_hashes.py. All of it costs next
to nothing, so every frame is classified as it arrives.
"""

import numpy as np

from clashroyalebuildabot.constants.screen_hashes import BUTTON_HASHES
from clashroyalebuildabot.constants.screenshot import (
    ELIXIR_NUMBER_BOX,
    LOBBY_BATTLE_BOX,
    RESULTS_CENTRE_OK_BOX,
    RESULTS_OK_BOX,
    RESULTS_PLAY_AGAIN_BOX,
    TIMER_BOX,
)
from clashroyalebuildabot.detectors import (
    digit_model,
    elixir_reader,
    timer_reader,
)
from clashroyalebuildabot.game import ScreenName
from clashroyalebuildabot.utils.image import Box, crop
from clashroyalebuildabot.utils.thumbnail import from_hex, thumbnail

THUMBNAIL_SIZE = (16, 6)
# How sure of the time the timer model must be to call it a battle. On
# battle frames it's 0.99 or more; on menus it reads nothing.
BATTLE_TIMER_CONFIDENCE = 0.95


def screen_thumbnail(
    image: np.ndarray, box: Box, size: tuple[int, int] = THUMBNAIL_SIZE
) -> np.ndarray:
    """A box of the frame as colour pixels, 16x6 unless ``size`` is given."""
    return thumbnail(crop(image, box), size)


def _differs(a: np.ndarray, reference: np.ndarray) -> float:
    """Mean difference per colour channel, out of 255."""
    return float(np.mean(np.abs(a.astype(np.float32) - reference)))


class ScreenDetector:
    def __init__(self, threshold: float = 20) -> None:
        # On real frames a button matches its thumbnail within 5, and
        # anything else differs by 38 or more.
        self.threshold = threshold
        self.references = {
            name: from_hex(value, THUMBNAIL_SIZE)
            for name, value in BUTTON_HASHES.items()
        }
        self.timer = digit_model.load(
            timer_reader.MODEL_PATH, timer_reader.CHARS
        )
        self.elixir = digit_model.load(elixir_reader.MODEL_PATH)

    def in_battle(self, image: np.ndarray) -> bool:
        """The timer shows a time, read for sure, and the elixir bar is
        there."""
        ((text, confidence),) = self.timer.read_scored(
            [crop(image, TIMER_BOX)]
        )
        if (
            timer_reader.parse(text) is None
            or confidence < BATTLE_TIMER_CONFIDENCE
        ):
            return False
        (number,) = self.elixir.read([crop(image, ELIXIR_NUMBER_BOX)])
        return number is not None or elixir_reader.bar_shows(image)

    def _shows(self, image: np.ndarray, button: str, box: Box) -> bool:
        diff = _differs(screen_thumbnail(image, box), self.references[button])
        return diff < self.threshold

    def run(self, image: np.ndarray) -> ScreenName:
        if self.in_battle(image):
            return ScreenName.IN_GAME
        if self._shows(image, "battle", LOBBY_BATTLE_BOX):
            return ScreenName.LOBBY
        if self._shows(image, "ok", RESULTS_OK_BOX) and self._shows(
            image, "play_again", RESULTS_PLAY_AGAIN_BOX
        ):
            return ScreenName.END_OF_GAME
        if self._shows(image, "ok", RESULTS_CENTRE_OK_BOX):
            return ScreenName.BYPASS_END_OF_GAME
        return ScreenName.UNKNOWN
