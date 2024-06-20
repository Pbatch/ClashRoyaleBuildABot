import os

import numpy as np
from PIL import Image

from clashroyalebuildabot.constants import IMAGES_DIR
from clashroyalebuildabot.namespaces import Screens


class ScreenDetector:
    def __init__(self, hash_size=8, threshold=20):
        self.hash_size = hash_size
        self.threshold = threshold
        self.screen_hashes = self._calculate_screen_hashes()

    def _image_hash(self, image):
        crop = image.resize(
            (self.hash_size, self.hash_size), Image.Resampling.BILINEAR
        )
        hash_ = np.array(crop, dtype=np.float32).flatten()
        return hash_

    def _calculate_screen_hashes(self):
        screen_hashes = {}
        for screen in Screens.__dict__.values():
            if screen.ltrb is None:
                continue
            path = os.path.join(IMAGES_DIR, "screen", f"{screen.name}.jpg")
            image = Image.open(path)
            screen_hashes[screen] = self._image_hash(image)
        return screen_hashes

    def run(self, image):
        current_screen = Screens.IN_GAME
        best_diff = self.threshold

        for screen in Screens.__dict__.values():
            if screen.ltrb is None:
                continue

            hash_ = self._image_hash(image.crop(screen.ltrb))
            target_hash = self.screen_hashes[screen]

            diff = np.mean(np.abs(hash_ - target_hash))
            if diff < best_diff:
                best_diff = diff
                current_screen = screen

        return current_screen
