import math
import os

import numpy as np

from clashroyalebuildabot.detectors.tower_hp_reader import (
    RUBBLE_SECONDS,
    TOWER_BOXES,
    TowerHPReader,
)
from clashroyalebuildabot.game.towers import (
    UNKNOWN_HP,
    UNKNOWN_LEVEL,
    Towers,
)
from clashroyalebuildabot.utils.image import load

DATA = os.path.join(os.path.dirname(__file__), "data", "numbers")
# Real crops of each tower from one battle frame, and what they show.
BATTLE = {
    "left_enemy_princess": 2030,
    "right_enemy_princess": 1145,
    "left_ally_princess": 0,  # rubble
    "right_ally_princess": 1459,
    "enemy_king": UNKNOWN_HP,  # untouched: only its badge
    "ally_king": 3803,
}


def frame(**crops: str) -> np.ndarray:
    """A black frame, with real crops pasted into towers' boxes. Each
    keyword names a tower, its value the crop to paste there."""
    image = np.zeros((652, 368, 3), np.uint8)
    for tower, name in crops.items():
        left, top, right, bottom = TOWER_BOXES[tower]
        crop = load(os.path.join(DATA, f"{name}.png"))
        image[top:bottom, left:right] = crop
    return image


def battle_frame(**overrides: str) -> np.ndarray:
    crops = {name: f"tower_{name}" for name in TOWER_BOXES}
    return frame(**{**crops, **overrides})


class Clock:
    """A clock the test moves on by hand."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def reader_and_clock():
    clock = Clock()
    return TowerHPReader(clock=clock), clock


def hps(towers: Towers) -> dict[str, float]:
    return {name: tower.hp for name, tower in towers.items()}


def test_reads_every_towers_hp():
    reader, clock = reader_and_clock()
    reader.run(battle_frame())
    clock.now = RUBBLE_SECONDS  # long enough for the rubble to count
    assert hps(reader.run(battle_frame())) == BATTLE


def test_levels_stay_unknown():
    reader, _ = reader_and_clock()
    towers = reader.run(battle_frame())
    assert all(t.level == UNKNOWN_LEVEL for _, t in towers.items())


def test_unknown_until_first_reading():
    reader, _ = reader_and_clock()
    assert all(math.isinf(hp) for hp in hps(reader.latest()).values())


def test_rubble_counts_only_after_a_while():
    # A missing bar might be a pop-up passing over; rubble stays missing.
    reader, clock = reader_and_clock()
    for t in np.arange(0, RUBBLE_SECONDS, 0.1):
        clock.now = t
        towers = reader.run(battle_frame())
        assert towers.left_ally_princess.hp == UNKNOWN_HP
    clock.now = RUBBLE_SECONDS
    assert reader.run(battle_frame()).left_ally_princess.hp == 0


def test_many_frames_dont_make_rubble_sooner():
    # However fast frames come, rubble takes RUBBLE_SECONDS.
    reader, clock = reader_and_clock()
    clock.now = 10.0
    for _ in range(100):
        towers = reader.run(battle_frame())
    assert towers.left_ally_princess.hp == UNKNOWN_HP


def test_a_bar_seen_again_restarts_the_wait():
    reader, clock = reader_and_clock()
    reader.run(battle_frame())  # rubble from t = 0
    clock.now = RUBBLE_SECONDS - 0.1
    # Its number shows again, for a moment.
    reader.run(battle_frame(left_ally_princess="tower_right_ally_princess"))
    clock.now = RUBBLE_SECONDS
    reader.run(battle_frame())  # gone again, but only just
    assert reader.latest().left_ally_princess.hp == 1459
    clock.now = 2 * RUBBLE_SECONDS
    assert reader.run(battle_frame()).left_ally_princess.hp == 0


def test_destroyed_tower_stays_destroyed():
    reader, clock = reader_and_clock()
    reader.run(battle_frame())
    clock.now = RUBBLE_SECONDS
    reader.run(battle_frame())
    # A number seen over its rubble later (a spell, a damage number) doesn't
    # bring it back.
    image = battle_frame(left_ally_princess="tower_right_ally_princess")
    assert reader.run(image).left_ally_princess.hp == 0


def test_covered_number_keeps_the_previous_reading():
    # "Not enough elixir" covers the number, but the bar's still there.
    reader, clock = reader_and_clock()
    reader.run(battle_frame())
    image = battle_frame(right_ally_princess="tower_covered_bar")
    for t in range(1, 5):
        clock.now = float(t)
        towers = reader.run(image)
    assert towers.right_ally_princess.hp == 1459


def test_untouched_king_tower_never_reads_as_destroyed():
    reader, clock = reader_and_clock()
    for t in range(5):
        clock.now = float(t)
        towers = reader.run(frame())
    assert towers.enemy_king.hp == UNKNOWN_HP
    assert towers.ally_king.hp == UNKNOWN_HP


def test_king_tower_keeps_its_last_reading():
    reader, _ = reader_and_clock()
    reader.run(battle_frame())
    assert reader.run(frame()).ally_king.hp == 3803


def test_reset_forgets_readings():
    reader, clock = reader_and_clock()
    reader.run(battle_frame())
    clock.now = RUBBLE_SECONDS
    reader.run(battle_frame())
    reader.reset()
    assert all(math.isinf(hp) for hp in hps(reader.latest()).values())
    # And the wait for rubble starts again.
    assert reader.run(battle_frame()).left_ally_princess.hp == UNKNOWN_HP


def test_every_tower_has_a_box():
    assert set(TOWER_BOXES) == {name for name, _ in Towers().items()}
