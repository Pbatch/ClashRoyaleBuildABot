import math

from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.namespaces.units import Units


class SpellAction(Action):
    """
    Play the spell to hit as many enemy units as possible
    """

    RADIUS = None
    MIN_SCORE = 5
    UNIT_TO_SCORE = {Units.SKELETON: 1}

    def calculate_score(self, state):
        hit_score = 0
        max_distance = float("inf")
        for det in state.enemies:
            distance = math.hypot(
                self.tile_x - det.position.tile_x,
                self.tile_y - det.position.tile_y + 2,
            )
            if distance <= self.RADIUS - 1:
                hit_score += self.UNIT_TO_SCORE.get(det.unit, 2)
                max_distance = min(max_distance, -distance)

        return [
            1 if hit_score >= self.MIN_SCORE else 0,
            hit_score,
            max_distance,
        ]
