from datetime import datetime
import signal
import sys
import threading
import time

from loguru import logger

from clashroyalebuildabot.actions import ArchersAction
from clashroyalebuildabot.actions import BabyDragonAction
from clashroyalebuildabot.actions import CannonAction
from clashroyalebuildabot.actions import GoblinBarrelAction
from clashroyalebuildabot.actions import KnightAction
from clashroyalebuildabot.actions import MinipekkaAction
from clashroyalebuildabot.actions import MusketeerAction
from clashroyalebuildabot.actions import WitchAction
from clashroyalebuildabot.bot import Bot

start_time = datetime.now()

logger.remove()
logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    backtrace=False,
    diagnose=False,
)


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
    actions = [
        ArchersAction,
        GoblinBarrelAction,
        BabyDragonAction,
        CannonAction,
        KnightAction,
        MinipekkaAction,
        MusketeerAction,
        WitchAction,
    ]
    try:
        bot = Bot(actions=actions)
        bot.run()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    title_thread = threading.Thread(target=update_terminal_title, daemon=True)
    title_thread.start()

    main()
