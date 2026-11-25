"""Tiny thumbnails of parts of a frame, and their hex form.

The screen detector recognises which screen is showing by comparing a
thumbnail of where a button should be with a reference thumbnail. The
references ship as hex strings in constants/screen_hashes.py, made with these
same functions by the scripts in dev/, so a reference and a frame's thumbnail
always match up.
"""

import cv2
import numpy as np

from clashroyalebuildabot.utils.image import resize


def thumbnail(
    image: np.ndarray, size: tuple[int, int], grey: bool = False
) -> np.ndarray:
    """An RGB image shrunk to ``size`` (width, height), as uint8: (height,
    width, 3), or (height, width) if ``grey``."""
    small = resize(image, size)
    return cv2.cvtColor(small, cv2.COLOR_RGB2GRAY) if grey else small


def to_hex(thumb: np.ndarray) -> str:
    """A thumbnail's pixels, row by row, as hex."""
    return thumb.astype(np.uint8).tobytes().hex()


def from_hex(
    value: str, size: tuple[int, int], grey: bool = False
) -> np.ndarray:
    """The thumbnail ``to_hex`` made, given its ``size`` (width, height)."""
    width, height = size
    shape = (height, width) if grey else (height, width, 3)
    return np.frombuffer(bytes.fromhex(value), np.uint8).reshape(shape)
