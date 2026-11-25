"""
Exercise the parts of the bot that lean hardest on third-party libraries
(onnxruntime, av, OpenCV), so dependency upgrades that break them fail here.
"""

import io
import os

import av
import numpy as np
import pytest

from clashroyalebuildabot.constants.device_screen import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    TILE_HEIGHT,
    TILE_INIT_X,
    TILE_INIT_Y,
    TILE_WIDTH,
)
from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.elixir_reader import ElixirReader
from clashroyalebuildabot.detectors.unit_detector import (
    DETECTOR_UNITS,
    UnitDetector,
)
from clashroyalebuildabot.emulator import Emulator
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.units import Units

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
    return np.zeros((SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH, 3), np.uint8)


def unit_detector():
    return UnitDetector(os.path.join(MODELS_DIR, "units_tiles.onnx"), DECK)


def test_unit_detector_model_runs():
    allies, enemies = unit_detector().run(blank_screenshot())
    assert allies == []
    assert enemies == []


def test_unit_detector_reads_the_tile_grid():
    detector = unit_detector()
    view = np.random.default_rng(0).integers(
        0, 256, (1, *detector.model.input_size, 3), np.uint8
    )
    probs = detector.model(view)
    assert probs.shape == (1, 2 * len(DETECTOR_UNITS), 32, 18)
    assert ((probs >= 0) & (probs <= 1)).all()
    top, bottom = detector.view_rows()
    assert (bottom - top, SCREENSHOT_WIDTH) == detector.model.input_size


def _probs():
    return np.zeros((2 * len(DETECTOR_UNITS), 32, 18), np.float32)


def _channel(unit, side):
    return 2 * DETECTOR_UNITS.index(unit) + (side == "enemy")


def test_unit_detector_keeps_a_swarm_and_drops_edge_doubles():
    detector = unit_detector()
    probs = _probs()
    skeleton = _channel(Units.SKELETON, "enemy")
    # Two skeletons on neighbouring tiles, both confident.
    probs[skeleton, 10, 4] = 0.95
    probs[skeleton, 10, 5] = 0.9
    # A knight whose foot is near a tile edge: a half-confident neighbour.
    knight = _channel(Units.KNIGHT, "enemy")
    probs[knight, 20, 8] = 0.8
    probs[knight, 21, 8] = 0.5
    _, enemies = detector.decode(probs)
    found = sorted(
        (d.unit.name, d.position.tile_x, d.position.tile_y) for d in enemies
    )
    # Rows count down from the top in the model, up from the bottom in the bot.
    assert found == [
        ("knight", 8, 11),
        ("skeleton", 4, 21),
        ("skeleton", 5, 21),
    ]


def _found(detections):
    return sorted(
        (d.unit.name, d.position.tile_x, d.position.tile_y, d.position.conf)
        for d in detections
    )


def test_unit_detector_names_allies_from_the_deck():
    detector = unit_detector()
    probs = _probs()
    # One of ours the model takes for a golem, which isn't in the deck, but
    # rates a little as a knight: it's our knight, as sure as the golem was.
    probs[_channel(Units.GOLEM, "ally"), 25, 3] = 0.9
    probs[_channel(Units.KNIGHT, "ally"), 25, 3] = 0.2
    # Enemies can be anything.
    probs[_channel(Units.GOLEM, "enemy"), 5, 3] = 0.9
    allies, enemies = detector.decode(probs)
    assert _found(allies) == [("knight", 3, 6, pytest.approx(0.9))]
    assert _found(enemies) == [("golem", 3, 26, pytest.approx(0.9))]


def test_unit_detector_keeps_neighbouring_allies_apart():
    detector = unit_detector()
    probs = _probs()
    probs[_channel(Units.KNIGHT, "ally"), 25, 9] = 0.9
    probs[_channel(Units.MUSKETEER, "ally"), 25, 10] = 0.6
    allies, _ = detector.decode(probs)
    assert [(n, x) for n, x, _, _ in _found(allies)] == [
        ("knight", 9),
        ("musketeer", 10),
    ]


def test_unit_detector_counts_spawned_units_as_the_decks():
    # The witch in DECK brings skeletons.
    detector = unit_detector()
    probs = _probs()
    probs[_channel(Units.SKELETON, "ally"), 20, 4] = 0.9
    allies, _ = detector.decode(probs)
    assert [d.unit.name for d in allies] == ["skeleton"]


@pytest.mark.parametrize(("col", "row"), [(0, 0), (17, 0), (0, 31), (9, 15)])
def test_unit_detector_tile_bbox_is_its_tile(col, row):
    left, top, right, bottom = UnitDetector._tile_bbox(col, row)
    assert 0 <= left < right <= SCREENSHOT_WIDTH
    assert 0 <= top < bottom <= SCREENSHOT_HEIGHT
    # The box's centre, back in display pixels, is on the same tile.
    x = (left + right) / 2 * DISPLAY_WIDTH / SCREENSHOT_WIDTH
    y = (top + bottom) / 2 * DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
    tile_x = int((x - TILE_INIT_X) // TILE_WIDTH)
    tile_y = int((DISPLAY_HEIGHT - TILE_INIT_Y - y) // TILE_HEIGHT)
    assert (tile_x, tile_y) == (col, 31 - row)


def test_elixir_reader_runs():
    elixir = ElixirReader().run(blank_screenshot())
    assert 0 <= elixir <= 10


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

    data = _h264_stream()
    last = None
    for chunk in chunker(data):
        last = emulator._get_last_frame(chunk) or last
    for frame in emulator.codec.decode(None) or []:  # flush buffered frames
        last = frame

    assert last is not None
    image = last.to_ndarray(
        width=SCREENSHOT_WIDTH, height=SCREENSHOT_HEIGHT, format="rgb24"
    )
    assert image.shape == (SCREENSHOT_HEIGHT, SCREENSHOT_WIDTH, 3)
