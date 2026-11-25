import numpy as np

from clashroyalebuildabot.constants.screenshot import ELIXIR_BOX
from clashroyalebuildabot.utils.image import crop


class ElixirReader:
    """Reads elixir from the colours of the elixir bar: the filled part
    varies more in colour than the empty part."""

    @staticmethod
    def _calculate_elixir(
        image: np.ndarray, window_size: int = 10, threshold: float = 50
    ) -> int:
        bar = crop(image, ELIXIR_BOX)
        std = bar.std(axis=(0, 2))
        rolling_std = np.convolve(
            std, np.ones(window_size) / window_size, mode="valid"
        )
        change_points = np.nonzero(rolling_std < threshold)[0]
        if len(change_points) == 0:
            elixir = 10
        else:
            elixir = (change_points[0] + window_size) * 10 // bar.shape[1]
        return int(elixir)

    def run(self, image: np.ndarray) -> int:
        return self._calculate_elixir(image)
