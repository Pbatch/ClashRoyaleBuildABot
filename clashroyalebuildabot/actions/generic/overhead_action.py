import math

from clashroyalebuildabot.actions.generic.action import Action


class OverheadAction(Action):
    """
    Play the card directly on top of enemy units
    """

    def calculate_score(self, state):
        score = [0.5] if state.numbers.elixir.number == 10 else [0]
        for det in state.enemies:
            distance = math.hypot(
                det.position.tile_x - self.tile_x,
                det.position.tile_y - self.tile_y,
            )
            if distance < 1:
                score = [1, -distance]
        return score
