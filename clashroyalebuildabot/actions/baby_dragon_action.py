import math

from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action


class BabyDragonAction(Action):
    CARD = Cards.BABY_DRAGON

    def calculate_score(self, state):
        for det in state.enemies:
            distance = math.hypot(
                det.position.tile_x - self.tile_x,
                det.position.tile_y - self.tile_y,
            )
            if 5 < distance < 6:
                return [1]
            if distance < 5:
                return [0]
        return [0]
