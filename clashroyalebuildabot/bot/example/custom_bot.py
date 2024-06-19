import random
import subprocess
import time

from loguru import logger

from clashroyalebuildabot.bot import Bot
from clashroyalebuildabot.bot.example.custom_action import CustomAction
from clashroyalebuildabot.data.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.data.constants import DISPLAY_WIDTH
from clashroyalebuildabot.data.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.data.constants import SCREENSHOT_WIDTH
from clashroyalebuildabot.namespaces.cards import Cards


class CustomBot(Bot):
    def __init__(self, cards, debug=False):
        preset_deck = {
            Cards.MINIONS,
            Cards.ARCHERS,
            Cards.ARROWS,
            Cards.GIANT,
            Cards.MINIPEKKA,
            Cards.FIREBALL,
            Cards.KNIGHT,
            Cards.MUSKETEER,
        }
        if set(cards) != preset_deck:
            raise ValueError(f"CustomBot must use cards: {preset_deck}")
        super().__init__(cards, CustomAction, debug=debug)
        self.end_of_game_clicked = False
        self.pause_until = 0
        self.scale_x = DISPLAY_WIDTH / SCREENSHOT_WIDTH
        self.scale_y = DISPLAY_HEIGHT / SCREENSHOT_HEIGHT

    def _preprocess(self):
        for side in ["ally", "enemy"]:
            for k, v in self.state["units"][side].items():
                for unit in v["positions"]:
                    bbox = unit["bounding_box"]
                    bbox[0] *= self.scale_x
                    bbox[1] *= self.scale_y
                    bbox[2] *= self.scale_x
                    bbox[3] *= self.scale_y
                    bbox_bottom = [((bbox[0] + bbox[2]) / 2), bbox[3]]
                    unit["tile_xy"] = self._get_nearest_tile(*bbox_bottom)

    def _end_of_game(self):
        if time.time() >= self.pause_until:
            time.sleep(1)
            return

        self.set_state()
        actions = self.get_actions()
        logger.info(f"Actions after end of game: {actions}")

        if self.state["screen"] == "lobby":
            logger.debug("Lobby detected, resuming normal operation.")
            return

        logger.info("Can't find Battle button, force game restart.")
        subprocess.run(
            "adb shell am force-stop com.supercell.clashroyale",
            shell=True,
        )
        time.sleep(1)
        subprocess.run(
            "adb shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp",
            shell=True,
        )
        logger.info("Waiting 10 seconds.")
        time.sleep(10)
        self.end_of_game_clicked = False

    def step(self):
        if self.end_of_game_clicked:
            self._end_of_game()

        old_screen = self.state["screen"] if self.state is not None else None
        self.set_state()
        new_screen = self.state["screen"]
        if new_screen != old_screen:
            logger.debug(f"New screen state: {new_screen}")

        if new_screen == "end_of_game":
            logger.info(
                "End of game detected. Waiting 10 seconds for battle button"
            )
            self.pause_until = time.time() + 10
            self.end_of_game_clicked = True
            time.sleep(10)
            return
        elif new_screen == "lobby":
            logger.info("In the main menu. Waiting for 1 second")
            time.sleep(1)
            return

        actions = self.get_actions()
        if not actions:
            if self.debug:
                logger.debug("No actions available. Waiting for 1 second")
            time.sleep(1)
            return

        random.shuffle(actions)
        self._preprocess()
        action = max(actions, key=lambda x: x.calculate_score(self.state))
        if action.score[0] == 0:
            time.sleep(1)
            return

        self.play_action(action)
        logger.info(
            f"Playing {action} with score {action.score}. Waiting for 1 second"
        )
        time.sleep(1)

    def run(self):
        try:
            while True:
                self.step()
        except KeyboardInterrupt:
            logger.info("Thanks for using CRBAB, see you next time!")
