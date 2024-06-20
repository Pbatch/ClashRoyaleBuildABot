from dataclasses import dataclass
from typing import Any, List, Tuple

from clashroyalebuildabot.namespaces.cards import Card
from clashroyalebuildabot.namespaces.screens import Screen


@dataclass
class State:
    units: Any
    numbers: Any
    cards: Tuple[Card, Card, Card, Card]
    ready: List[int]
    screen: Screen
