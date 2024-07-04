import os
import random
import sys
import time

from loguru import logger
import yaml

from clashroyalebuildabot.constants import ALLY_TILES
from clashroyalebuildabot.constants import DEBUG_DIR
from clashroyalebuildabot.constants import DISPLAY_CARD_DELTA_X
from clashroyalebuildabot.constants import DISPLAY_CARD_HEIGHT
from clashroyalebuildabot.constants import DISPLAY_CARD_INIT_X
from clashroyalebuildabot.constants import DISPLAY_CARD_WIDTH
from clashroyalebuildabot.constants import DISPLAY_CARD_Y
from clashroyalebuildabot.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.constants import LEFT_PRINCESS_TILES
from clashroyalebuildabot.constants import RIGHT_PRINCESS_TILES
from clashroyalebuildabot.constants import SRC_DIR
from clashroyalebuildabot.constants import TILE_HEIGHT
from clashroyalebuildabot.constants import TILE_INIT_X
from clashroyalebuildabot.constants import TILE_INIT_Y
from clashroyalebuildabot.constants import TILE_WIDTH
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.namespaces import Screens


class Bot:
    def __init__(self, actions, auto_start=True, debug=False):
        self.actions = actions
        self.auto_start = auto_start
        self.debug = debug

        cards = [action.CARD for action in actions]
        if len(cards) != 8:
            raise ValueError(f"Must provide 8 cards but was given: {cards}")
        self.cards_to_actions = dict(zip(cards, actions))

        self.detector = Detector(cards=cards, debug=self.debug)
        self.emulator = Emulator()
        self.state = None

        self._setup_logger()
        self.end_of_game_clicked = False

    @staticmethod
    def _setup_logger():
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
        log_level = config.get("bot", {}).get("log_level", "INFO").upper()
        logger.remove()
        logger.add(sys.stdout, level=log_level)
        logger.add(
            os.path.join(DEBUG_DIR, "bot.log"),
            rotation="500 MB",
            level=log_level,
        )

    @staticmethod
    def _get_nearest_tile(x, y):
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(
            ((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5
        )
        return tile_x, tile_y

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        x = (
            DISPLAY_CARD_INIT_X
            + DISPLAY_CARD_WIDTH / 2
            + card_n * DISPLAY_CARD_DELTA_X
        )
        y = DISPLAY_CARD_Y + DISPLAY_CARD_HEIGHT / 2
        return x, y

    def _get_valid_tiles(self):
        tiles = ALLY_TILES
        if self.state.numbers["left_enemy_princess_hp"]["number"] == 0:
            tiles += LEFT_PRINCESS_TILES
        if self.state.numbers["right_enemy_princess_hp"]["number"] == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self):
        if not self.state:
            return []
        all_tiles = ALLY_TILES + LEFT_PRINCESS_TILES + RIGHT_PRINCESS_TILES
        valid_tiles = self._get_valid_tiles()
        actions = []
        for i in self.state.ready:
            card = self.state.cards[i + 1]
            if int(self.state.numbers["elixir"]["number"]) < card.cost:
                continue

            tiles = all_tiles if card.target_anywhere else valid_tiles
            actions.extend(
                [self.cards_to_actions[card](i, x, y) for (x, y) in tiles]
            )

        return actions

    def set_state(self):
        screenshot = self.emulator.take_screenshot()
        self.state = self.detector.run(screenshot)
        if self.auto_start and self.state.screen != Screens.IN_GAME:
            self.emulator.click(*self.state.screen.click_xy)
            logger.info("Starting game. Waiting for 2 seconds")
            time.sleep(2)

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.emulator.click(*card_centre)
        self.emulator.click(*tile_centre)

    def _restart_game(self):
        self.emulator.stop_game()
        time.sleep(1)
        self.emulator.start_game()
        logger.info("Starting game. Waiting 10 seconds.")
        time.sleep(10)
        self.end_of_game_clicked = False

    def _end_of_game(self):
        self.set_state()
        actions = self.get_actions()
        logger.info(f"Actions after end of game: {actions}")

        if self.state.screen == Screens.LOBBY:
            logger.debug("Lobby detected, resuming normal operation.")
            return

        logger.info("Can't find Battle button, force game restart.")
        self._restart_game()

    def step(self):
        if self.end_of_game_clicked:
            self._end_of_game()
            return

        old_screen = self.state.screen if self.state else None
        self.set_state()
        new_screen = self.state.screen
        if new_screen != old_screen:
            logger.info(f"New screen state: {new_screen}")

        if new_screen == Screens.END_OF_GAME:
            logger.info(
                "End of game detected. Waiting 10 seconds for battle button"
            )
            self.end_of_game_clicked = True
            time.sleep(10)
            return

        if new_screen == Screens.LOBBY:
            logger.info("In the main menu. Waiting for 1 second")
            time.sleep(1)
            return

        actions = self.get_actions()
        if not actions:
            logger.debug("No actions available. Waiting for 1 second")
            time.sleep(1)
            return

        random.shuffle(actions)
        best_score = [0]
        best_action = None
        for action in actions:
            score = action.calculate_score(self.state)
            if score > best_score:
                best_action = action
                best_score = score

        if best_score[0] == 0:
            logger.info("No good actions available. Waiting for 1 second")
            time.sleep(1)
            return

        self.play_action(best_action)
        logger.info(
            f"Playing {best_action} with score {best_score}. Waiting for 1 second"
        )
        time.sleep(1)

    def run(self):
        try:
            while True:
                self.step()
        except (KeyboardInterrupt, Exception):
            self.emulator.quit()
            logger.info("Thanks for using CRBAB, see you next time!")
