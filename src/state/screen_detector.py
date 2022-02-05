from src.data.constants import SCREEN_CONFIG, DATA_DIR
from PIL import Image
from imagehash import average_hash


class ScreenDetector:
    def __init__(self, threshold=10):
        self.threshold = threshold
        self.screen_hashes = self._calculate_screen_hashes()

    @staticmethod
    def _calculate_screen_hashes():
        screen_hashes = []
        for name, _, _ in SCREEN_CONFIG:
            path = f'{DATA_DIR}/images/screen/{name}.png'
            image = Image.open(path)
            image_hash = average_hash(image, hash_size=16)
            screen_hashes.append(image_hash)
        return screen_hashes

    def run(self, image):
        screen = {}
        for (name, bounding_box, _), screen_hash in zip(SCREEN_CONFIG, self.screen_hashes):
            crop = image.crop(bounding_box)
            crop_hash = average_hash(crop, hash_size=16)
            hash_diff = crop_hash - screen_hash
            screen[name] = hash_diff < self.threshold

        # Default to "in_game" if not in the lobby or at the end of a game
        screen['in_game'] = not any([k for k in screen.values()])

        return screen
