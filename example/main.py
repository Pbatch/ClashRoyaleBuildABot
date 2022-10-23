"""
A CustomBot implementation through import
"""
from custom_bot import CustomBot # see custom_bot.py


def main():
    # Set required bot variables
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    # Define an instance of CustomBot
    bot = CustomBot(card_names, debug=True, device_name="localhost:5555")
    # and run!
    bot.run()


if __name__ == '__main__':
    main()