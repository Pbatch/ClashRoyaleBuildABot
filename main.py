from src.bot.pete.pete_bot import PeteBot


def main():
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    bot = PeteBot(card_names)
    bot.run()


if __name__ == '__main__':
    main()