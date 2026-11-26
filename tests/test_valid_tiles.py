import pytest

from clashroyalebuildabot.bot.plays import ALLY_TOWER_TILES, placeable_tiles
from clashroyalebuildabot.constants.device_screen import (
    ALL_TILES,
    ALLY_TILES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
)

OPEN_ALLY_TILES = [t for t in ALLY_TILES if tuple(t) not in ALLY_TOWER_TILES]


def test_nothing_goes_under_our_towers(state_factory):
    # 3x3 under each princess tower, 4x4 under the king.
    assert len(ALLY_TOWER_TILES) == 9 + 9 + 16
    tiles = placeable_tiles(state_factory())
    for tile in [[7, 1], [10, 4], [2, 5], [4, 7], [13, 5], [15, 7]]:
        assert tile not in tiles
    # Just beside them is fine.
    for tile in [[6, 1], [11, 4], [1, 5], [5, 7], [3, 8], [9, 5]]:
        assert tile in tiles


def test_spells_can_still_target_our_towers():
    assert [3, 6] in ALL_TILES


def test_only_ally_tiles_while_both_towers_stand(state_factory):
    state = state_factory(left_enemy_hp=0.5, right_enemy_hp=0.5)
    assert placeable_tiles(state) == OPEN_ALLY_TILES


@pytest.mark.parametrize(
    ("left_hp", "right_hp", "extra"),
    [
        (0, 0.5, LEFT_PRINCESS_TILES),
        (0.5, 0, RIGHT_PRINCESS_TILES),
        (0, 0, LEFT_PRINCESS_TILES + RIGHT_PRINCESS_TILES),
    ],
)
def test_destroyed_towers_unlock_tiles(
    state_factory, left_hp, right_hp, extra
):
    state = state_factory(left_enemy_hp=left_hp, right_enemy_hp=right_hp)
    assert placeable_tiles(state) == OPEN_ALLY_TILES + extra


def test_does_not_mutate_ally_tiles(state_factory):
    """Regression: ALLY_TILES used to grow on every step after a tower fell."""
    original = [list(tile) for tile in ALLY_TILES]
    state = state_factory(left_enemy_hp=0, right_enemy_hp=0)

    for _ in range(5):
        placeable_tiles(state)

    assert original == ALLY_TILES
