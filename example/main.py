import threading
import time
import sys
from datetime import datetime

from clashroyalebuildabot.data.cards import Cards
from custom_bot import CustomBot
from clashroyalebuildabot.state.error_handler import adb_fix

start_time = datetime.now()


def update_terminal_title():
    while True:
        elapsed_time = datetime.now() - start_time
        hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        sys.stdout.write(f"\x1b]2;{formatted_time} | BuildABot\x07")
        sys.stdout.flush()
        time.sleep(1)


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
    title_thread = threading.Thread(target=update_terminal_title, daemon=True)
    title_thread.start()
    main()
