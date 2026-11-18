from pydantic.dataclasses import dataclass

from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.numbers import Numbers
from clashroyalebuildabot.game.screens import ScreenName
from clashroyalebuildabot.game.units import UnitDetection


@dataclass
class State:
    allies: list[UnitDetection]
    enemies: list[UnitDetection]
    numbers: Numbers
    # Five cards: the next card, then the four in hand.
    cards: list[Card]
    # Playable hand positions (0-3). Hand position i is cards[i + 1].
    ready: list[int]
    screen: ScreenName
