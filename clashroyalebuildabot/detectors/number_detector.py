import numpy as np
from PIL import ImageFilter

from clashroyalebuildabot.constants import ELIXIR_BOUNDING_BOX
from clashroyalebuildabot.constants import HP_HEIGHT
from clashroyalebuildabot.constants import HP_WIDTH
from clashroyalebuildabot.constants import NUMBER_CONFIG
from clashroyalebuildabot.namespaces.numbers import NumberDetection
from clashroyalebuildabot.namespaces.numbers import Numbers


class NumberDetector:
    @staticmethod
    def _calculate_elixir(image, window_size=10, threshold=50):
        crop = image.crop(ELIXIR_BOUNDING_BOX)
        std = np.array(crop).std(axis=(0, 2))
        rolling_std = np.convolve(
            std, np.ones(window_size) / window_size, mode="valid"
        )
        change_points = np.nonzero(rolling_std < threshold)[0]
        if len(change_points) == 0:
            elixir = 10
        else:
            elixir = (change_points[0] + window_size) * 10 // crop.width
        return elixir

    @staticmethod
    def _calculate_hp(image, bbox, lhs_colour, rhs_colour, threshold=30):
        crop = np.array(
            image.crop(bbox).filter(ImageFilter.SMOOTH_MORE), dtype=np.float32
        )

        means = np.array(
            [
                np.mean(np.abs(crop - colour), axis=2)
                for colour in [lhs_colour, rhs_colour]
            ]
        )
        best_row = np.argmin(np.sum(np.min(means, axis=0), axis=1))
        means = means[:, best_row, :]
        sides = np.argmin(means, axis=0)
        avg_min_dist = np.mean(np.where(sides, means[1], means[0]))

        if avg_min_dist > threshold:
            hp = 0.0
        else:
            change_point = np.argmin(np.cumsum(2 * sides - 1))
            hp = change_point / (HP_WIDTH - 1)

        return hp

    def run(self, image):
        pred = {}
        for name, (x, y, lhs_colour, rhs_colour) in NUMBER_CONFIG.items():
            bbox = (x, y, x + HP_WIDTH, y + HP_HEIGHT)
            hp = self._calculate_hp(image, bbox, lhs_colour, rhs_colour)
            pred[name] = NumberDetection(bbox, hp)

        elixir = self._calculate_elixir(image)
        pred["elixir"] = NumberDetection(ELIXIR_BOUNDING_BOX, elixir)

        numbers = Numbers(**pred)

        return numbers
