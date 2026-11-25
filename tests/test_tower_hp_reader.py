import math
import os
import threading

import numpy as np

from clashroyalebuildabot.detectors.background import LatestResult
from clashroyalebuildabot.detectors.tower_hp_reader import (
    RUBBLE_READINGS,
    TOWER_BOXES,
    TowerHPReader,
)
from clashroyalebuildabot.game.numbers import (
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


def read_in_background(reader, image):
    reader.run(image)
    reader.wait(5)
    return reader.latest()


def hps(towers: Towers) -> dict[str, float]:
    return {name: tower.hp for name, tower in towers.items()}


def test_reads_every_towers_hp():
    reader = TowerHPReader(interval=0)
    for _ in range(RUBBLE_READINGS):
        towers = read_in_background(reader, battle_frame())
    assert hps(towers) == BATTLE
    reader.close()


def test_levels_stay_unknown():
    reader = TowerHPReader(interval=0)
    towers = read_in_background(reader, battle_frame())
    assert all(t.level == UNKNOWN_LEVEL for _, t in towers.items())
    reader.close()


def test_unknown_until_first_reading():
    reader = TowerHPReader()
    assert all(math.isinf(hp) for hp in hps(reader.latest()).values())
    reader.close()


def test_rubble_counts_only_after_several_readings():
    # A missing bar might be a moment's glitch; rubble stays missing.
    reader = TowerHPReader(interval=0)
    for _ in range(RUBBLE_READINGS - 1):
        towers = read_in_background(reader, battle_frame())
        assert towers.left_ally_princess.hp == UNKNOWN_HP
    towers = read_in_background(reader, battle_frame())
    assert towers.left_ally_princess.hp == 0
    reader.close()


def test_destroyed_tower_stays_destroyed():
    reader = TowerHPReader(interval=0)
    for _ in range(RUBBLE_READINGS):
        read_in_background(reader, battle_frame())
    # A number seen over its rubble later (a spell, a damage number) doesn't
    # bring it back.
    image = battle_frame(left_ally_princess="tower_right_ally_princess")
    towers = read_in_background(reader, image)
    assert towers.left_ally_princess.hp == 0
    reader.close()


def test_covered_number_keeps_the_previous_reading():
    # "Not enough elixir" covers the number, but the bar's still there.
    reader = TowerHPReader(interval=0)
    read_in_background(reader, battle_frame())
    image = battle_frame(right_ally_princess="tower_covered_bar")
    for _ in range(RUBBLE_READINGS + 1):
        towers = read_in_background(reader, image)
    assert towers.right_ally_princess.hp == 1459
    reader.close()


def test_untouched_king_tower_never_reads_as_destroyed():
    reader = TowerHPReader(interval=0)
    for _ in range(RUBBLE_READINGS + 1):
        towers = read_in_background(reader, frame())
    assert towers.enemy_king.hp == UNKNOWN_HP
    assert towers.ally_king.hp == UNKNOWN_HP
    reader.close()


def test_king_tower_keeps_its_last_reading():
    reader = TowerHPReader(interval=0)
    read_in_background(reader, battle_frame())
    towers = read_in_background(reader, frame())
    assert towers.ally_king.hp == 3803
    reader.close()


def test_reset_forgets_readings():
    reader = TowerHPReader(interval=0)
    for _ in range(RUBBLE_READINGS):
        read_in_background(reader, battle_frame())
    reader.reset()
    assert all(math.isinf(hp) for hp in hps(reader.latest()).values())
    # And the rubble count starts again.
    towers = read_in_background(reader, battle_frame())
    assert towers.left_ally_princess.hp == UNKNOWN_HP
    reader.close()


def test_reset_discards_an_answer_still_in_flight():
    release = threading.Event()

    def slow(image, previous):
        release.wait(5)
        return "old"

    latest = LatestResult(slow, default="none", interval=0, max_age=None)
    latest.run(frame())
    latest.reset()
    release.set()
    latest.wait(5)
    assert latest.latest() == "none"
    latest.close()


def test_every_tower_has_a_box():
    assert set(TOWER_BOXES) == {name for name, _ in Towers().items()}
