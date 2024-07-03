import math

from clashroyalebuildabot.actions.action import Action


class SpellAction(Action):
    RADIUS = None
    MIN_TO_HIT = None

    def calculate_score(self, state):
        hit_units = 0
        max_distance = float("inf")
        for v in state.enemies.values():
            for position in v["positions"]:
                distance = math.hypot(
                    self.tile_x - position.tile_x,
                    self.tile_y - position.tile_y + 2,
                )
                if distance <= self.RADIUS - 1:
                    hit_units += 1
                    max_distance = min(max_distance, -distance)

        return [
            1 if hit_units >= self.MIN_TO_HIT else 0,
            hit_units,
            max_distance,
        ]
