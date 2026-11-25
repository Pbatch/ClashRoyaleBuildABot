import pytest

from clashroyalebuildabot.bot.bot import Bot
from clashroyalebuildabot.constants.device_screen import (
    ALLY_TILES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
)


def test_only_ally_tiles_while_both_towers_stand(state_factory):
    state = state_factory(left_enemy_hp=0.5, right_enemy_hp=0.5)
    assert Bot._get_valid_tiles(state) == ALLY_TILES


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
    assert Bot._get_valid_tiles(state) == ALLY_TILES + extra


def test_does_not_mutate_ally_tiles(state_factory):
    """Regression: ALLY_TILES used to grow on every step after a tower fell."""
    original = [list(tile) for tile in ALLY_TILES]
    state = state_factory(left_enemy_hp=0, right_enemy_hp=0)

    for _ in range(5):
        Bot._get_valid_tiles(state)

    assert original == ALLY_TILES
