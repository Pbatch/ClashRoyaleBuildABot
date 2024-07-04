import math

from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.action import Action


class MusketeerAction(Action):
    CARD = Cards.MUSKETEER

    def calculate_score(self, state):
        for v in state.enemies.values():
            for position in v["positions"]:
                distance = math.hypot(
                    position.tile_x - self.tile_x,
                    position.tile_y - self.tile_y,
                )
                if 5 < distance < 6:
                    return [1]
                if distance < 5:
                    return [0]
        return [0]
