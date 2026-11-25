"""Turning a frame into the game's State.

A detector works out *what* is on screen, from a fixed set of
possibilities: the cards in hand, the units on the tiles, the screen
itself. A reader reads a *value* the game draws: elixir, tower HP, the
timer. The StateReader runs them all and puts the State together.
"""

from .card_detector import CardDetector
from .elixir_reader import ElixirReader
from .screen_detector import ScreenDetector
from .state_reader import StateReader
from .timer_reader import TimerReader
from .tower_hp_reader import TowerHPReader
from .unit_detector import UnitDetector

__all__ = [
    "CardDetector",
    "ElixirReader",
    "ScreenDetector",
    "StateReader",
    "TimerReader",
    "TowerHPReader",
    "UnitDetector",
]
