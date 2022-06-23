import os

import numpy as np
from PIL import Image

from clashroyalebuildabot.data.constants import SCREEN_CONFIG, DATA_DIR


class ScreenDetector:
    def __init__(self, hash_size=8, threshold=20):
        self.hash_size = hash_size
        self.threshold = threshold

        self.screen_hashes = self._calculate_screen_hashes()

    def _calculate_screen_hashes(self):
        screen_hashes = np.zeros((len(SCREEN_CONFIG), self.hash_size * self.hash_size * 3), dtype=np.int32)
        for i, name in enumerate(SCREEN_CONFIG.keys()):
            path = os.path.join(f'{DATA_DIR}/images/screen', f'{name}.png')
            image = Image.open(path)
            hash_ = np.array(image.resize((self.hash_size, self.hash_size), Image.BILINEAR)).flatten()
            screen_hashes[i] = hash_
        return screen_hashes

    def run(self, image):
        crop_hashes = np.array([np.array(image.crop(v['bbox'])
                                         .resize((self.hash_size, self.hash_size), Image.BILINEAR))
                                .flatten()
                                for v in SCREEN_CONFIG.values()])
        hash_diffs = np.mean(np.abs(crop_hashes - self.screen_hashes), axis=1)

        # No crops match
        if min(hash_diffs) > self.threshold:
            screen = 'in_game'
        else:
            screen = list(SCREEN_CONFIG.keys())[np.argmin(hash_diffs)]

        return screen
