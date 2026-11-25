"""Tell from the pixels of the current frame whether it shows a battle.

The screen detector's answer is a second or more old, so it says IN_GAME a
moment after a battle starts and keeps saying so while the results screen
is up. This decides from the frame itself instead, by looking for the pink
elixir drop at the left end of the elixir bar, which only a battle shows.
It compares a few pixels against a reference, so it costs next to nothing.
"""

import os

import cv2
import numpy as np

from clashroyalebuildabot.constants.paths import IMAGES_DIR
from clashroyalebuildabot.constants.screenshot import BATTLE_CHECK_BOX
from clashroyalebuildabot.utils.image import crop, load, resize

REFERENCE_PATH = os.path.join(IMAGES_DIR, "screen", "in_game.jpg")


class BattleCheck:
    def __init__(self, hash_size: int = 8, threshold: float = 30) -> None:

        self.hash_size = hash_size
        # Mean difference per colour channel, out of 255.
        self.threshold = threshold
        self.reference = self._hash(load(REFERENCE_PATH))

    def _hash(self, image: np.ndarray) -> np.ndarray:
        small = resize(
            image, (self.hash_size, self.hash_size), cv2.INTER_LINEAR
        )
        return small.astype(np.float32)

    def run(self, image: np.ndarray) -> bool:
        drop = crop(image, BATTLE_CHECK_BOX)
        diff = np.mean(np.abs(self._hash(drop) - self.reference))
        return bool(diff < self.threshold)
