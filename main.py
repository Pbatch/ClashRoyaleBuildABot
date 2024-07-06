from datetime import datetime
import signal
import sys
import threading
import time

from clashroyalebuildabot.actions.archers_action import ArchersAction
from clashroyalebuildabot.actions.fireball_action import FireballAction
from clashroyalebuildabot.actions.giant_action import GiantAction
from clashroyalebuildabot.actions.knight_action import KnightAction
from clashroyalebuildabot.actions.minions_action import MinionsAction
from clashroyalebuildabot.actions.minipekka_action import MinipekkaAction
from clashroyalebuildabot.actions.musketeer_action import MusketeerAction
from clashroyalebuildabot.actions.zap_action import ZapAction
from clashroyalebuildabot.bot import Bot

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
    actions = {
        ArchersAction,
        ZapAction,
        FireballAction,
        GiantAction,
        KnightAction,
        MinionsAction,
        MinipekkaAction,
        MusketeerAction,
    }
    bot = Bot(actions=actions, debug=False)
    bot.run()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    title_thread = threading.Thread(target=update_terminal_title, daemon=True)
    title_thread.start()

    main()
