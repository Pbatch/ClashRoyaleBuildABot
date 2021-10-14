from src.bot.random_bot import RandomBot


def main():
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    bot = RandomBot(card_names)
    bot.run()


if __name__ == '__main__':
    main()