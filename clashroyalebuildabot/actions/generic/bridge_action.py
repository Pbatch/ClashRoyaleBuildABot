from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.game.state import State

# The last row on our side, in front of each bridge. The bridge itself
# (y=15) is only playable once that enemy princess tower is destroyed.
LEFT_BRIDGE = (3, 14)
RIGHT_BRIDGE = (14, 14)


class BridgeAction(Action):
    """
    If you have 10 elixir,
    play this card at the bridge on the side of the weakest tower
    """

    def calculate_score(self, state: State) -> list[float]:
        tile = (self.tile_x, self.tile_y)
        if tile not in {LEFT_BRIDGE, RIGHT_BRIDGE}:
            return [0]

        if state.elixir != 10:
            return [0]

        left_hp = state.towers.left_enemy_princess.hp
        right_hp = state.towers.right_enemy_princess.hp
        if tile == LEFT_BRIDGE:
            return [1, left_hp > 0, left_hp <= right_hp]
        return [1, right_hp > 0, right_hp <= left_hp]
