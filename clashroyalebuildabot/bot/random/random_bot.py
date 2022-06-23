from clashroyalebuildabot.bot.bot import Bot
import time
import random


class RandomBot(Bot):
    def run(self):
        while True:
            # Set the state of the game
            self.set_state()
            # Obtain a list of playable actions
            actions = self.get_actions()
            if actions:
                # Choose a random action
                action = random.choice(actions)
                # Play the given action
                self.play_action(action)
                # Log the result
                print(f'Playing {action}')
            time.sleep(3)
