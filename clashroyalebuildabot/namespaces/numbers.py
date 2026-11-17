from dataclasses import dataclass


@dataclass(frozen=True)
class NumberDetection:
    bbox: tuple[int, int, int, int]
    number: float


@dataclass(frozen=True)
class Numbers:
    left_enemy_princess_hp: NumberDetection
    right_enemy_princess_hp: NumberDetection
    left_ally_princess_hp: NumberDetection
    right_ally_princess_hp: NumberDetection
    elixir: NumberDetection
