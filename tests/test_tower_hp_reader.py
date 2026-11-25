import math
import threading

import numpy as np

from clashroyalebuildabot.constants.screenshot import (
    KING_TOWER_BOXES,
    PRINCESS_TOWER_BOXES,
)
from clashroyalebuildabot.detectors.background import LatestResult
from clashroyalebuildabot.detectors.tower_hp_reader import (
    CROP_SCALE,
    TOWERS,
    KingReading,
    TowerHPReader,
    TowerReading,
)
from clashroyalebuildabot.detectors.vlm_client import VisionError
from clashroyalebuildabot.game.numbers import (
    UNKNOWN_HP,
    UNKNOWN_LEVEL,
    Towers,
)

ALL_BOXES = {**PRINCESS_TOWER_BOXES, **KING_TOWER_BOXES}
HPS = {
    "left_enemy_princess": 1918,
    "right_enemy_princess": 931,
    "left_ally_princess": 2432,
    "right_ally_princess": 2534,
    "enemy_king": 1302,
    "ally_king": 4392,
}
LEVELS = {
    "left_enemy_princess": 8,
    "right_enemy_princess": 8,
    "left_ally_princess": 9,
    "right_ally_princess": 9,
    "enemy_king": 8,
    "ally_king": 10,
}
SHADE = 40  # each tower's box is painted a different shade of grey


class FakeClient:
    """Answers for each tower, told apart by the shade of grey the test
    frame paints its box."""

    def __init__(self, hps=HPS, levels=LEVELS, fail=()):
        self.hps = dict(hps)
        self.levels = dict(levels)
        self.fail: set[str] = set(fail)
        self.crops = []

    def ask(self, image, prompt, schema):
        self.crops.append(image.shape[1::-1])
        name = TOWERS[image[0, 0, 0] // SHADE][0]
        expected = KingReading if "king" in name else TowerReading
        assert schema is expected
        if name in self.fail:
            raise VisionError("down")
        return schema(level=self.levels[name], hp=self.hps[name])


def frame():
    image = np.zeros((652, 368, 3), np.uint8)
    for i, (_, (left, top, right, bottom), _) in enumerate(TOWERS):
        image[top:bottom, left:right] = i * SHADE
    return image


def hps(towers):
    return {name: tower.hp for name, tower in towers.items()}


def levels(towers):
    return {name: tower.level for name, tower in towers.items()}


def read_in_background(reader):
    reader.run(frame())
    reader.wait(5)
    return reader.latest()


def test_reads_hp_and_level_from_enlarged_crops():
    client = FakeClient()
    reader = TowerHPReader(client)
    readings = reader.read(frame())
    assert hps(readings) == HPS
    assert levels(readings) == LEVELS
    expected = [
        ((r - left) * CROP_SCALE, (b - t) * CROP_SCALE)
        for left, t, r, b in ALL_BOXES.values()
    ]
    assert sorted(client.crops) == sorted(expected)
    reader.close()


def test_readings_are_named_towers():
    reader = TowerHPReader(FakeClient())
    towers = reader.read(frame())
    assert isinstance(towers, Towers)
    assert towers.right_enemy_princess.hp == 931
    assert towers.right_ally_princess.level == 9
    assert towers.enemy_king.hp == 1302
    assert towers.ally_king.level == 10
    reader.close()


def test_unknown_until_first_reading():
    reader = TowerHPReader(FakeClient())
    readings = reader.latest()
    assert all(math.isinf(n) for n in hps(readings).values())
    assert all(n == UNKNOWN_LEVEL for n in levels(readings).values())
    reader.close()


def test_destroyed_tower_keeps_its_last_level():
    client = FakeClient()
    reader = TowerHPReader(client, interval=0)
    read_in_background(reader)

    # Rubble has no badge; the model answers level 1 there in practice.
    client.hps["left_ally_princess"] = 0
    client.levels["left_ally_princess"] = 1
    readings = read_in_background(reader)

    assert readings.left_ally_princess.hp == 0
    assert readings.left_ally_princess.level == 9
    reader.close()


def test_untouched_king_tower_counts_as_standing_with_its_level():
    client = FakeClient()
    client.hps["enemy_king"] = 0  # only the badge is showing
    readings = TowerHPReader(client).read(frame())
    assert readings.enemy_king.hp == UNKNOWN_HP
    assert readings.enemy_king.level == 8


def test_untouched_king_tower_never_reads_as_destroyed():
    client = FakeClient()
    client.hps["ally_king"] = 0
    towers = TowerHPReader(client).read(frame())
    assert towers.ally_king.hp > 0


def test_failed_tower_keeps_its_previous_reading():
    client = FakeClient()
    reader = TowerHPReader(client, interval=0)
    read_in_background(reader)

    client.fail = {"right_enemy_princess"}
    client.hps["left_enemy_princess"] = 1582
    readings = read_in_background(reader)

    assert readings.left_enemy_princess.hp == 1582
    assert readings.right_enemy_princess.hp == 931
    assert readings.right_enemy_princess.level == 8
    reader.close()


def test_failed_first_reading_stays_unknown():
    reader = TowerHPReader(FakeClient(fail=set(HPS)))
    readings = reader.read(frame())
    assert all(n == UNKNOWN_HP for n in hps(readings).values())
    assert all(n == UNKNOWN_LEVEL for n in levels(readings).values())
    reader.close()


def test_reset_forgets_readings():
    reader = TowerHPReader(FakeClient(), interval=0)
    assert hps(read_in_background(reader)) == HPS
    reader.reset()
    assert all(math.isinf(n) for n in hps(reader.latest()).values())
    reader.close()


def test_reset_discards_an_answer_still_in_flight():
    release = threading.Event()

    def slow(image):
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
    assert set(ALL_BOXES) == {name for name, _ in Towers().items()}
