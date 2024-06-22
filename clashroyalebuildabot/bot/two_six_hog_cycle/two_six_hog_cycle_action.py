import math

from clashroyalebuildabot.bot.bot import Action
from clashroyalebuildabot.namespaces.cards import Cards
from clashroyalebuildabot.namespaces.units import Transport


class TwoSixHogCycleAction(Action):
    score = 0

    def _calculate_hog_rider_score(self, state):
        """
        If there are no enemy troops on our side of the arena and
        the player has 7 elixir or more
        Place hog rider on the bridge as high up as possible
        Try to target the lowest hp tower
        """
        for v in state.enemies.values():
            for position in v["positions"]:
                if not self.tile_y < position.tile_y <= 14:
                    continue
                if (position.tile_x > 8 and self.tile_x == 10) or (
                    position.tile_x <= 8 and self.tile_x == 7
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
        if (self.tile_x, self.tile_y) != (9, 10):
            return [0]

        for v in state.enemies.values():
            for position in v["positions"]:
                if (
                    v["transport"] == Transport.GROUND
                    and position.tile_y >= 10
                ):
                    return [2]

        return [0]

    def _calculate_musketeer_score(self, state):
        """
        If there are flying troops
        Place musketeer at 7 tiles in front of the enemies
        That should be just within her range and not too close to the enemy
        """
        for v in state.enemies.values():
            for position in v["positions"]:
                if (
                    v["transport"] == Transport.AIR
                    and self.tile_y == position.tile_y - 7
                ):
                    return [2]

        return [0]

    def _calculate_ice_golem_score(self, state):
        """
        If there is a ground troop on the bridge place the ice golem in the middle of the
        arena one tile away from the enemy
        """
        if self.tile_y != 4:
            return [0]

        for v in state.enemies.values():
            for position in v["positions"]:
                if (
                    not (15 <= position.tile_y <= 18)
                    or v["transport"] != Transport.GROUND
                ):
                    continue

                lhs = position.tile_x <= 8 and self.tile_x == 9
                rhs = position.tile_x > 8 and self.tile_x == 8
                if lhs or rhs:
                    return [2]

        return [0]

    def _calculate_ice_spirit_score(self, state):
        """
        Place the ice spirit in the middle of the arena when a ground troop is on the bridge
        """
        if self.tile_y != 10:
            return [0]

        for v in state.enemies.values():
            for position in v["positions"]:
                if (
                    not (15 <= position.tile_y <= 18)
                    or v["transport"] != Transport.GROUND
                ):
                    continue

                lhs = position.tile_x <= 8 and self.tile_x == 9
                rhs = position.tile_x > 8 and self.tile_x == 8
                if lhs or rhs:
                    return [2]

        return [0]

    def _calculate_spell_score(self, state, radius, min_to_hit):
        """
        Calculate the score for a spell card (either fireball or arrows)

        The score is defined as [A, B, C]
            A is 1 if we'll hit `min_to_hit` or more units, 0 otherwise
            B is the number of units we hit
            C is the negative distance to the furthest unit
        """
        score = [0, 0, 0]
        for v in state.enemies.values():
            for position in v["positions"]:
                # Add 1 to the score if the spell will hit the unit
                distance = math.hypot(
                    position.tile_x - self.tile_x,
                    position.tile_y - self.tile_y - 2,
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
        for v in state.enemies.values():
            for position in v["positions"]:
                if position.tile_y <= 8 and v["transport"] == Transport.GROUND:
                    if (
                        self.tile_y == position.tile_y - 4
                        and self.tile_x == position.tile_x
                    ):
                        score = [1]

        return score

    def _calculate_fireball_score(self, state):
        """
        Play the fireball card if it will hit flying units
        """
        for v in state.enemies.values():
            for position in v["positions"]:
                if (
                    v["transport"] == Transport.AIR
                    and self.tile_y == position.tile_y - 4
                    and self.tile_x == position.tile_x
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

        self.score = card_to_score[self.card](state)
        return self.score
