"""Confirm from the pixels of the current frame that it shows a battle.

The screen detector's answer is a second or more old, so when a battle ends
it still says IN_GAME while the results screen is up. Before the bot plays a
card, this checks the frame itself for the pink elixir drop at the left end
of the elixir bar, which only a battle shows. It compares a few pixels
against a reference, so it costs next to nothing.
"""

import os

import numpy as np
from PIL import Image

from clashroyalebuildabot.constants.paths import IMAGES_DIR
from clashroyalebuildabot.constants.screenshot import BATTLE_CHECK_BOX

REFERENCE_PATH = os.path.join(IMAGES_DIR, "screen", "in_game.jpg")


class BattleCheck:
    def __init__(self, hash_size=8, threshold=30):
        self.hash_size = hash_size
        # Mean difference per colour channel, out of 255.
        self.threshold = threshold
        self.reference = self._hash(Image.open(REFERENCE_PATH))

    def _hash(self, image: Image.Image) -> np.ndarray:
        small = image.convert("RGB").resize(
            (self.hash_size, self.hash_size), Image.Resampling.BILINEAR
        )
        return np.array(small, dtype=np.float32)

    def run(self, image: Image.Image) -> bool:
        crop = image.crop(BATTLE_CHECK_BOX)
        diff = np.mean(np.abs(self._hash(crop) - self.reference))
        return bool(diff < self.threshold)
