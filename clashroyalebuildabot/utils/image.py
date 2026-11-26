"""Small helpers for frames held as numpy arrays.

Frames are (height, width, 3) uint8 arrays in RGB order, the layout the
models take. OpenCV works in BGR, so images are converted when they're read
from or written to disk.

Boxes are (left, top, right, bottom), as in constants.screenshot.
"""

import cv2
import numpy as np

# (left, top, right, bottom), in pixels.
type Box = tuple[float, float, float, float]


def crop(image: np.ndarray, box: Box, fill: int = 0) -> np.ndarray:
    """The part of ``image`` inside ``box``.

    Coordinates are rounded to whole pixels. Inside the image, the crop is a
    view, not a copy. Any part of the box outside the image is ``fill``
    (black by default), so a crop is always the size of its box.
    """
    left, top, right, bottom = (round(v) for v in box)
    height, width = image.shape[:2]
    if 0 <= left <= right <= width and 0 <= top <= bottom <= height:
        return image[top:bottom, left:right]

    out = np.full(
        (max(0, bottom - top), max(0, right - left), *image.shape[2:]),
        fill,
        dtype=image.dtype,
    )
    x0, y0 = max(left, 0), max(top, 0)
    x1, y1 = min(right, width), min(bottom, height)
    if x0 < x1 and y0 < y1:
        out[y0 - top : y1 - top, x0 - left : x1 - left] = image[y0:y1, x0:x1]
    return out


def resize(
    image: np.ndarray,
    size: tuple[int, int],
    interpolation: int = cv2.INTER_CUBIC,
) -> np.ndarray:
    """Resize ``image`` to ``size``, given as (width, height).

    Shrinking averages each output pixel's whole area, as Pillow does, so
    fine detail doesn't alias. ``interpolation`` is used when enlarging.
    """
    height, width = image.shape[:2]
    if size[0] < width or size[1] < height:
        interpolation = cv2.INTER_AREA
    return cv2.resize(image, size, interpolation=interpolation)


def load(path: str) -> np.ndarray:
    """Read an image file as RGB."""
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Can't read the image {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def save(path: str, image: np.ndarray) -> None:
    """Write an RGB image to a file, in the format its extension names."""
    if not cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR)):
        raise OSError(f"Can't write the image {path}")


def encode_png(image: np.ndarray) -> bytes:
    ok, data = cv2.imencode(".png", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    if not ok:
        raise ValueError("Can't encode the image as PNG")
    return data.tobytes()
