from dataclasses import dataclass
from typing import Any, List, Tuple

from clashroyalebuildabot.namespaces.cards import Card
from clashroyalebuildabot.namespaces.screens import Screen


@dataclass
class State:
    enemies: Any
    allies: Any
    numbers: Any
    cards: Tuple[Card, Card, Card, Card]
    ready: List[int]
    screen: Screen


@dataclass
class Position:
    bbox: Tuple[int, int, int, int]
    conf: float
    tile_x: int
    tile_y: int
