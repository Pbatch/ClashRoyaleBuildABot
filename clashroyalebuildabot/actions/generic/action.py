from abc import ABC
from abc import abstractmethod

from clashroyalebuildabot.namespaces.cards import Card


class Action(ABC):
    CARD: Card = None

    def __init__(self, index, tile_x, tile_y):
        self.index = index
        self.tile_x = tile_x
        self.tile_y = tile_y

    def __repr__(self):
        return f"{self.CARD.name} at ({self.tile_x}, {self.tile_y})"

    @abstractmethod
    def calculate_score(self, state):
        pass
