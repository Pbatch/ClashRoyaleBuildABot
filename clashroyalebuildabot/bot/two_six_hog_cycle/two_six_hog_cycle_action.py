from clashroyalebuildabot.bot.bot import Action
from clashroyalebuildabot.namespaces.cards import Cards


class TwoSixHogCycleAction(Action):
    score = 0

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _calculate_hog_rider_score(self, state):
        """
        If there are no enemy troops on our side of the arena and
        the player has 7 elixir or more
        Place hog rider on the bridge as high up as possible
        Try to target the lowest hp tower
        """
        for v in state.units["enemy"].values():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                if self.tile_y < tile_y <= 14:
                    if (
                        tile_x > 8
                        and self.tile_x == 10
                        or tile_x <= 8
                        and self.tile_x == 7
                    ):
                        return [0]

        if state.numbers["elixir"]["number"] >= 7:
            left_hp, right_hp = [
                state.numbers[f"{direction}_enemy_princess_hp"]["number"]
                for direction in ["left", "right"]
            ]
            if self.tile_x == 3:
                return [1, self.tile_y, left_hp != -1, left_hp <= right_hp]

            if self.tile_x == 14:
                return [1, self.tile_y, right_hp != -1, right_hp <= left_hp]

        return [0]

    def _calculate_cannon_score(self, state):
        """
        If there are ground troops place the cannon in the middle of the arena
        """
        if self.tile_x != 9 or self.tile_y != 10:
            return [0]

        for side in ["ally", "enemy"]:
            for v in state.units[side].values():
                for unit in v["positions"]:
                    tile_y = unit["tile_xy"][1]
                    if v["transport"] == "ground" and tile_y >= 10:
                        return [2]

        return [0]

    def _calculate_musketeer_score(self, state):
        """
        If there are flying troops
        Place musketeer at 7 tiles in front of the enemies
        That should be just within her range and not too close to the enemy
        """
        for side in ["ally", "enemy"]:
            for v in state.units[side].values():
                for unit in v["positions"]:
                    tile_y = unit["tile_xy"][1]
                    if v["transport"] == "air" and self.tile_y == tile_y - 7:
                        return [2]

        return [0]

    def _calculate_ice_golem_score(self, state):
        """
        If there is a ground troop on the bridge place the ice golem in the middle of the
        arena one tile away from the enemy
        """
        if self.tile_y != 4:
            return [0]

        for side in ["ally", "enemy"]:
            for v in state.units[side].values():
                for unit in v["positions"]:
                    tile_x, tile_y = unit["tile_xy"]
                    if not (18 >= tile_y >= 15) or v["transport"] != "ground":
                        continue

                    lhs = tile_x <= 8 and self.tile_x == 9
                    rhs = tile_x > 8 and self.tile_x == 8
                    if lhs or rhs:
                        return [2]

        return [0]

    def _calculate_ice_spirit_score(self, state):
        """
        Place the ice spirit in the middle of the arena when a ground troop is on the bridge
        """
        if self.tile_y != 10:
            return [0]

        for side in ["ally", "enemy"]:
            for v in state.units[side].values():
                for unit in v["positions"]:
                    tile_x, tile_y = unit["tile_xy"]
                    if not (18 >= tile_y >= 15) or v["transport"] != "ground":
                        continue

                    if (tile_x <= 8 and self.tile_x == 8) or (
                        tile_x > 8 and self.tile_x == 9
                    ):
                        return [2]

        return [0]

    def _calculate_spell_score(self, units, radius, min_to_hit):
        """
        Calculate the score for a spell card (either fireball or arrows)

        The score is defined as [A, B, C]
            A is 1 if we'll hit `min_to_hit` or more units, 0 otherwise
            B is the number of units we hit
            C is the negative distance to the furthest unit
        """
        score = [0, 0, 0]
        for v in units["enemy"].values():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                # Assume the unit will move down a few spaces
                tile_y -= 2

                # Add 1 to the score if the spell will hit the unit
                distance = self._distance(
                    tile_x, tile_y, self.tile_x, self.tile_y
                )
                if distance <= radius - 1:
                    score[1] += 1
                    score[2] = min(score[2], -distance)

        # Set score[0] to 1 if we think we'll hit enough units
        if score[1] >= min_to_hit:
            score[0] = 1

        return score

    def _calculate_log_score(self, state):
        """
        Calculate the score for the log card
        """
        score = [0]
        for v in state.units["enemy"].values():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                if tile_y <= 8 and v["transport"] == "ground":
                    if self.tile_y == tile_y - 4 and self.tile_x == tile_x:
                        score = [1]

        return score

    def _calculate_fireball_score(self, state):
        """
        Play the fireball card if it will hit flying units
        """
        for v in state.units["enemy"].values():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                if (
                    v["transport"] == "air"
                    and self.tile_y == tile_y - 4
                    and self.tile_x == tile_x
                ):
                    return [1]

        return self._calculate_spell_score(
            state.units, radius=2.5, min_to_hit=3
        )

    def calculate_score(self, state):
        card_to_score = {
            Cards.HOG_RIDER: self._calculate_hog_rider_score,
            Cards.ICE_GOLEM: self._calculate_ice_golem_score,
            Cards.FIREBALL: self._calculate_fireball_score,
            Cards.ICE_SPIRIT: self._calculate_ice_spirit_score,
            Cards.THE_LOG: self._calculate_log_score,
            Cards.MUSKETEER: self._calculate_musketeer_score,
            Cards.CANNON: self._calculate_cannon_score,
            Cards.SKELETONS: self._calculate_ice_spirit_score,
        }

        score_function = card_to_score[self.card]
        score = score_function(state)
        self.score = score
        return score
