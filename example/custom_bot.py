"""
custom_bot.py
Implementation of a custom bot for Clash Royale, based on clashroyalebuildabot.
"""

import random
import time
import os  # For file paths
from clashroyalebuildabot.bot import Bot
from custom_action import CustomAction
from clashroyalebuildabot.data.constants import DISPLAY_WIDTH, SCREENSHOT_WIDTH, DISPLAY_HEIGHT, SCREENSHOT_HEIGHT
from clashroyalebuildabot.data.constants import SCREEN_CONFIG

class CustomBot(Bot):
    """
    A custom bot for Clash Royale.
    """

    def __init__(self, card_names, debug=False):
        """
        Initializes the custom bot.

        Args:
            card_names: A list of card names in the deck.
            debug: Whether to enable debug mode (default: False).
        """

        preset_deck = {'minions', 'archers', 'arrows', 'giant', 'minipekka', 'fireball', 'knight', 'musketeer'}
        if set(card_names) != preset_deck:
            raise ValueError(f'You must use the preset deck with cards {preset_deck} for CustomBot')
        super().__init__(card_names, CustomAction, debug=debug)
        # Variable to track if end_of_game was recently clicked
        self.end_of_game_clicked = False
        self.pause_until = 0  # Variable to store the time until which to pause

    def _preprocess(self):
        """
        Performs preprocessing steps on the game state.

        Estimates the tile of each unit to be the bottom of their bounding box.
        """

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
                    
    def _click(self, x, y):
        """
        Clicks at the specified coordinates within the game window.
        """
        # Implement the actual click logic here (e.g., using pyautogui or another library)
        pass  # Temporary placeholder

    def run(self):
        """
        Starts the bot and runs it in a loop.
        """
        print("Custom Bot is running...")
        while True:
            # Check for end of game screen and pause
            if self.end_of_game_clicked:
                if time.time() > self.pause_until:
                    self.end_of_game_clicked = False
                else:
                    time.sleep(1.0)  # Wait until the pause is over
                    continue

            # Update game state
            self.set_state()

            # End of game detected, but no actions performed yet
            if self.state['screen'] == 'end_of_game':
                self._click(*SCREEN_CONFIG['end_of_game']['click_coordinates'])
                print("End of game detected, waiting for 10 seconds...")
                self.pause_until = time.time() + 10  # Set pause for 10 seconds
                self.end_of_game_clicked = True  # Mark the end of the game
                time.sleep(2)  # Additional pause to ensure state is updated
                continue  # Skip to the next loop iteration without performing actions

            # Get possible actions
            actions = self.get_actions()

            if not actions:  # No actions available
                print("No actions available. Waiting for 1 second...")
                time.sleep(1.0)
                continue
            # Perform actions only if in the game and not in the main menu
            elif self.state['screen'] != 'lobby':
                # Shuffle actions (since action scores might be the same)
                random.shuffle(actions)
                # Preprocess
                self._preprocess()
                # Select the best action
                action = max(actions, key=lambda x: x.calculate_score(self.state))
                # Skip the action if it doesn't score high enough
                if action.score[0] == 0:
                    continue
                # Play the best action
                self.play_action(action)
                # Log the result
                print(f'Playing {action} with score {action.score} and sleeping for 1 second')
                time.sleep(1.0)
            else:
                print("In the main menu or no actions available. Waiting for 1 second...")
                time.sleep(1.0)
