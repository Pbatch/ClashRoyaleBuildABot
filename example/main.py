"""
A CustomBot implementation through import
"""
from random_bot import RandomBot # see custom_bot.py


def main():
    # Set required bot variables
    card_names = ['monk', 'electro_giant', 'royal_recruits', 'royal_delivery',
                  'hunter', 'electro_dragon', 'electro_spirit', 'fisherman']
    # Define an instance of CustomBot
    bot = RandomBot(card_names, debug=True)
    # and run!
    bot.run()


if __name__ == '__main__':
    main()