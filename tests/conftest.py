import os

import pytest

from clashroyalebuildabot.config import Config, load_config
from clashroyalebuildabot.game import ScreenName, State
from clashroyalebuildabot.game.timer import Timer
from clashroyalebuildabot.game.towers import Tower, Towers
from clashroyalebuildabot.game.units import (
    Position,
    UnitDetection,
    Units,
)


def make_unit(tile_x, tile_y, unit=Units.KNIGHT):
    return UnitDetection(unit, Position(1.0, tile_x, tile_y))


def make_state(
    *,
    allies=(),
    enemies=(),
    elixir=5,
    left_enemy_hp=1.0,
    right_enemy_hp=1.0,
    left_ally_hp=1.0,
    right_ally_hp=1.0,
    cards=(),
    ready=(),
    screen=ScreenName.IN_GAME,
):
    towers = Towers(
        left_enemy_princess=Tower(hp=left_enemy_hp),
        right_enemy_princess=Tower(hp=right_enemy_hp),
        left_ally_princess=Tower(hp=left_ally_hp),
        right_ally_princess=Tower(hp=right_ally_hp),
    )
    return State(
        allies=list(allies),
        enemies=list(enemies),
        elixir=elixir,
        towers=towers,
        timer=Timer(),
        cards=list(cards),
        ready=list(ready),
        screen=screen,
    )


@pytest.fixture
def state_factory():
    return make_state


@pytest.fixture
def unit_factory():
    return make_unit


def default_config() -> Config:
    """The shipped default settings, ignoring any local config.yaml."""
    return load_config(user_config_path=os.devnull + ".missing")
