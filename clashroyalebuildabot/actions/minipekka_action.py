from clashroyalebuildabot import Cards
from clashroyalebuildabot.actions.action import Action


class MinipekkaAction(Action):
    CARD = Cards.MINIPEKKA

    def calculate_score(self, state):
        left_hp, right_hp = (
            state.numbers[f"{direction}_enemy_princess_hp"]["number"]
            for direction in ["left", "right"]
        )
        if self.tile_x in [3, 14]:
            return (
                [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
                if self.tile_x == 3
                else [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
            )
        return [0]
