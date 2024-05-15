import random
import time
import os
import subprocess
from datetime import datetime
from clashroyalebuildabot.bot import Bot
from custom_action import CustomAction
from clashroyalebuildabot.data.constants import DISPLAY_WIDTH, SCREENSHOT_WIDTH, DISPLAY_HEIGHT, SCREENSHOT_HEIGHT
from clashroyalebuildabot.data.constants import SCREEN_CONFIG

class CustomBot(Bot):
    def __init__(self, card_names, debug=False):
        preset_deck = {'minions', 'archers', 'arrows', 'giant', 'minipekka', 'fireball', 'knight', 'musketeer'}
        if set(card_names) != preset_deck:
            raise ValueError(f'You must use the preset deck with cards {preset_deck} for CustomBot')
        super().__init__(card_names, CustomAction, debug=debug)
        self.end_of_game_clicked = False
        self.pause_until = 0

    def _preprocess(self):
        for side in ['ally', 'enemy']:
            for k, v in self.state['units'][side].items():
                for unit in v['positions']:
                    bbox = unit['bounding_box']
                    bbox[0] *= DISPLAY_WIDTH / SCREENSHOT_WIDTH
                    bbox[1] *= DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
                    bbox[2] *= DISPLAY_WIDTH / SCREENSHOT_WIDTH
                    bbox[3] *= DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
                    bbox_bottom = [((bbox[0] + bbox[2]) / 2), bbox[3]]
                    unit['tile_xy'] = self._get_nearest_tile(*bbox_bottom)

    def run(self):
        while True:
            if self.end_of_game_clicked:
                if time.time() > self.pause_until:
                    if not any(action.name == "Battle" for action in self.get_actions()):
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] [INFO] Cant find Battle button force game restart.")

                        subprocess.run("adb shell am force-stop com.supercell.clashroyale", shell=True)
                        time.sleep(1)
                        subprocess.run("adb shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp", shell=True)

                        print(f"[{datetime.now().strftime('%H:%M:%S')}] [INFO] Waiting 10 seconds...")
                        time.sleep(10)

                    self.end_of_game_clicked = False
                else:
                    time.sleep(1.0)
                    continue

            self.set_state()

            if self.state['screen'] == 'end_of_game':
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [INFO] End of game detected. Waiting 10 seconds for battle button...")
                self.pause_until = time.time() + 10
                self.end_of_game_clicked = True
                time.sleep(10)

            actions = self.get_actions()

            if not actions:
                if self.debug:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [DEBUG] No actions available. Waiting for 1 second...")
                time.sleep(1.0)
                continue
            elif self.state['screen'] != 'lobby':
                random.shuffle(actions)
                self._preprocess()
                action = max(actions, key=lambda x: x.calculate_score(self.state))
                if action.score[0] == 0:
                    continue
                self.play_action(action)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [ACTION] Playing {action} with score {action.score} and sleeping for 1 second")
                time.sleep(1.0)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [INFO] In the main menu or no actions available. Waiting for 1 second...")
                time.sleep(1.0)
