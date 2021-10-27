from src.bot.action import Action


class PeteAction(Action):
    RADII = {'fireball': 2.5, 'arrows': 4}

    def _calculate_troop_score(self, enemy_units):
        return 0.5

    def _calculate_spell_score(self, enemy_units):
        """
        Calculate the score for a spell card (either fireball or arrows)

        The score is an estimate of the number of units the spell will hit
        """
        score = 0
        for k, v in enemy_units.items():
            for unit in v:
                tile_x, tile_y = unit['tile_xy']
                # Assume the unit will move down a space
                tile_y -= 1
                distance = ((self.tile_x - tile_x) ** 2 + (self.tile_y - tile_y) ** 2) ** 0.5
                if distance <= self.RADII[self.name] - 1:
                    score += 1
        return score

    def calculate_score(self, enemy_units):
        if self.type == 'spell':
            score = self._calculate_spell_score(enemy_units)
        elif self.type == 'troop':
            score = self._calculate_troop_score(enemy_units)
        else:
            raise ValueError(f'Scoring for type {self.type} is not supported')
        return score
