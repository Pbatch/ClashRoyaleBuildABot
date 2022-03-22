import random
import time

from src.bot.bot import Bot
from src.bot.pete.pete_action import PeteAction


class PeteBot(Bot):
    def __init__(self, card_names, debug=False):
        super().__init__(card_names, PeteAction, debug=debug)

    def _preprocess(self):
        """
        Perform preprocessing on the state

        Estimate the tile of each unit to be the bottom of their bounding box
        """
        for k, v in self.state['units'].items():
            for unit in v:
                bb = unit['bounding_box']
                bb_box_bottom = [((bb[0] + bb[2]) / 2), bb[3]]
                unit['tile_xy'] = self._get_nearest_tile(*bb_box_bottom)

    def _calculate_action_scores(self, actions):
        """
        Calculate a score for every action
        """
        self._preprocess()
        action_scores = [a.calculate_score(self.state['units']) for a in actions]
        return action_scores

    def run(self):
        while True:
            # Set the state of the game
            self.set_state()
            # Obtain a list of playable actions
            actions = self.get_actions()
            if actions:
                # Shuffle the actions (because action scores might be the same)
                random.shuffle(actions)
                # Preprocessing
                self._preprocess()
                # Get the best action
                action = max(actions, key=lambda x: x.calculate_score(self.state['units']))
                # Skip the action if it doesn't score high enough
                if action.score[0] == 0:
                    continue
                # Play the best action
                self.play_action(action)
                # Log the result
                print(f'Playing {action} with score {action.score}')
            time.sleep(0.5)
