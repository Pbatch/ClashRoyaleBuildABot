from src.bot.bot import Bot
import numpy as np
import time
from pprint import pprint
import random


class PeteBot(Bot):
    def _calculate_action_scores(self, actions, state):
        # Preprocessing
        enemy_units = {k: [unit for unit in v if unit['confidence'] > 0.6]
                       for k, v in state['units'].items()
                       if k[:5] == 'enemy'}
        for k, v in enemy_units.items():
            for unit in v:
                bb = unit['bounding_box']
                bb_box_bottom = [((bb[0] + bb[2]) / 2), bb[3]]
                unit['tile_xy'] = self._get_nearest_tile(*bb_box_bottom)
        radii = {'fireball': 2.5, 'arrows': 4}

        scores = []
        for action in actions:
            card_name = state['cards'][action[0] + 1]['name']
            if card_name not in {'fireball', 'arrows'}:
                scores.append(0.5)
                continue

            score = 0
            for k, v in enemy_units.items():
                for unit in v:
                    tile_x, tile_y = unit['tile_xy']
                    distance = ((action[1] - tile_x) ** 2 + (action[2] - tile_y) ** 2) ** 0.5
                    if distance <= radii[card_name] - 1:
                        score += 1
            scores.append(score)

        return scores

    def run(self):
        while True:
            state = self.get_state()
            actions = self.get_actions(state)
            if actions:
                random.shuffle(actions)
                scores = self._calculate_action_scores(actions, state)
                best_idx = np.argmax(np.array(scores))
                action = actions[best_idx]
                self.play_action(action)
                print(f'Playing {state["cards"][action[0] + 1]["name"]} at tile ({action[1]}, {action[2]})')
            time.sleep(4)
