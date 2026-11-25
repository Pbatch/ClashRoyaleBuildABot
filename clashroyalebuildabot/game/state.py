from pydantic.dataclasses import dataclass

from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.screens import ScreenName
from clashroyalebuildabot.game.timer import Timer
from clashroyalebuildabot.game.towers import Towers
from clashroyalebuildabot.game.units import UnitDetection


@dataclass
class State:
    allies: list[UnitDetection]
    enemies: list[UnitDetection]
    # 0 to 10.
    elixir: int
    towers: Towers
    timer: Timer
    # Five cards: the next card, then the four in hand. None is an empty
    # slot.
    cards: list[Card | None]
    # Playable hand positions (0-3). Hand position i is cards[i + 1].
    ready: list[int]
    screen: ScreenName
