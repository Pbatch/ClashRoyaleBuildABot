"""
Exercise the parts of the bot that lean hardest on third-party libraries
(onnxruntime, OpenCV), so dependency upgrades that break them fail here.
"""

import numpy as np
import pytest

from clashroyalebuildabot.constants.device_screen import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    TILE_HEIGHT,
    TILE_INIT_X,
    TILE_INIT_Y,
    TILE_WIDTH,
    tile_box,
)
from clashroyalebuildabot.constants.screenshot import (
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
)
from clashroyalebuildabot.detectors.elixir_reader import ElixirReader
from clashroyalebuildabot.detectors.unit_detector import (
    DETECTOR_UNITS,
    UnitDetector,
)
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
    return UnitDetector(DECK)


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
    assert probs.shape == (1, 2 * len(detector.units), 32, 18)
    assert detector.units == DETECTOR_UNITS[: len(detector.units)]
    assert ((probs >= 0) & (probs <= 1)).all()
    top, bottom = detector.view_rows()
    assert (bottom - top, SCREENSHOT_WIDTH) == detector.model.input_size


def _probs(detector):
    return np.zeros((2 * len(detector.units), 32, 18), np.float32)


def _channel(detector, unit, side):
    return 2 * detector.units.index(unit) + (side == "enemy")


def test_unit_detector_keeps_a_swarm_and_drops_edge_doubles():
    detector = unit_detector()
    probs = _probs(detector)
    skeleton = _channel(detector, Units.SKELETON, "enemy")
    # Two skeletons on neighbouring tiles, both confident.
    probs[skeleton, 10, 4] = 0.95
    probs[skeleton, 10, 5] = 0.9
    # A knight whose foot is near a tile edge: a half-confident neighbour.
    knight = _channel(detector, Units.KNIGHT, "enemy")
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
    probs = _probs(detector)
    # One of ours the model takes for a golem, which isn't in the deck, but
    # rates a little as a knight: it's our knight, as sure as the golem was.
    probs[_channel(detector, Units.GOLEM, "ally"), 25, 3] = 0.9
    probs[_channel(detector, Units.KNIGHT, "ally"), 25, 3] = 0.2
    # Enemies can be anything.
    probs[_channel(detector, Units.GOLEM, "enemy"), 5, 3] = 0.9
    allies, enemies = detector.decode(probs)
    assert _found(allies) == [("knight", 3, 6, pytest.approx(0.9))]
    assert _found(enemies) == [("golem", 3, 26, pytest.approx(0.9))]


def test_unit_detector_keeps_neighbouring_allies_apart():
    detector = unit_detector()
    probs = _probs(detector)
    probs[_channel(detector, Units.KNIGHT, "ally"), 25, 9] = 0.9
    probs[_channel(detector, Units.MUSKETEER, "ally"), 25, 10] = 0.6
    allies, _ = detector.decode(probs)
    assert [(n, x) for n, x, _, _ in _found(allies)] == [
        ("knight", 9),
        ("musketeer", 10),
    ]


def test_unit_detector_counts_spawned_units_as_the_decks():
    # The witch in DECK brings skeletons.
    detector = unit_detector()
    probs = _probs(detector)
    probs[_channel(detector, Units.SKELETON, "ally"), 20, 4] = 0.9
    allies, _ = detector.decode(probs)
    assert [d.unit.name for d in allies] == ["skeleton"]


@pytest.mark.parametrize(
    ("tile_x", "tile_y"), [(0, 0), (17, 0), (0, 31), (9, 15)]
)
def test_tile_box_is_its_tile(tile_x, tile_y):
    left, top, right, bottom = tile_box(tile_x, tile_y)
    assert 0 <= left < right <= SCREENSHOT_WIDTH
    assert 0 <= top < bottom <= SCREENSHOT_HEIGHT
    # The box's centre, back in display pixels, is on the same tile.
    x = (left + right) / 2 * DISPLAY_WIDTH / SCREENSHOT_WIDTH
    y = (top + bottom) / 2 * DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
    assert int((x - TILE_INIT_X) // TILE_WIDTH) == tile_x
    assert int((DISPLAY_HEIGHT - TILE_INIT_Y - y) // TILE_HEIGHT) == tile_y


def test_elixir_reader_runs():
    elixir = ElixirReader().run(blank_screenshot())
    assert 0 <= elixir <= 10
