import random
import threading
from typing import cast

from loguru import logger

from clashroyalebuildabot.constants import (
    ALL_TILES,
    ALLY_TILES,
    DISPLAY_CARD_DELTA_X,
    DISPLAY_CARD_HEIGHT,
    DISPLAY_CARD_INIT_X,
    DISPLAY_CARD_WIDTH,
    DISPLAY_CARD_Y,
    DISPLAY_HEIGHT,
    LEFT_PRINCESS_TILES,
    RIGHT_PRINCESS_TILES,
    TILE_HEIGHT,
    TILE_INIT_X,
    TILE_INIT_Y,
    TILE_WIDTH,
)
from clashroyalebuildabot.detectors.detector import Detector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.namespaces import Screens
from clashroyalebuildabot.namespaces.state import State
from clashroyalebuildabot.visualizer import Visualizer


class Bot:
    def __init__(self, actions, config):
        self.actions = actions
        self.auto_start = config["bot"]["auto_start_game"]
        self.end_of_game_clicked = False
        self.bypass_end_of_game_clicked = False
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # Detector checks the deck size, before the emulator is created.
        cards = [action.CARD for action in actions]
        self.cards_to_actions = dict(zip(cards, actions, strict=False))

        self.play_action_delay = config.get("ingame", {}).get("play_action", 1)
        self.visualizer = Visualizer(**config["visuals"])
        self.detector = Detector(
            cards=cards, screen_config=config.get("screen_detector")
        )

        # The emulator owns a screen-recording process and a frame thread,
        # so it is created last and closed again if anything after it fails.
        self.emulator = Emulator(device_serial=config["adb"]["device_serial"])
        try:
            if config["bot"]["load_deck"]:
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
        x = (
            DISPLAY_CARD_INIT_X
            + DISPLAY_CARD_WIDTH / 2
            + card_n * DISPLAY_CARD_DELTA_X
        )
        y = DISPLAY_CARD_Y + DISPLAY_CARD_HEIGHT / 2
        return x, y

    @staticmethod
    def _get_valid_tiles(state: State):
        tiles = list(ALLY_TILES)
        if state.numbers.left_enemy_princess_hp.number == 0:
            tiles += LEFT_PRINCESS_TILES
        if state.numbers.right_enemy_princess_hp.number == 0:
            tiles += RIGHT_PRINCESS_TILES
        return tiles

    def get_actions(self, state: State):
        valid_tiles = self._get_valid_tiles(state)
        actions = []
        for i in state.ready:
            card = state.cards[i + 1]
            if state.numbers.elixir.number < card.cost:
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
        self.emulator.click(*card_centre)
        self.emulator.click(*tile_centre)

    def step(self, state: State | None):
        old_screen = state.screen if state else None
        state = self.compute_state()
        if state is None:
            return state

        new_screen = state.screen
        if new_screen != old_screen:
            logger.info(f"New screen state: {new_screen}")

        if new_screen == Screens.UNKNOWN:
            self._log_and_wait("Unknown screen", 2)
            return state

        if new_screen == Screens.END_OF_GAME:
            if not self.end_of_game_clicked:
                self.emulator.click(
                    *cast(tuple[int, int], Screens.END_OF_GAME.click_xy)
                )
                self.end_of_game_clicked = True
                self._log_and_wait("Clicked END_OF_GAME screen", 2)
            return state
        self.end_of_game_clicked = False

        if new_screen == Screens.BYPASS_END_OF_GAME:
            if not self.bypass_end_of_game_clicked:
                self.emulator.click(
                    *cast(tuple[int, int], Screens.BYPASS_END_OF_GAME.click_xy)
                )
                self.bypass_end_of_game_clicked = True
                self._log_and_wait("Clicked BYPASS_END_OF_GAME screen", 2)
            return state
        self.bypass_end_of_game_clicked = False

        if self.auto_start and new_screen == Screens.LOBBY:
            self.emulator.click(*cast(tuple[int, int], Screens.LOBBY.click_xy))
            self._log_and_wait("Starting game", 2)
            return state

        self._handle_game_step(state)
        return state

    def _handle_game_step(self, state: State):
        actions = self.get_actions(state)
        if not actions:
            self._log_and_wait("No actions available", self.play_action_delay)
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
