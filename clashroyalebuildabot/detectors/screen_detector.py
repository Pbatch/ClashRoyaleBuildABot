import os

import numpy as np
from PIL import Image

from clashroyalebuildabot.constants import IMAGES_DIR
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.namespaces.screens import Screen


class ScreenDetector:
    def __init__(self, hash_size=8, threshold=30):
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

    def run(self, image: Image) -> Screen:
        current_screen = Screens.UNKNOWN
        best_diff = self.threshold

        for screen in Screens.__dict__.values():
            if screen.ltrb is None:
                continue
            # screen.ltb are dimensions scaled to 720x1280 so we scale them :
            treated_ltrb = (
                int(screen.ltrb[0] * image.size[0] / 720),
                int(screen.ltrb[1] * image.size[1] / 1280),
                int(screen.ltrb[2] * image.size[0] / 720),
                int(screen.ltrb[3] * image.size[1] / 1280),
            )
            hash_ = self._image_hash(image.crop(treated_ltrb))
            target_hash = self.screen_hashes[screen]

            diff = np.mean(np.abs(hash_ - target_hash))
            if diff < best_diff:
                best_diff = diff
                current_screen = screen

        return current_screen
