from src.bot import Bot
import random
import time


class RandomBot(Bot):
    def run(self):
        while True:
            state = self.get_state()
            actions = self.get_actions(state)
            if actions:
                action = random.choice(actions)
                self.play_action(action)
                print(f'elixir:{state["elixir"]}')
                print(f'action:{action}')
            time.sleep(1)

