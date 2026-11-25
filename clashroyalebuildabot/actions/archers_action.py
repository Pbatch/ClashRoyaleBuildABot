from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.state import State


class ArchersAction(Action):
    CARD = Cards.ARCHERS

    def calculate_score(self, state: State) -> list[float]:
        score: list[float] = [0.5] if state.numbers.elixir == 10 else [0]

        for det in state.enemies:
            lhs = det.position.tile_x <= 8 and self.tile_x == 7
            rhs = det.position.tile_x > 8 and self.tile_x == 10
            if self.tile_y < det.position.tile_y <= 14 and (lhs or rhs):
                score = [1, self.tile_y - det.position.tile_y]
        return score
