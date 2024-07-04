from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.action import Action


class GiantAction(Action):
    CARD = Cards.GIANT

    def calculate_score(self, state):
        score = [0]
        left_hp, right_hp = (
            state.numbers[f"{direction}_enemy_princess_hp"]["number"]
            for direction in ["left", "right"]
        )
        if state.numbers["elixir"]["number"] == 10:
            if self.tile_x == 3:
                score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
            elif self.tile_x == 14:
                score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
        return score
