from clashroyalebuildabot.bot import Action
from clashroyalebuildabot.data.cards import Cards


class CustomAction(Action):
    score = None

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _calculate_spell_score(self, units, radius, min_to_hit):
        enemy_units = (unit for v in units["enemy"].values() for unit in v["positions"])
        scores = [
            (
                1 if self._distance(unit["tile_xy"][0], unit["tile_xy"][1] - 2, self.tile_x, self.tile_y) <= radius - 1 else 0,
                unit
            )
            for unit in enemy_units
        ]
        hit_units = sum(score[0] for score in scores)
        max_distance = min(
            (-self._distance(unit["tile_xy"][0], unit["tile_xy"][1] - 2, self.tile_x, self.tile_y)) for _, unit in scores
        ) if scores else float('inf')

        return [1 if hit_units >= min_to_hit else 0, hit_units, max_distance]

    def _calculate_unit_score(self, state, tile_x_conditions, score_if_met):
        score = [0.5] if state["numbers"]["elixir"]["number"] == 10 else [0]
        for unit in (unit for v in state["units"]["enemy"].values() for unit in v["positions"]):
            tile_x, tile_y = unit["tile_xy"]
            if self.tile_y < tile_y <= 14 and any(condition(tile_x) for condition in tile_x_conditions):
                score = score_if_met(self.tile_y, tile_y)
        return score

    def _calculate_knight_score(self, state):
        return self._calculate_unit_score(
            state,
            [lambda x: x > 8 and self.tile_x == 9, lambda x: x <= 8 and self.tile_x == 8],
            lambda my_y, enemy_y: [1, my_y - enemy_y],
        )

    def _calculate_minions_score(self, state):
        score = [0.5] if state["numbers"]["elixir"]["number"] == 10 else [0]
        for unit in (unit for v in state["units"]["enemy"].values() for unit in v["positions"]):
            tile_x, tile_y = unit["tile_xy"]
            distance = self._distance(tile_x, tile_y, self.tile_x, self.tile_y)
            if distance < 1:
                score = [1, -distance]
        return score

    def _calculate_fireball_score(self, state):
        return self._calculate_spell_score(state["units"], radius=2.5, min_to_hit=3)

    def _calculate_arrows_score(self, state):
        return self._calculate_spell_score(state["units"], radius=4, min_to_hit=5)

    def _calculate_archers_score(self, state):
        return self._calculate_unit_score(
            state,
            [lambda x: x > 8 and self.tile_x == 10, lambda x: x <= 8 and self.tile_x == 7],
            lambda my_y, enemy_y: [1, my_y - enemy_y],
        )

    def _calculate_giant_score(self, state):
        score = [0]
        left_hp, right_hp = (state["numbers"][f"{direction}_enemy_princess_hp"]["number"] for direction in ["left", "right"])
        if state["numbers"]["elixir"]["number"] == 10:
            if self.tile_x == 3:
                score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
            elif self.tile_x == 14:
                score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
        return score

    def _calculate_minipekka_score(self, state):
        left_hp, right_hp = (state["numbers"][f"{direction}_enemy_princess_hp"]["number"] for direction in ["left", "right"])
        score = [0]
        if self.tile_x == 3:
            score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
        elif self.tile_x == 14:
            score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
        return score

    def _calculate_musketeer_score(self, state):
        score = [0]
        for unit in (unit for v in state["units"]["enemy"].values() for unit in v["positions"]):
            tile_x, tile_y = unit["tile_xy"]
            distance = self._distance(tile_x, tile_y, self.tile_x, self.tile_y)
            if 5 < distance < 6:
                score = [1]
            elif distance < 5:
                score = [0]
        return score

    def calculate_score(self, state):
        name_to_score = {
            Cards.KNIGHT: self._calculate_knight_score,
            Cards.MINIONS: self._calculate_minions_score,
            Cards.FIREBALL: self._calculate_fireball_score,
            Cards.GIANT: self._calculate_giant_score,
            Cards.MINIPEKKA: self._calculate_minipekka_score,
            Cards.MUSKETEER: self._calculate_musketeer_score,
            Cards.ARROWS: self._calculate_arrows_score,
            Cards.ARCHERS: self._calculate_archers_score,
        }
        score_function = name_to_score[self.name]
        self.score = score_function(state)
        return self.score
