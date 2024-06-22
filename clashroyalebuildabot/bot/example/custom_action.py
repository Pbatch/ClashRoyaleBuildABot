import math

from clashroyalebuildabot.bot.bot import Action
from clashroyalebuildabot.namespaces.cards import Cards


class CustomAction(Action):
    score = None

    def _calculate_spell_score(self, state, radius, min_to_hit):
        hit_units = 0
        max_distance = float("inf")
        for v in state.enemies.values():
            for position in v["positions"]:
                distance = math.hypot(
                    self.tile_x - position.tile_x,
                    self.tile_y - position.tile_y + 2,
                )
                if distance <= radius - 1:
                    hit_units += 1
                    max_distance = min(max_distance, -distance)

        return [1 if hit_units >= min_to_hit else 0, hit_units, max_distance]

    def _calculate_unit_score(self, state, tile_x_conditions, score_if_met):
        score = [0.5] if state.numbers["elixir"]["number"] == 10 else [0]
        for v in state.enemies.values():
            for position in v["positions"]:
                if self.tile_y < position.tile_y <= 14 and any(
                    condition(position.tile_x)
                    for condition in tile_x_conditions
                ):
                    score = score_if_met(self.tile_y, position.tile_y)
        return score

    def _calculate_knight_score(self, state):
        return self._calculate_unit_score(
            state,
            [
                lambda x: x > 8 and self.tile_x == 9,
                lambda x: x <= 8 and self.tile_x == 8,
            ],
            lambda my_y, enemy_y: [1, my_y - enemy_y],
        )

    def _calculate_minions_score(self, state):
        score = [0.5] if state.numbers["elixir"]["number"] == 10 else [0]
        for v in state.enemies.values():
            for position in v["positions"]:
                distance = math.hypot(
                    position.tile_x - self.tile_x,
                    position.tile_y - self.tile_y,
                )
                if distance < 1:
                    score = [1, -distance]
        return score

    def _calculate_fireball_score(self, state):
        return self._calculate_spell_score(state, radius=2.5, min_to_hit=3)

    def _calculate_arrows_score(self, state):
        return self._calculate_spell_score(state, radius=4, min_to_hit=5)

    def _calculate_archers_score(self, state):
        return self._calculate_unit_score(
            state,
            [
                lambda x: x > 8 and self.tile_x == 10,
                lambda x: x <= 8 and self.tile_x == 7,
            ],
            lambda my_y, enemy_y: [1, my_y - enemy_y],
        )

    def _calculate_giant_score(self, state):
        score = [0]
        left_hp, right_hp = (
            state.numbers[f"{direction}_enemy_princess_hp"]["number"]
            for direction in ["left", "right"]
        )
        if state.numbers["elixir"]["number"] == 10:
            if self.tile_x == 3:
                score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
            elif self.tile_x == 14:
                score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
        return score

    def _calculate_minipekka_score(self, state):
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

    def _calculate_musketeer_score(self, state):
        for v in state.enemies.values():
            for position in v["positions"]:
                distance = math.hypot(
                    position.tile_x - self.tile_x,
                    position.tile_y - self.tile_y,
                )
                if 5 < distance < 6:
                    return [1]
                elif distance < 5:
                    return [0]
        return [0]

    def calculate_score(self, state):
        card_to_score = {
            Cards.KNIGHT: self._calculate_knight_score,
            Cards.MINIONS: self._calculate_minions_score,
            Cards.FIREBALL: self._calculate_fireball_score,
            Cards.GIANT: self._calculate_giant_score,
            Cards.MINIPEKKA: self._calculate_minipekka_score,
            Cards.MUSKETEER: self._calculate_musketeer_score,
            Cards.ARROWS: self._calculate_arrows_score,
            Cards.ARCHERS: self._calculate_archers_score,
        }
        self.score = card_to_score[self.card](state)
        return self.score
