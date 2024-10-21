from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Screen:
    name: str
    ltrb: Optional[Tuple[float, float, float, float]]
    click_xy: Optional[Tuple[int, int]]


# coords are scaled to 720x1280
@dataclass(frozen=True)
class _ScreensNamespace:
    UNKNOWN: Screen = Screen("unknown", None, None)
    IN_GAME: Screen = Screen("in_game", (148, 1254, 163, 1274), None)
    LOBBY: Screen = Screen(
        "lobby",
        (424, 126, 506, 181),
        (360, 820),
    )
    END_OF_GAME: Screen = Screen(
        "end_of_game",
        (279, 1095, 440, 1154),
        (360, 1125),
    )


Screens = _ScreensNamespace()
