import random
import threading
from typing import cast

from loguru import logger

from clashroyalebuildabot.config import Config
from clashroyalebuildabot.constants.device_screen import (
    ALL_TILES,
    ALLY_TILES,
    DISPLAY_HEIGHT,
    HAND_CARD_BOXES,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
    TILE_HEIGHT,
    TILE_INIT_X,
    TILE_INIT_Y,
    TILE_WIDTH,
)
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.game import ScreenName, Screens
from clashroyalebuildabot.game.state import State
from clashroyalebuildabot.gui.visualizer import Visualizer

# Screens the bot just waits through.
WAITING_SCREENS = {
    ScreenName.UNKNOWN,
    ScreenName.SEARCHING_FOR_OPPONENT,
    ScreenName.LOADING,
    ScreenName.VS,
    ScreenName.MATCH_OVER,
}
# Seconds between looks at a screen outside a battle. The screen detector
# answers about once a second, so looking more often gains nothing.
SCREEN_POLL_DELAY = 0.5


class Bot:
    def __init__(self, actions, config: Config):
        self.actions = actions
        self.auto_start = config.bot.auto_start_game
        self.end_of_game_clicked = False
        self.bypass_end_of_game_clicked = False
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # Detector checks the deck size, before the emulator is created.
        cards = [action.CARD for action in actions]
        self.cards_to_actions = dict(zip(cards, actions, strict=False))

        self.play_action_delay = config.ingame.play_action
        self.visualizer = Visualizer(**config.visuals.model_dump())
        self.detector = Detector(
            cards=cards, screen_config=config.screen_detector
        )

        # The emulator owns a screen-recording process and a frame thread,
        # so it is created last and closed again if anything after it fails.
        self.emulator = Emulator(device_serial=config.adb.device_serial)
        try:
            if config.bot.load_deck:
                self.emulator.load_deck(cards)
        except BaseException:
            self.emulator.close()
            raise

    def _log_and_wait(self, prefix, delay):
        suffix = ""
        if delay > 1:
            suffix = "s"
        message = f"{prefix}. Waiting for {delay} second{suffix}."
        logger.info(message)
        # Returns early if stop() is called, so stopping is never delayed.
        self._stop_event.wait(delay)

    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def pause(self):
        if not self.is_paused:
            self._pause_event.set()
            logger.info("Bot paused.")

    def resume(self):
        if self.is_paused:
            self._pause_event.clear()
            logger.info("Bot resumed.")

    def toggle_pause(self):
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    @staticmethod
    def _get_tile_centre(tile_x, tile_y):
        x = TILE_INIT_X + (tile_x + 0.5) * TILE_WIDTH
        y = DISPLAY_HEIGHT - TILE_INIT_Y - (tile_y + 0.5) * TILE_HEIGHT
        return x, y

    @staticmethod
    def _get_card_centre(card_n):
        left, top, right, bottom = HAND_CARD_BOXES[card_n]
        return (left + right) / 2, (top + bottom) / 2

    @staticmethod
    def _get_valid_tiles(state: State):
        tiles = list(ALLY_TILES)
        if state.numbers.towers.left_enemy_princess.hp == 0:
            tiles += LEFT_PRINCESS_TILES
        if state.numbers.towers.right_enemy_princess.hp == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self, state: State):
        valid_tiles = self._get_valid_tiles(state)
        actions = []
        for i in state.ready:
            card = state.cards[i + 1]
            if state.numbers.elixir < card.cost:
                continue

            tiles = ALL_TILES if card.target_anywhere else valid_tiles
            card_actions = [
                self.cards_to_actions[card](i, x, y) for (x, y) in tiles
            ]
            actions.extend(card_actions)

        return actions

    def compute_state(self) -> State | None:
        screenshot = self.emulator.take_screenshot()
        if screenshot is None:
            return None
        state = self.detector.run(screenshot)
        if state is not None:
            self.visualizer.run(screenshot, state)
        return state

    def play_action(self, action):
        card_centre = self._get_card_centre(action.index)
        tile_centre = self._get_tile_centre(action.tile_x, action.tile_y)
        self.emulator.tap_sequence([card_centre, tile_centre])

    def step(self, state: State | None):
        old_screen = state.screen if state else None
        state = self.compute_state()
        if state is None:
            return state

        new_screen = state.screen
        if new_screen != old_screen:
            logger.info(f"New screen state: {new_screen}")

        # Wait here, before the end-of-game flags below are cleared, so a
        # flicker through one of these screens can't cause a second tap.
        if new_screen in WAITING_SCREENS:
            self._log_and_wait(
                f"Waiting on the {new_screen} screen", SCREEN_POLL_DELAY
            )
            return state

        if new_screen == ScreenName.END_OF_GAME:
            if not self.end_of_game_clicked:
                self.emulator.click(
                    *cast(
                        tuple[int, int],
                        Screens.get(ScreenName.END_OF_GAME).click_xy,
                    )
                )
                self.end_of_game_clicked = True
                self._log_and_wait("Clicked END_OF_GAME screen", 2)
            return state
        self.end_of_game_clicked = False

        if new_screen == ScreenName.BYPASS_END_OF_GAME:
            if not self.bypass_end_of_game_clicked:
                self.emulator.click(
                    *cast(
                        tuple[int, int],
                        Screens.get(ScreenName.BYPASS_END_OF_GAME).click_xy,
                    )
                )
                self.bypass_end_of_game_clicked = True
                self._log_and_wait("Clicked BYPASS_END_OF_GAME screen", 2)
            return state
        self.bypass_end_of_game_clicked = False

        if self.auto_start and new_screen == ScreenName.LOBBY:
            self.emulator.click(
                *cast(tuple[int, int], Screens.get(ScreenName.LOBBY).click_xy)
            )
            self._log_and_wait("Starting game", 2)
            return state

        # Only play cards in a battle, never in the lobby.
        if new_screen != ScreenName.IN_GAME:
            self._log_and_wait(
                f"Waiting on the {new_screen} screen", SCREEN_POLL_DELAY
            )
            return state

        self._handle_game_step(state)
        return state

    def _handle_game_step(self, state: State):
        # Only playing a card is followed by a wait, for it to land and the
        # elixir to drop. Otherwise the bot looks again at the next frame,
        # so it plays as soon as a card is affordable or worth playing.
        actions = self.get_actions(state)
        if not actions:
            logger.debug("No actions available")
            return

        random.shuffle(actions)
        best_score = [0]
        best_action = None
        for action in actions:
            score = action.calculate_score(state)
            if score > best_score:
                best_action = action
                best_score = score

        if best_score[0] == 0:
            logger.debug("No good actions available")
            return

        self.play_action(best_action)
        self._log_and_wait(
            f"Playing {best_action} with score {best_score}",
            self.play_action_delay,
        )

    def run(self):
        """Play until stop() is called. Always closes the emulator on exit."""
        state = None
        try:
            while not self._stop_event.is_set():
                if self.is_paused:
                    self._stop_event.wait(0.1)
                    continue

                state = self.step(state)
        except KeyboardInterrupt:
            pass
        finally:
            self.detector.close()
            self.emulator.close()
        logger.info("Thanks for using CRBAB, see you next time!")

    def stop(self):
        """Ask run() to return. Safe to call from any thread."""
        self._stop_event.set()
