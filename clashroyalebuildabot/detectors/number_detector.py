import numpy as np

from clashroyalebuildabot.constants.screenshot import ELIXIR_BOX


class NumberDetector:
    """Reads elixir from the colours of the elixir bar.

    Tower health is read by the TowerHPReader.
    """

    @staticmethod
    def _calculate_elixir(image, window_size=10, threshold=50):
        crop = image.crop(ELIXIR_BOX)
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

    def run(self, image) -> int:
        return int(self._calculate_elixir(image))
