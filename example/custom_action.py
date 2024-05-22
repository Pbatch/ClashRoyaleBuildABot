"""
custom_action.py

Implementation of custom actions for the Clash Royale Bot.
"""

from clashroyalebuildabot.bot import Action


class CustomAction(Action):
    """
    A custom action for the Clash Royale Bot.
    """

    score = None  # Placeholder for calculated action score

    @staticmethod
    def _distance(x1, y1, x2, y2):
        """
        Calculates the distance between two points.
        """
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _calculate_spell_score(self, units, radius, min_to_hit):
        """
        Calculates the score for a spell card (fireball or arrows).

        The score is a list [A, B, C]:
            A: 1 if the spell hits at least `min_to_hit` units, 0 otherwise
            B: Number of units hit by the spell
            C: Negative distance to the furthest unit hit
        """
        score = [0, 0, 0]
        for k, v in units["enemy"].items():
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

    def _calculate_unit_score(self, state, tile_x_conditions, score_if_met):
        """
        Calculates the score for a unit card based on given conditions.
        """
        score = [0] if state["numbers"]["elixir"]["number"] != 10 else [0.5]
        for k, v in state["units"]["enemy"].items():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                if self.tile_y < tile_y <= 14 and any(
                    condition(tile_x) for condition in tile_x_conditions
                ):
                    score = score_if_met(self.tile_y, tile_y)
        return score

    def _calculate_knight_score(self, state):
        """
        Calculates the score for the Knight card.
        """
        return self._calculate_unit_score(
            state,
            [
                lambda x: x > 8 and self.tile_x == 9,
                lambda x: x <= 8 and self.tile_x == 8,
            ],
            lambda my_y, enemy_y: [1, my_y - enemy_y],
        )

    def _calculate_minions_score(self, state):
        """
        Only play minions on top of enemy units.
        """
        score = [0] if state["numbers"]["elixir"]["number"] != 10 else [0.5]
        for k, v in state["units"]["enemy"].items():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                distance = self._distance(
                    tile_x, tile_y, self.tile_x, self.tile_y
                )
                if distance < 1:
                    score = [1, -distance]
        return score

    def _calculate_fireball_score(self, state):
        """
        Only play fireball if at least 3 units will be hit.
        Try to hit as many units as possible.
        """
        return self._calculate_spell_score(
            state["units"], radius=2.5, min_to_hit=3
        )

    def _calculate_arrows_score(self, state):
        """
        Only play arrows if at least 5 units will be hit.
        Try to hit as many units as possible.
        """
        return self._calculate_spell_score(
            state["units"], radius=4, min_to_hit=5
        )

    def _calculate_archers_score(self, state):
        """
        Calculates the score for the Archers card.
        """
        return self._calculate_unit_score(
            state,
            [
                lambda x: x > 8 and self.tile_x == 10,
                lambda x: x <= 8 and self.tile_x == 7,
            ],
            lambda my_y, enemy_y: [1, my_y - enemy_y],
        )

    def _calculate_giant_score(self, state):
        """
        Only place the giant when at 10 elixir.
        Place it as high up as possible.
        Try to target the lowest HP tower.
        """
        score = [0]
        left_hp, right_hp = [
            state["numbers"][f"{direction}_enemy_princess_hp"]["number"]
            for direction in ["left", "right"]
        ]
        if state["numbers"]["elixir"]["number"] == 10:
            if self.tile_x == 3:
                score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
            elif self.tile_x == 14:
                score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]

        return score

    def _calculate_minipekka_score(self, state):
        """
        Place minipekka on the bridge as high up as possible.
        Try to target the lowest HP tower.
        """
        left_hp, right_hp = [
            state["numbers"][f"{direction}_enemy_princess_hp"]["number"]
            for direction in ["left", "right"]
        ]
        score = [0]
        if self.tile_x == 3:
            score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
        elif self.tile_x == 14:
            score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
        return score

    def _calculate_musketeer_score(self, state):
        """
        Place musketeer at 5-6 tiles away from enemies.
        That should be just within her range.
        """
        score = [0]
        for k, v in state["units"]["enemy"].items():
            for unit in v["positions"]:
                tile_x, tile_y = unit["tile_xy"]
                distance = self._distance(
                    tile_x, tile_y, self.tile_x, self.tile_y
                )
                if 5 < distance < 6:
                    score = [1]
                elif distance < 5:
                    score = [0]
        return score

    def calculate_score(self, state):
        name_to_score = {
            "knight": self._calculate_knight_score,
            "minions": self._calculate_minions_score,
            "fireball": self._calculate_fireball_score,
            "giant": self._calculate_giant_score,
            "minipekka": self._calculate_minipekka_score,
            "musketeer": self._calculate_musketeer_score,
            "arrows": self._calculate_arrows_score,
            "archers": self._calculate_archers_score,
        }
        score_function = name_to_score[self.name]
        score = score_function(state)
        self.score = score
        return score
