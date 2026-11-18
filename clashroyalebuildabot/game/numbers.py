"""The numbers read from the screen each step: elixir, towers and timer.

These are plain values. Where each one is on the screen is fixed, so it
lives in constants/screenshot.py (``ELIXIR_BOX``, ``PRINCESS_TOWER_BOXES``,
``KING_TOWER_BOXES`` and ``TIMER_BOX``), not here.
"""

import math
from collections.abc import Iterator
from dataclasses import field, fields

from pydantic.dataclasses import dataclass

# A tower that hasn't been read yet, or an untouched king tower, which shows
# no health bar: counts as standing, and both towers on a side compare as
# equal.
UNKNOWN_HP = math.inf
UNKNOWN_LEVEL = 0
UNKNOWN_TIME = math.inf


@dataclass(frozen=True)
class Tower:
    # 0 once destroyed. UNKNOWN_HP until read, and for a king tower until
    # it's first hit.
    hp: float = UNKNOWN_HP
    # From the badge beside the health bar. UNKNOWN_LEVEL until read.
    level: int = UNKNOWN_LEVEL


@dataclass(frozen=True)
class Towers:
    left_enemy_princess: Tower = field(default_factory=Tower)
    right_enemy_princess: Tower = field(default_factory=Tower)
    left_ally_princess: Tower = field(default_factory=Tower)
    right_ally_princess: Tower = field(default_factory=Tower)
    enemy_king: Tower = field(default_factory=Tower)
    ally_king: Tower = field(default_factory=Tower)

    def items(self) -> Iterator[tuple[str, Tower]]:
        """Each tower with its name, in the order above."""
        for f in fields(self):
            yield f.name, getattr(self, f.name)


@dataclass(frozen=True)
class Timer:
    # Seconds left. In overtime, it counts down the overtime left.
    # UNKNOWN_TIME until read.
    time_left: float = UNKNOWN_TIME
    overtime: bool = False


@dataclass(frozen=True)
class Numbers:
    elixir: int = 0
    towers: Towers = field(default_factory=Towers)
    timer: Timer = field(default_factory=Timer)
