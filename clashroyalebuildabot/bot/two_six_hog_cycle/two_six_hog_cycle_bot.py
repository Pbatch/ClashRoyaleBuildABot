import random
import time

from loguru import logger

from clashroyalebuildabot.bot.bot import Bot
from clashroyalebuildabot.bot.two_six_hog_cycle.two_six_hog_cycle_action import (
    TwoSixHogCycleAction,
)
from clashroyalebuildabot.namespaces.cards import Cards


class TwoSixHogCycle(Bot):
    PRESET_DECK = {
        Cards.HOG_RIDER,
        Cards.THE_LOG,
        Cards.FIREBALL,
        Cards.ICE_SPIRIT,
        Cards.ICE_GOLEM,
        Cards.SKELETONS,
        Cards.CANNON,
        Cards.MUSKETEER,
    }

    def __init__(self, cards=None, debug=True):
        if cards is not None:
            raise ValueError(
                f"CustomBot uses a preset deck: {self.PRESET_DECK}."
                "Use cards=None instead."
            )
        super().__init__(self.PRESET_DECK, TwoSixHogCycleAction, debug=debug)

    def run(self):
        while True:
            # Set the state of the game
            self.set_state()
            # Obtain a list of playable actions
            actions = self.get_actions()
            if actions:
                # Shuffle the actions (because action scores might be the same)
                random.shuffle(actions)
                # Get the best action
                action = max(
                    actions, key=lambda x: x.calculate_score(self.state)
                )
                # Skip the action if it doesn't score high enough
                if action.score[0] == 0:
                    continue
                # Play the best action
                self.play_action(action)
                # Log the result
                logger.info(
                    f"Playing {action} with score {action.score} and sleeping for 1 second"
                )
                time.sleep(1.0)
