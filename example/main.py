"""
A CustomBot implementation through import
"""

from clashroyalebuildabot.data.cards import Cards
from custom_bot import CustomBot  # see custom_bot.py
from clashroyalebuildabot.state.error_handler import adb_fix


def main():
    adb_fix()
    # Set required bot variables
    card_names = [
        Cards.MINIONS,
        Cards.ARCHERS,
        Cards.ARROWS,
        Cards.GIANT,
        Cards.MINIPEKKA,
        Cards.FIREBALL,
        Cards.KNIGHT,
        Cards.MUSKETEER,
    ]
    # Define an instance of CustomBot
    bot = CustomBot(card_names, debug=False)
    # and run!
    bot.run()


if __name__ == "__main__":
    main()
