from dataclasses import dataclass
from typing import Optional, Tuple

CHEST_SIZE = 62
CHEST_X = 0
CHEST_Y = 590
OK_X = 143
OK_Y = 558
OK_WIDTH = 82
OK_HEIGHT = 30


@dataclass(frozen=True)
class Screen:
    name: str
    ltrb: Optional[Tuple[float, float, float, float]]
    click_xy: Optional[Tuple[int, int]]


@dataclass(frozen=True)
class _ScreensNamespace:
    IN_GAME: Screen = Screen("in_game", None, None)
    LOBBY: Screen = Screen(
        "lobby",
        (CHEST_X, CHEST_Y, CHEST_X + CHEST_SIZE, CHEST_Y + CHEST_SIZE),
        (220, 830),
    )
    END_OF_GAME: Screen = Screen(
        "end_of_game",
        (OK_X, OK_Y, OK_X + OK_WIDTH, OK_Y + OK_HEIGHT),
        (360, 1125),
    )


Screens = _ScreensNamespace()
