import random
import subprocess
import time

from loguru import logger

from clashroyalebuildabot.bot import Bot
from clashroyalebuildabot.data.cards import Cards
from clashroyalebuildabot.data.constants import (
    DISPLAY_WIDTH,
    SCREENSHOT_WIDTH,
    DISPLAY_HEIGHT,
    SCREENSHOT_HEIGHT,
)
from custom_action import CustomAction


class CustomBot(Bot):
    def __init__(self, card_names, debug=False):
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
        if set(card_names) != preset_deck:
            raise ValueError(
                f"You must use the preset deck with cards {preset_deck} for CustomBot"
            )
        super().__init__(card_names, CustomAction, debug=debug)
        self.end_of_game_clicked = False
        self.pause_until = 0

    def _preprocess(self):
        for side in ["ally", "enemy"]:
            for k, v in self.state["units"][side].items():
                for unit in v["positions"]:
                    bbox = unit["bounding_box"]
                    bbox[0] *= DISPLAY_WIDTH / SCREENSHOT_WIDTH
                    bbox[1] *= DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
                    bbox[2] *= DISPLAY_WIDTH / SCREENSHOT_WIDTH
                    bbox[3] *= DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
                    bbox_bottom = [((bbox[0] + bbox[2]) / 2), bbox[3]]
                    unit["tile_xy"] = self._get_nearest_tile(*bbox_bottom)

    def run(self):
        try:
            while True:
                if self.end_of_game_clicked:
                    if time.time() > self.pause_until:
                        if not any(
                            action.name == "Battle"
                            for action in self.get_actions()
                        ):
                            logger.info(
                                "Can't find Battle button, force game restart."
                            )
                            subprocess.run(
                                "adb shell am force-stop com.supercell.clashroyale",
                                shell=True,
                            )
                            time.sleep(1)
                            subprocess.run(
                                "adb shell am start -n com.supercell.clashroyale/com.supercell.titan.GameApp",
                                shell=True,
                            )

                            logger.info("Waiting 10 seconds...")
                            time.sleep(10)

                        self.end_of_game_clicked = False
                    else:
                        time.sleep(1.0)
                        continue

                self.set_state()

                if self.state["screen"] == "end_of_game":
                    logger.info(
                        "End of game detected. Waiting 10 seconds for battle button..."
                    )
                    self.pause_until = time.time() + 10
                    self.end_of_game_clicked = True
                    time.sleep(10)

                actions = self.get_actions()

                if not actions:
                    if self.debug:
                        logger.debug(
                            "No actions available. Waiting for 1 second..."
                        )
                    time.sleep(1.0)
                    continue
                elif self.state["screen"] != "lobby":
                    random.shuffle(actions)
                    self._preprocess()
                    action = max(
                        actions, key=lambda x: x.calculate_score(self.state)
                    )
                    if action.score[0] == 0:
                        continue
                    self.play_action(action)
                    logger.info(
                        f"Playing {action} with score {action.score} and sleeping for 1 second"
                    )
                    time.sleep(1.0)
                else:
                    logger.info(
                        "In the main menu or no actions available. Waiting for 1 second..."
                    )
                    time.sleep(1.0)

        except KeyboardInterrupt:
            logger.info(
                "KeyboardInterrupt detected. Exiting bot gracefully."
            )  # Log the interruption
