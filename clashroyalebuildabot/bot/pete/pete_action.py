from clashroyalebuildabot.bot.action import Action


class PeteAction(Action):
    RADII = {'fireball': 2.5, 'arrows': 4}
    score = None

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def _calculate_building_score(self, units):
        score = [0, 0, 0]

        n_enemies = sum([len(v) for k, v in units['enemy'].items()])

        # Play defensively if the enemy has a unit in our half
        if n_enemies != 0:
            rhs = 0
            lhs = 0
            for k, v in units['enemy'].items():
                for unit in v['positions']:
                    tile_x, tile_y = unit['tile_xy']
                    if tile_x > 8 and tile_y <= 17:
                        rhs += 1
                    elif tile_x <= 8 and tile_y <= 17:
                        lhs += 1

            if rhs > lhs:
                score[0] = int(self.tile_x > 8)
            else:
                score[0] = int(self.tile_x <= 8)
            score[1] = -self._distance(self.tile_x, self.tile_y, 8.5, 11)

        return score

    def _calculate_troop_score(self, units):
        """
        Calculate the score for a troop card (either fireball or arrows)

        The score is defined as [A, B, C]
            A is
                1 if the troop will 'attack' or 'defend'
                0 if the troop ignores 'defence'
                0.5 otherwise
            B is the negative distance of the troop to the centre
        """
        score = [0.5, 0, 0]

        # Play aggressively if the enemy has no units
        n_enemies = sum([len(v) for k, v in units['enemy'].items()])
        if self.target == 'buildings' and n_enemies == 0:
            score[0] = 1

        # Play defensively if the enemy has a unit in our half
        elif n_enemies != 0:
            rhs = 0
            lhs = 0
            for k, v in units['enemy'].items():
                for unit in v['positions']:
                    tile_x, tile_y = unit['tile_xy']
                    if tile_x > 8 and tile_y <= 17:
                        rhs += 1
                    elif tile_x <= 8 and tile_y <= 17:
                        lhs += 1

            if rhs > lhs:
                score[0] = int(self.tile_x > 8)
            else:
                score[0] = int(self.tile_x <= 8)
            score[1] = -self._distance(self.tile_x, self.tile_y, 8.5, 11)

        return score

    def _calculate_spell_score(self, units):
        """
        Calculate the score for a spell card (either fireball or arrows)

        The score is defined as [A, B, C]
            A is 2 if we'll hit 3 or more units, 0 otherwise
            B is the number of units we hit
            C is the negative distance to the furthest unit
        """
        score = [0, 0, 0]
        for k, v in units['enemy'].items():
            for unit in v['positions']:
                tile_x, tile_y = unit['tile_xy']
                # Assume the unit will move down a space
                tile_y -= 1

                # Add 1 to the score if the spell will hit the unit
                distance = self._distance(tile_x, tile_y, self.tile_x, self.tile_y)
                if distance <= self.RADII[self.name] - 1:
                    score[1] += 1
                    score[2] = min(score[2], -distance)

        # Set score[0] to 2 if we think we'll hit 3 or more units
        if score[1] >= 3:
            score[0] = 2

        return score

    def calculate_score(self, units):
        if self.type == 'spell':
            score = self._calculate_spell_score(units)
        elif self.type == 'troop':
            score = self._calculate_troop_score(units)
        elif self.type == 'building':
            score = self._calculate_building_score(units)
        else:
            raise ValueError(f'Scoring for type {self.type} is not supported')
        self.score = score
        return score
