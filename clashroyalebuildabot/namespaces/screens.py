from dataclasses import dataclass


@dataclass(frozen=True)
class Screen:
    name: str
    # Where to tap to leave the screen, in 720x1280 coordinates.
    click_xy: tuple[int, int] | None


@dataclass(frozen=True)
class _ScreensNamespace:
    UNKNOWN: Screen = Screen("unknown", None)
    IN_GAME: Screen = Screen("in_game", None)
    LOBBY: Screen = Screen("lobby", (360, 1000))
    END_OF_GAME: Screen = Screen("end_of_game", (243, 1158))
    BYPASS_END_OF_GAME: Screen = Screen("bypass_end_of_game", (360, 1161))


Screens = _ScreensNamespace()
