import random
import threading
import time

import keyboard
from loguru import logger

from clashroyalebuildabot.constants import ALL_TILES
from clashroyalebuildabot.constants import ALLY_TILES
from clashroyalebuildabot.constants import DISPLAY_CARD_DELTA_X
from clashroyalebuildabot.constants import DISPLAY_CARD_HEIGHT
from clashroyalebuildabot.constants import DISPLAY_CARD_INIT_X
from clashroyalebuildabot.constants import DISPLAY_CARD_WIDTH
from clashroyalebuildabot.constants import DISPLAY_CARD_Y
from clashroyalebuildabot.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.constants import LEFT_PRINCESS_TILES
from clashroyalebuildabot.constants import RIGHT_PRINCESS_TILES
from clashroyalebuildabot.constants import TILE_HEIGHT
from clashroyalebuildabot.constants import TILE_INIT_X
from clashroyalebuildabot.constants import TILE_INIT_Y
from clashroyalebuildabot.constants import TILE_WIDTH
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.visualizer import Visualizer
from error_handling import WikifiedError

pause_event = threading.Event()
pause_event.set()
is_paused_logged = False
is_resumed_logged = True


class Bot:
    is_paused_logged = False
    is_resumed_logged = True

    def __init__(self, actions, config):
        self.actions = actions
        self.auto_start = config["bot"]["auto_start_game"]
        self.end_of_game_clicked = False
        self.should_run = True

        cards = [action.CARD for action in actions]
        if len(cards) != 8:
            raise WikifiedError(
                "005", f"Must provide 8 cards but {len(cards)} was given"
            )
        self.cards_to_actions = dict(zip(cards, actions))

        self.visualizer = Visualizer(**config["visuals"])
        self.emulator = Emulator(**config["adb"])
        self.detector = Detector(cards=cards)
        self.state = None
        self.play_action_delay = config.get("ingame", {}).get("play_action", 1)

        keyboard_thread = threading.Thread(
            target=self._handle_keyboard_shortcut, daemon=True
        )
        keyboard_thread.start()

        if config["bot"]["load_deck"]:
            self.emulator.load_deck(cards)

    @staticmethod
    def _log_and_wait(prefix, delay):
        suffix = ""
        if delay > 1:
            suffix = "s"
        message = f"{prefix}. Waiting for {delay} second{suffix}."
        logger.info(message)
        time.sleep(delay)

    @staticmethod
    def _handle_keyboard_shortcut():
        while True:
            keyboard.wait("ctrl+p")
            Bot.pause_or_resume()

    @staticmethod
    def pause_or_resume():
        if pause_event.is_set():
            logger.info("Bot paused.")
            pause_event.clear()
            Bot.is_paused_logged = True
            Bot.is_resumed_logged = False
        else:
            logger.info("Bot resumed.")
            pause_event.set()
            Bot.is_resumed_logged = True
            Bot.is_paused_logged = False

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
        if self.state.numbers.left_enemy_princess_hp.number == 0:
            tiles += LEFT_PRINCESS_TILES
        if self.state.numbers.right_enemy_princess_hp.number == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self):
        if not self.state:
            return []
        valid_tiles = self._get_valid_tiles()
        actions = []
        for i in self.state.ready:
            card = self.state.cards[i + 1]
            if self.state.numbers.elixir.number < card.cost:
                continue

            tiles = ALL_TILES if card.target_anywhere else valid_tiles
            card_actions = [
                self.cards_to_actions[card](i, x, y) for (x, y) in tiles
            ]
            actions.extend(card_actions)

        return actions

    def set_state(self):
        screenshot = self.emulator.take_screenshot()
        self.state = self.detector.run(screenshot)
        self.visualizer.run(screenshot, self.state)

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.emulator.click(*card_centre)
        self.emulator.click(*tile_centre)

    def _handle_play_pause_in_step(self):
        if not pause_event.is_set():
            if not Bot.is_paused_logged:
                logger.info("Bot paused.")
                Bot.is_paused_logged = True
            time.sleep(0.1)
            return
        if not Bot.is_resumed_logged:
            logger.info("Bot resumed.")
            Bot.is_resumed_logged = True

    def step(self):
        self._handle_play_pause_in_step()
        old_screen = self.state.screen if self.state else None
        self.set_state()
        new_screen = self.state.screen
        if new_screen != old_screen:
            logger.info(f"New screen state: {new_screen}")

        if new_screen == Screens.UNKNOWN:
            self._log_and_wait("Unknown screen", 2)
            return

        if new_screen == Screens.END_OF_GAME:
            if not self.end_of_game_clicked:
                self.emulator.click(*self.state.screen.click_xy)
                self.end_of_game_clicked = True
                self._log_and_wait("Clicked END_OF_GAME screen", 2)
            return

        self.end_of_game_clicked = False

        if self.auto_start and new_screen == Screens.LOBBY:
            self.emulator.click(*self.state.screen.click_xy)
            self.end_of_game_clicked = False
            self._log_and_wait("Starting game", 2)
            return

        self._handle_game_step()

    def _handle_game_step(self):
        actions = self.get_actions()
        if not actions:
            self._log_and_wait("No actions available", self.play_action_delay)
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
            self._log_and_wait(
                "No good actions available", self.play_action_delay
            )
            return

        self.play_action(best_action)
        self._log_and_wait(
            f"Playing {best_action} with score {best_score}",
            self.play_action_delay,
        )

    def run(self):
        try:
            while self.should_run:
                if not pause_event.is_set():
                    time.sleep(0.1)
                    continue

                self.step()
            logger.info("Thanks for using CRBAB, see you next time!")
        except KeyboardInterrupt:
            logger.info("Thanks for using CRBAB, see you next time!")

    def stop(self):
        self.should_run = False
