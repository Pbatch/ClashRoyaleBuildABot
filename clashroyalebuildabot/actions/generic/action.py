from abc import ABC, abstractmethod

from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.game.state import State


class Action(ABC):
    CARD: Card

    def __init__(self, index: int, tile_x: int, tile_y: int) -> None:
        self.index = index
        self.tile_x = tile_x
        self.tile_y = tile_y

    def __repr__(self) -> str:
        return f"{self.CARD.name} at ({self.tile_x}, {self.tile_y})"

    @abstractmethod
    def calculate_score(self, state: State) -> list[float]:

        pass
