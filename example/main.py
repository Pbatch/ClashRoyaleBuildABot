from clashroyalebuildabot.data.cards import Cards
from custom_bot import CustomBot
from clashroyalebuildabot.state.error_handler import adb_fix

def main():
    adb_fix()
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
    bot = CustomBot(card_names, debug=False)
    bot.run()

if __name__ == "__main__":
    main()
