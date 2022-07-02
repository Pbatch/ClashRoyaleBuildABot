from clashroyalebuildabot.bot.action import Action


class StandardAction(Action):
    score = None

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _calculate_spell_score(self, units, radius, min_to_hit):
        """
        Calculate the score for a spell card (either fireball or arrows)

        The score is defined as [A, B, C]
            A is 1 if we'll hit `min_to_hit` or more units, 0 otherwise
            B is the number of units we hit
            C is the negative distance to the furthest unit
        """
        score = [0, 0, 0]
        for k, v in units.items():
            if k[:4] == 'ally':
                continue
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                # Assume the unit will move down a few spaces
                tile_y -= 2

                # Add 1 to the score if the spell will hit the unit
                distance = self._distance(tile_x, tile_y, self.tile_x, self.tile_y)
                if distance <= radius - 1:
                    score[1] += 1
                    score[2] = min(score[2], -distance)

        # Set score[0] to 1 if we think we'll hit enough units
        if score[1] >= min_to_hit:
            score[0] = 1

        return score

    def _calculate_knight_score(self, state):
        """
        Only play the knight if a ground troop is on our side of the battlefield
        Play the knight in the center, vertically aligned with the troop
        """
        score = [0] if state['numbers']['elixir']['number'] != 10 else [0.5]
        for k, v in state['units']['enemy'].items():
            if k[:4] == 'ally':
                continue
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                if self.tile_y < tile_y <= 14 and v['transport'] == 'ground':
                    if tile_x > 8 and self.tile_x == 9 or tile_x <= 8 and self.tile_x == 8:
                        score = [1, self.tile_y - tile_y]
        return score

    def _calculate_minions_score(self, state):
        """
        Only play minions on top of enemy units
        """
        score = [0] if state['numbers']['elixir']['number'] != 10 else [0.5]
        for k, v in state['units']['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                distance = self._distance(tile_x, tile_y, self.tile_x, self.tile_y)
                if distance < 1:
                    score = [1, -distance]
        return score

    def _calculate_fireball_score(self, state):
        """
        Only play fireball if at least 3 units will be hit
        Try to hit as many units as possible
        """
        return self._calculate_spell_score(state['units']['enemy'], radius=2.5, min_to_hit=3)

    def _calculate_arrows_score(self, state):
        """
        Only play arrows if at least 5 units will be hit
        Try to hit as many units as possible
        """
        return self._calculate_spell_score(state['units']['enemy'], radius=4, min_to_hit=5)

    def _calculate_archers_score(self, state):
        """
        Only play the archers if there is a troop on our side of the battlefield
        Play the archers in the center, vertically aligned with the troop
        """
        score = [0] if state['numbers']['elixir']['number'] != 10 else [0.5]
        for k, v in state['units']['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                if self.tile_y < tile_y <= 14:
                    if tile_x > 8 and self.tile_x == 10 or tile_x <= 8 and self.tile_x == 7:
                        score = [1, self.tile_y - tile_y]
        return score

    def _calculate_giant_score(self, state):
        """
        Only place the giant when at 10 elixir
        Place it as high up as possible
        Try to target the lowest hp tower
        """
        score = [0]
        left_hp, right_hp = [state['numbers'][f'{direction}_enemy_princess_hp']['number']
                             for direction in ['left', 'right']]
        if state['numbers']['elixir']['number'] == 10:
            if self.tile_x == 3:
                score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
            elif self.tile_x == 14:
                score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]

        return score

    def _calculate_minipekka_score(self, state):
        """
        Place minipekka on the bridge as high up as possible
        Try to target the lowest hp tower
        """
        left_hp, right_hp = [state['numbers'][f'{direction}_enemy_princess_hp']['number']
                             for direction in ['left', 'right']]
        score = [0]
        if self.tile_x == 3:
            score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
        elif self.tile_x == 14:
            score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
        return score

    def _calculate_musketeer_score(self, state):
        """
        Place musketeer at 5-6 tiles away from enemies
        That should be just within her range
        """
        score = [0]
        for k, v in state['units']['enemy'].items():
            if k[:4] == 'ally':
                continue
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                distance = self._distance(tile_x, tile_y, self.tile_x, self.tile_y)
                if 5 < distance < 6:
                    score = [1]
                elif distance < 5:
                    score = [0]
        return score

    def calculate_score(self, state):
        name_to_score = {'knight': self._calculate_knight_score,
                         'minions': self._calculate_minions_score,
                         'fireball': self._calculate_fireball_score,
                         'giant': self._calculate_giant_score,
                         'minipekka': self._calculate_minipekka_score,
                         'musketeer': self._calculate_musketeer_score,
                         'arrows': self._calculate_arrows_score,
                         'archers': self._calculate_archers_score
                         }
        score_function = name_to_score[self.name]
        score = score_function(state)
        self.score = score
        return score
