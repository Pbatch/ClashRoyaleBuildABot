from clashroyalebuildabot.bot.action import Action


class TwoSixHogCycleAction(Action):
    score = 0

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _calculate_enemy_troops(self, state):
        for k, v in state['units']['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                if self.tile_y < tile_y <= 14:
                    if tile_x > 8 and self.tile_x == 9 or tile_x <= 8 and self.tile_x == 8:
                        return True
        return False

    def _calculate_hog_rider_score(self, state):
        """
        If there are no enemy troops on our side of the arena and
        the player has 7 elixir or more
        Place hog rider on the bridge as high up as possible
        Try to target the lowest hp tower
        """
        for k, v in state['units']['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                if self.tile_y < tile_y <= 14:
                    if tile_x > 8 and self.tile_x == 10 or tile_x <= 8 and self.tile_x == 7:
                        score = [0]
                        return score

        if state['numbers']['elixir']['number'] >= 7:
            left_hp, right_hp = [state['numbers'][f'{direction}_enemy_princess_hp']['number']
                                 for direction in ['left', 'right']]

            score = [0]
            if self.tile_x == 3:
                score = [1, self.tile_y, left_hp != -1, left_hp <= right_hp]
            elif self.tile_x == 14:
                score = [1, self.tile_y, right_hp != -1, right_hp <= left_hp]
            return score
        return [0]

    def _calculate_cannon_score(self, state):
        """
        If there are ground troops place the cannon in the middle of the arena

        :param state:
        :return:
        """

        score = [0]
        for side in ['ally', 'enemy']:
            for k, v in state['units'][side].items():
                for unit in v['positions']:
                    tile_x, tile_y = unit['tile_xy']
                    if v['transport'] == 'ground':
                        if tile_y >= 10:
                            if 8 < self.tile_x < 10:
                                if self.tile_y == 10:
                                    score = [2]
        return score

    def _calculate_musketeer_score(self, state):
        """
        If there are flying troops
        Place musketeer at 7 tiles in front of the enemies
        That should be just within her range and not too close to the enemy
        """
        score = [0]
        for side in ['ally', 'enemy']:
            for k, v in state['units'][side].items():
                for unit in v['positions']:
                    tile_x, tile_y = unit['tile_xy']
                    if v['transport'] == 'air' and self.tile_y == tile_y - 7:
                        score = [2]
        return score

    def _calculate_ice_golem_score(self, state):
        """
        If there is a ground troop on the bridge place the ice golem in the middle of the
        arena one tile away from the enemy
        """
        score = [0]
        for side in ['ally', 'enemy']:
            for k, v in state['units'][side].items():
                for unit in v['positions']:
                    tile_x, tile_y = unit['tile_xy']
                    if (18 >= tile_y >= 15) and (v['transport'] == 'ground'):
                        if tile_x > 8:
                            if self.tile_y == 14 and self.tile_x == 8:
                                score = [2]
                        if tile_x <= 8:
                            if self.tile_y == 14 and self.tile_x == 9:
                                score = [2]

        return score

    def _calculate_ice_spirit_score(self, state):
        """
        Place the ice spirit in the middle of the arena when a ground troop is on the bridge
        """
        score = [0] if state['numbers']['elixir']['number'] != 10 else [0.5]
        score = [0]
        for side in ['ally', 'enemy']:
            for k, v in state['units'][side].items():
                for unit in v['positions']:
                    tile_x, tile_y = unit['tile_xy']
                    if (18 >= tile_y >= 15) and (v['transport'] == 'ground'):
                        if tile_x > 8:
                            if self.tile_y == 10 and self.tile_x == 8:
                                score = [2]
                        if tile_x <= 8:
                            if self.tile_y == 10 and self.tile_x == 9:
                                score = [2]

        return score

    def _calculate_spell_score(self, units, radius, min_to_hit):
        """
        Calculate the score for a spell card (either fireball or arrows)

        The score is defined as [A, B, C]
            A is 1 if we'll hit `min_to_hit` or more units, 0 otherwise
            B is the number of units we hit
            C is the negative distance to the furthest unit
        """
        score = [0, 0, 0]
        for k, v in units['enemy'].items():
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

    def _calculate_log_score(self, state):
        """
        Calculate the score for the log card
        """
        units = state['units']
        score = [0]
        for k, v in units['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                if tile_y <= 8 and v['transport'] == 'ground':
                    if self.tile_y == tile_y - 4 and self.tile_x == tile_x:
                        score = [1]

        return score

    def _calculate_fireball_score(self, state):
        """
        Play the fireball card if it will hit flying units
        """
        units = state['units']
        score = [0]
        for k, v in units['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                if v['transport'] == 'air':
                    if self.tile_y == tile_y - 4 and self.tile_x == tile_x:
                        score = [1]
                        return score
        return self._calculate_spell_score(state['units'], radius=2.5, min_to_hit=3)

    def calculate_score(self, state):
        name_to_score = {'hog_rider': self._calculate_hog_rider_score,
                         'ice_golem': self._calculate_ice_golem_score,
                         'fireball': self._calculate_fireball_score,
                         'ice_spirit': self._calculate_ice_spirit_score,
                         'the_log': self._calculate_log_score,
                         'musketeer': self._calculate_musketeer_score,
                         'cannon': self._calculate_cannon_score,
                         'skeletons': self._calculate_ice_spirit_score,
                         }

        score_function = name_to_score[self.name]
        score = score_function(state)
        self.score = score
        return score
