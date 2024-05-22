"""
A CustomBot implementation through import
"""
from custom_bot import CustomBot # see custom_bot.py
from clashroyalebuildabot.state.error_handler import adb_fix


def main():
    adb_fix()
    # Set required bot variables
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    # Define an instance of CustomBot
    bot = CustomBot(card_names, debug=False)
    # and run!
    bot.run()


if __name__ == '__main__':
    main()
