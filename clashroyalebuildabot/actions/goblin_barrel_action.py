from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.generic.action import Action


class GoblinBarrelAction(Action):
    CARD = Cards.GOBLIN_BARREL

    def calculate_score(self, state):
        left_hp = state.numbers.left_enemy_princess_hp.number
        right_hp = state.numbers.right_enemy_princess_hp.number

        if (self.tile_x, self.tile_y) == (3, 25) and left_hp > 0:
            return [1, left_hp <= right_hp]

        if (self.tile_x, self.tile_y) == (14, 25) and right_hp > 0:
            return [1, right_hp <= left_hp]

        if (self.tile_x, self.tile_y) in {(8, 27), (9, 27), (8, 28), (9, 28)}:
            return [0.5]

        return [0]
