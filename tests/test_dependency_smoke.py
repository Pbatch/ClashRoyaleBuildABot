"""
Exercise the parts of the bot that lean hardest on third-party libraries
(onnxruntime, av, Pillow), so dependency upgrades that break them fail here.
"""

import io
import os

import av
import numpy as np
import pytest
from PIL import Image

from clashroyalebuildabot.constants import (
    MODELS_DIR,
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.number_detector import NumberDetector
from clashroyalebuildabot.detectors.unit_detector import UnitDetector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.namespaces.cards import Cards

DECK = [
    Cards.ARCHERS,
    Cards.BABY_DRAGON,
    Cards.CANNON,
    Cards.GOBLIN_BARREL,
    Cards.KNIGHT,
    Cards.MINIPEKKA,
    Cards.MUSKETEER,
    Cards.WITCH,
]


def blank_screenshot():
    return Image.new("RGB", (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT))


def test_unit_detector_models_run():
    detector = UnitDetector(
        os.path.join(MODELS_DIR, "units_M_480x352.onnx"), DECK
    )
    allies, enemies = detector.run(blank_screenshot())
    assert allies == [] and enemies == []


def test_side_detector_model_runs():
    detector = UnitDetector(
        os.path.join(MODELS_DIR, "units_M_480x352.onnx"), DECK
    )
    side = detector.side_detector.run(Image.new("RGB", (20, 20)))
    assert side in ("ally", "enemy")


def test_number_detector_runs():
    numbers = NumberDetector().run(blank_screenshot())
    assert 0 <= numbers.elixir.number <= 10


def _h264_stream(width=64, height=96, n_frames=5):
    """Encode a few frames as a raw H.264 stream, like `screenrecord` emits."""
    buffer = io.BytesIO()
    with av.open(buffer, "w", format="h264") as container:
        stream = container.add_stream("libx264", rate=10)
        stream.width, stream.height = width, height
        stream.pix_fmt = "yuv420p"
        for i in range(n_frames):
            pixels = np.full((height, width, 3), i * 40, dtype=np.uint8)
            frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
            container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
    return buffer.getvalue()


def _readline_chunks(data):
    """Split like the emulator's readline() loop: after each newline byte."""
    return io.BytesIO(data).readlines()


def _fixed_chunks(data, size=512):
    return [data[i : i + size] for i in range(0, len(data), size)]


@pytest.mark.parametrize("chunker", [_readline_chunks, _fixed_chunks])
def test_h264_frames_decode_to_screenshots(chunker):
    try:
        av.codec.Codec("libx264", "w")
    except av.codec.codec.UnknownCodecError:
        pytest.skip("libx264 encoder not available in this av build")

    emulator = Emulator.__new__(Emulator)  # skip adb setup in __init__
    emulator.codec = av.codec.CodecContext.create("h264", "r")
    emulator.os_name = "linux"

    data = _h264_stream()
    last = None
    for chunk in chunker(data):
        last = emulator._get_last_frame(chunk) or last
    for frame in emulator.codec.decode(None) or []:  # flush buffered frames
        last = frame

    assert last is not None
    image = last.reformat(
        width=SCREENSHOT_WIDTH, height=SCREENSHOT_HEIGHT, format="rgb24"
    ).to_image()
    assert image.size == (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT)
