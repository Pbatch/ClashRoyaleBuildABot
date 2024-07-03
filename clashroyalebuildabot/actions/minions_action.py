import math

from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.action import Action


class MinionsAction(Action):
    CARD = Cards.MINIONS

    def calculate_score(self, state):
        score = [0.5] if state.numbers["elixir"]["number"] == 10 else [0]
        for v in state.enemies.values():
            for position in v["positions"]:
                distance = math.hypot(
                    position.tile_x - self.tile_x,
                    position.tile_y - self.tile_y,
                )
                if distance < 1:
                    score = [1, -distance]
        return score
