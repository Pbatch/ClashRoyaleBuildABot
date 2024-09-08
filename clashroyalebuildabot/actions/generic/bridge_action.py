from clashroyalebuildabot.actions.generic.action import Action


class BridgeAction(Action):
    """
    If you have 10 elixir,
    play this card at the bridge on the side of the weakest tower
    """

    def calculate_score(self, state):
        if (self.tile_x, self.tile_y) not in {(3, 15), (14, 15)}:
            return [0]

        if state.numbers.elixir.number != 10:
            return [0]

        left_hp = state.numbers.left_enemy_princess_hp.number
        right_hp = state.numbers.right_enemy_princess_hp.number
        if self.tile_x == 3:
            score = [1, left_hp > 0, left_hp <= right_hp]
        else:
            # self.tile_x == 14
            score = [1, right_hp > 0, right_hp <= left_hp]

        return score
