from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class NumberDetection:
    bbox: Tuple[int, int, int, int]
    confidence: List[float]
    number: int


@dataclass(frozen=True)
class Numbers:
    enemy_king_level: NumberDetection
    enemy_king_hp: NumberDetection
    left_enemy_princess_hp: NumberDetection
    right_enemy_princess_hp: NumberDetection
    ally_king_level: NumberDetection
    ally_king_hp: NumberDetection
    left_ally_princess_hp: NumberDetection
    right_ally_princess_hp: NumberDetection
    elixir: NumberDetection
