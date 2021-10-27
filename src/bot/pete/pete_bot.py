from src.bot.bot import Bot
from src.bot.pete.pete_action import PeteAction
import numpy as np
import random
from copy import deepcopy
import time


class PeteBot(Bot):
    def __init__(self, card_names):
        super().__init__(card_names, PeteAction)

    def _preprocess(self):
        """
        Perform preprocessing on the state

        We retrieve a list of the enemy units and their approximate (x, y) coordinates
        """
        enemy_units = {k: [deepcopy(unit) for unit in v if unit['confidence'] > 0.6]
                       for k, v in self.state['units'].items()
                       if k[:5] == 'enemy'}
        for k, v in enemy_units.items():
            for unit in v:
                bb = unit['bounding_box']
                bb_box_bottom = [((bb[0] + bb[2]) / 2), bb[3]]
                unit['tile_xy'] = self._get_nearest_tile(*bb_box_bottom)
        return enemy_units

    def _calculate_action_scores(self, actions):
        """
        Calculate a score for every action
        """
        enemy_units = self._preprocess()
        action_scores = [a.calculate_score(enemy_units) for a in actions]
        return action_scores

    def run(self):
        import os
        i = 0
        os.makedirs('screenshots', exist_ok=True)
        while True:
            # Set the state of the game
            self.set_state()
            # Obtain a list of playable actions
            actions = self.get_actions()
            if actions:
                # Shuffle the actions (because action scores might be the same)
                random.shuffle(actions)
                # Calculate a score for each action
                scores = self._calculate_action_scores(actions)
                # Choose the best action
                best_idx = np.argmax(np.array(scores))
                action = actions[best_idx]
                # Play the best action
                self.play_action(action)
                # Log the result
                print(f'Playing {action}')
                # Take a screenshot
                screenshot = self.screen.take_screenshot()
                screenshot.save(f'screenshots/{i}.jpg')
                i += 1
            time.sleep(3)
