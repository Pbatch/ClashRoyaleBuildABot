from dataclasses import dataclass
from typing import List, Tuple

from clashroyalebuildabot.namespaces.cards import Card
from clashroyalebuildabot.namespaces.numbers import Numbers
from clashroyalebuildabot.namespaces.screens import Screen
from clashroyalebuildabot.namespaces.units import UnitDetection


@dataclass
class State:
    allies: List[UnitDetection]
    enemies: List[UnitDetection]
    numbers: Numbers
    cards: Tuple[Card, Card, Card, Card]
    ready: List[int]
    screen: Screen
