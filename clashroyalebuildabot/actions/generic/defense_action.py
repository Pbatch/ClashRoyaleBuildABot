from clashroyalebuildabot.actions.generic.action import Action


class DefenseAction(Action):
    """
    If there are enemies on our side,
    play the card in a defensive position
    """

    def calculate_score(self, state):
        if (self.tile_x, self.tile_y) not in {(8, 9), (9, 9)}:
            return [0]

        lhs = 0
        rhs = 0
        for det in state.enemies:
            if det.position.tile_y > 16:
                continue

            if det.position.tile_x >= 9:
                rhs += 1
            else:
                lhs += 1

        if lhs == rhs == 0:
            return [0]

        if lhs >= rhs and self.tile_x == 9:
            return [0]

        return [1]
