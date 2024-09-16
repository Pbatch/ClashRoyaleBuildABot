from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Screen:
    name: str
    ltrb: Optional[Tuple[float, float, float, float]]
    click_xy: Optional[Tuple[int, int]]


@dataclass(frozen=True)
class _ScreensNamespace:
    UNKNOWN: Screen = Screen("unknown", None, None)
    IN_GAME: Screen = Screen("in_game", (315, 5, 365, 15), None)
    IN_GAME_OVERTIME: Screen = Screen(
        "in_game_overtime", (315, 5, 365, 15), None
    )
    LOBBY: Screen = Screen(
        "lobby",
        (315, 48, 356, 89),
        (220, 830),
    )
    END_OF_GAME: Screen = Screen(
        "end_of_game",
        (143, 558, 225, 588),
        (360, 1125),
    )


Screens = _ScreensNamespace()
