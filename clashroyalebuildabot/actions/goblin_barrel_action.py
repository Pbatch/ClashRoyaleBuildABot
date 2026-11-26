from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.state import State


class GoblinBarrelAction(Action):
    CARD = Cards.GOBLIN_BARREL

    def calculate_score(self, state: State) -> list[float]:
        left_hp = state.towers.left_enemy_princess.hp
        right_hp = state.towers.right_enemy_princess.hp

        if (self.tile_x, self.tile_y) == (3, 25) and left_hp > 0:
            return [1, left_hp <= right_hp]

        if (self.tile_x, self.tile_y) == (14, 25) and right_hp > 0:
            return [1, right_hp <= left_hp]

        if (self.tile_x, self.tile_y) in {(8, 27), (9, 27), (8, 28), (9, 28)}:
            return [0.5]

        return [0]
