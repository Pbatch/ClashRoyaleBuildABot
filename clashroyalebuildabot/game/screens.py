from enum import StrEnum, auto

from pydantic.dataclasses import dataclass


class ScreenName(StrEnum):
    IN_GAME = auto()
    LOBBY = auto()
    END_OF_GAME = auto()
    # END_OF_GAME with the OK button in the centre.
    BYPASS_END_OF_GAME = auto()
    # Screens between the lobby, the battle and the results. The bot only
    # waits through them. The vision model reads the value, and does better
    # with "searching_for_opponent" than "matchmaking".
    SEARCHING_FOR_OPPONENT = auto()
    LOADING = auto()
    VS = auto()
    MATCH_OVER = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Screen:
    name: ScreenName
    # Where to tap to leave the screen, in 720x1280 coordinates.
    click_xy: tuple[int, int] | None = None
    # How the screen is described to the screen detector's vision model.
    # Screens without one aren't offered to the model.
    description: str | None = None


class Screens:
    """Look up a screen's details from its name."""

    # The order here is the order the screens are listed in the model's
    # prompt, so UNKNOWN, the catch-all, comes last.
    _ALL = (
        Screen(
            ScreenName.IN_GAME,
            description="a battle in progress: the arena with towers, and a "
            "hand of cards with an elixir bar at the bottom, sometimes with "
            "a FIGHT! or Battle ends in banner",
        ),
        Screen(
            ScreenName.LOBBY,
            click_xy=(360, 1000),
            description="the main menu, with a large yellow Battle button "
            "and navigation tabs at the bottom",
        ),
        Screen(
            ScreenName.END_OF_GAME,
            click_xy=(243, 1158),
            description="the battle results screen, with crowns or a winner "
            "banner and a blue OK button",
        ),
        # Not offered to the model: the screen detector picks it from where
        # the OK button is.
        Screen(ScreenName.BYPASS_END_OF_GAME, click_xy=(360, 1161)),
        Screen(
            ScreenName.SEARCHING_FOR_OPPONENT,
            description="searching for an opponent: a Searching for "
            "opponent banner and a red Cancel button",
        ),
        Screen(
            ScreenName.LOADING,
            description="a loading screen: the Clash Royale logo over game "
            "artwork, with a loading progress bar at the bottom",
        ),
        Screen(
            ScreenName.VS,
            description="the versus screen before a battle: both players' "
            "names and trophies, with a VS badge between them",
        ),
        Screen(
            ScreenName.MATCH_OVER,
            description="the words Match Over! written in large letters "
            "across the middle of the screen",
        ),
        Screen(
            ScreenName.UNKNOWN,
            description="anything else, such as a popup, shop or chest "
            "opening",
        ),
    )
    _BY_NAME = {screen.name: screen for screen in _ALL}

    @classmethod
    def get(cls, name: ScreenName) -> Screen:
        return cls._BY_NAME[name]

    @classmethod
    def all(cls) -> tuple[Screen, ...]:
        return cls._ALL
