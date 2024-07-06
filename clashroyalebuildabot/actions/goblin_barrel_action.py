from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.action import Action


class GoblinBarrelAction(Action):
    CARD = Cards.GOBLIN_BARREL

    def calculate_score(self, state):
        left_hp, right_hp = (
            state.numbers[f"{direction}_enemy_princess_hp"]["number"]
            for direction in ["left", "right"]
        )
        if (self.tile_x, self.tile_y) == (14, 25) and right_hp <= left_hp:
            score = [1]
        elif (self.tile_x, self.tile_y) == (3, 25) and left_hp <= right_hp:
            score = [1]
        else:
            score = [0]

        return score
