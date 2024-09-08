import math

from clashroyalebuildabot.actions.generic.action import Action


class KingAction(Action):
    """
    Play the card behind the king, on the side of the closest enemy
    """

    def calculate_score(self, state):
        if (self.tile_x, self.tile_y) not in {(8, 0), (9, 0)}:
            return [0]

        min_distance = float("inf")
        for det in state.enemies:
            distance = math.hypot(
                det.position.tile_x - self.tile_x,
                det.position.tile_y - self.tile_y,
            )
            min_distance = min(min_distance, distance)

        return [0.5, -min_distance]
