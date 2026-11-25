from enum import StrEnum, auto
from typing import ClassVar

from pydantic.dataclasses import dataclass


class ScreenName(StrEnum):
    IN_GAME = auto()
    LOBBY = auto()
    # The results screen, with Play Again and OK buttons.
    END_OF_GAME = auto()
    # The results screen with only an OK button, in the centre.
    BYPASS_END_OF_GAME = auto()
    # Anything else, such as searching for an opponent, loading or a popup.
    # The bot waits through it.
    UNKNOWN = auto()


@dataclass(frozen=True)
class Screen:
    name: ScreenName
    # Where to tap to leave the screen, in 720x1280 coordinates.
    click_xy: tuple[int, int] | None = None


class Screens:
    """Look up a screen's details from its name."""

    _ALL = (
        Screen(ScreenName.IN_GAME),
        # The Battle button.
        Screen(ScreenName.LOBBY, click_xy=(360, 1000)),
        # Play Again.
        Screen(ScreenName.END_OF_GAME, click_xy=(243, 1158)),
        # OK.
        Screen(ScreenName.BYPASS_END_OF_GAME, click_xy=(360, 1161)),
        Screen(ScreenName.UNKNOWN),
    )
    _BY_NAME: ClassVar[dict[ScreenName, Screen]] = {
        screen.name: screen for screen in _ALL
    }

    @classmethod
    def get(cls, name: ScreenName) -> Screen:
        return cls._BY_NAME[name]

    @classmethod
    def all(cls) -> tuple[Screen, ...]:
        return cls._ALL
