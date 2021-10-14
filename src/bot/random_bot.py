from src.bot.bot import Bot
import random
import time
from pprint import pprint


class RandomBot(Bot):
    def run(self):
        while True:
            state = self.get_state()
            actions = self.get_actions(state)
            if actions:
                action = random.choice(actions)
                self.play_action(action)
                print(f'Playing {state["cards"][action[0] + 1]["name"]} at tile ({action[1]}, {action[2]})')
            time.sleep(5)


