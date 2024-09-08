from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action


class GiantAction(Action):
    CARD = Cards.GIANT

    def calculate_score(self, state):
        if state.numbers.elixir.number != 10:
            return [0]

        left_hp = state.numbers.left_enemy_princess_hp.number
        right_hp = state.numbers.right_enemy_princess_hp.number

        if (self.tile_x, self.tile_y) == (3, 15):
            return [1, left_hp > 0, left_hp <= right_hp]

        if (self.tile_x, self.tile_y) == (14, 15):
            return [1, right_hp > 0, right_hp <= left_hp]

        return [0]
