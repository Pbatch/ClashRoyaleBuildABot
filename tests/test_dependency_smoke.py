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
from clashroyalebuildabot.detectors.opponent_deck import OpponentDeck
from clashroyalebuildabot.detectors.unit_detector import (
    DETECTOR_UNITS,
    UnitDetector,
)
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.towers import Tower, Towers
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
    probs[_channel(detector, Units.GOLEM, "ally"), 25, 6] = 0.9
    probs[_channel(detector, Units.KNIGHT, "ally"), 25, 6] = 0.2
    # Enemies can be anything.
    probs[_channel(detector, Units.GOLEM, "enemy"), 5, 6] = 0.9
    allies, enemies = detector.decode(probs)
    assert _found(allies) == [("knight", 6, 6, pytest.approx(0.9))]
    assert _found(enemies) == [("golem", 6, 26, pytest.approx(0.9))]


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


def test_unit_detector_scores_every_unit_on_the_tile():
    detector = unit_detector()
    probs = _probs(detector)
    archer = _channel(detector, Units.ARCHER, "enemy")
    musketeer = _channel(detector, Units.MUSKETEER, "enemy")
    probs[archer, 5, 6] = 0.8
    probs[musketeer, 5, 6] = 0.5
    probs[_channel(detector, Units.ARCHER, "ally"), 5, 6] = 0.2
    # Named as their musketeer, but scored as the model saw it.
    _, (enemy,) = detector.decode(probs, _opponent(Units.MUSKETEER))
    assert enemy.unit == Units.MUSKETEER
    assert enemy.units == detector.units
    expected = np.zeros((2, len(detector.units)), np.float32)
    expected[1, archer // 2] = 0.8
    expected[1, musketeer // 2] = 0.5
    expected[0, archer // 2] = 0.2
    np.testing.assert_array_equal(enemy.scores, expected)


def _opponent(*units):
    deck = OpponentDeck()
    for unit in units:
        deck.saw(unit)
    return deck


def test_unit_detector_names_enemies_from_their_cards():
    detector = unit_detector()
    probs = _probs(detector)
    # They play a musketeer. The model rates it a little higher as an
    # archer, which they haven't been seen to play: it's their musketeer.
    probs[_channel(detector, Units.ARCHER, "enemy"), 5, 6] = 0.8
    probs[_channel(detector, Units.MUSKETEER, "enemy"), 5, 6] = 0.6
    # And a golem the model is sure of: a card they hadn't played yet.
    probs[_channel(detector, Units.GOLEM, "enemy"), 10, 8] = 0.9
    probs[_channel(detector, Units.MUSKETEER, "enemy"), 10, 8] = 0.1
    _, enemies = detector.decode(probs, _opponent(Units.MUSKETEER))
    assert _found(enemies) == [
        ("golem", 8, 21, pytest.approx(0.9)),
        ("musketeer", 6, 26, pytest.approx(0.8)),
    ]
    # Knowing nothing of their deck, the model's names stand: an archer and
    # a musketeer on the one tile.
    _, enemies = detector.decode(probs)
    assert sorted(d.unit.name for d in enemies) == [
        "archer",
        "golem",
        "musketeer",
    ]


def test_unit_detector_names_enemies_only_from_a_complete_deck():
    detector = unit_detector()
    opponent = _opponent(
        Units.GOLEM,
        Units.BABY_DRAGON,
        Units.MEGA_MINION,
        Units.LUMBERJACK,
        Units.NIGHT_WITCH,
        Units.ELECTRO_DRAGON,
        Units.TOMBSTONE,
        Units.MUSKETEER,
    )
    assert opponent.complete
    probs = _probs(detector)
    # Sure it's a pekka, barely a musketeer: still a card of theirs.
    probs[_channel(detector, Units.PEKKA, "enemy"), 5, 6] = 0.9
    probs[_channel(detector, Units.MUSKETEER, "enemy"), 5, 6] = 0.05
    # A unit with no rating for any of their units is still one of theirs.
    probs[_channel(detector, Units.HOG_RIDER, "enemy"), 10, 8] = 0.9
    _, enemies = detector.decode(probs, opponent)
    possible = opponent.possible_units()
    assert len(enemies) == 2
    assert all(d.unit in possible for d in enemies)
    assert _found(enemies)[1][:3] == ("musketeer", 6, 26)


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


def test_unit_detector_keeps_ground_units_off_standing_towers():
    detector = unit_detector()
    probs = _probs(detector)
    # TOWER_TILES puts the left enemy princess on x 2-4, y 24-26: model
    # rows 5-7. An X-Bow seen in its sprite, and a baby dragon over it.
    probs[_channel(detector, Units.X_BOW, "enemy"), 6, 3] = 0.9
    probs[_channel(detector, Units.BABY_DRAGON, "enemy"), 5, 2] = 0.9
    # Our knight beside the tower, not on it.
    probs[_channel(detector, Units.KNIGHT, "ally"), 6, 5] = 0.9
    allies, enemies = detector.decode(probs)
    assert [d.unit.name for d in enemies] == ["baby_dragon"]
    assert [d.unit.name for d in allies] == ["knight"]
    # Once the tower falls, units can walk over its ruins.
    fallen = Towers(left_enemy_princess=Tower(hp=0))
    _, enemies = detector.decode(probs, towers=fallen)
    assert sorted(d.unit.name for d in enemies) == ["baby_dragon", "x_bow"]


def test_unit_detector_doesnt_rename_a_unit_on_a_tower():
    # A ground unit on our king tower isn't renamed as our baby dragon.
    detector = unit_detector()
    probs = _probs(detector)
    probs[_channel(detector, Units.GOLEM, "ally"), 29, 8] = 0.9
    probs[_channel(detector, Units.BABY_DRAGON, "ally"), 29, 8] = 0.1
    allies, _ = detector.decode(probs)
    assert allies == []


def test_unit_detector_keeps_ground_units_out_of_the_river():
    detector = unit_detector()
    probs = _probs(detector)
    # The river is rows 15 and 16 (model rows 16 and 15). A skeleton in
    # the water, one on the left bridge, a hog rider jumping it and a bat
    # flying over it.
    probs[_channel(detector, Units.SKELETON, "enemy"), 16, 8] = 0.9
    probs[_channel(detector, Units.SKELETON, "enemy"), 15, 3] = 0.9
    probs[_channel(detector, Units.HOG_RIDER, "enemy"), 15, 11] = 0.9
    probs[_channel(detector, Units.BAT, "enemy"), 16, 0] = 0.9
    _, enemies = detector.decode(probs)
    assert _found(enemies) == [
        ("bat", 0, 15, pytest.approx(0.9)),
        ("hog_rider", 11, 16, pytest.approx(0.9)),
        ("skeleton", 3, 16, pytest.approx(0.9)),
    ]
