"""The six towers' health and level, read from the screen each step.

Where each tower is on the screen is fixed, so it lives in
constants/screenshot.py (``PRINCESS_TOWER_BOXES`` and ``KING_TOWER_BOXES``),
not here.
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
