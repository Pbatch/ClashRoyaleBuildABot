import pytest

from clashroyalebuildabot.namespaces import Screens, State
from clashroyalebuildabot.namespaces.numbers import NumberDetection, Numbers
from clashroyalebuildabot.namespaces.units import (
    Position,
    UnitDetection,
    Units,
)

_BBOX = (0, 0, 0, 0)


def _number(value):
    return NumberDetection(_BBOX, value)


def make_unit(tile_x, tile_y, unit=Units.KNIGHT):
    return UnitDetection(unit, Position(_BBOX, 1.0, tile_x, tile_y))


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
    screen=Screens.IN_GAME,
):
    numbers = Numbers(
        left_enemy_princess_hp=_number(left_enemy_hp),
        right_enemy_princess_hp=_number(right_enemy_hp),
        left_ally_princess_hp=_number(left_ally_hp),
        right_ally_princess_hp=_number(right_ally_hp),
        elixir=_number(elixir),
    )
    return State(
        allies=list(allies),
        enemies=list(enemies),
        numbers=numbers,
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
