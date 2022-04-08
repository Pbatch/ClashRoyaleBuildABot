from src.bot.standard.standard_bot import StandardBot


def main():
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    bot = StandardBot(card_names, debug=True)
    bot.run()


if __name__ == '__main__':
    main()