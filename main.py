import logging
import signal
import sys

from loguru import logger
from PyQt6.QtWidgets import QApplication

from clashroyalebuildabot.actions import ArchersAction
from clashroyalebuildabot.actions import BabyDragonAction
from clashroyalebuildabot.actions import CannonAction
from clashroyalebuildabot.actions import GoblinBarrelAction
from clashroyalebuildabot.actions import KnightAction
from clashroyalebuildabot.actions import MinipekkaAction
from clashroyalebuildabot.actions import MusketeerAction
from clashroyalebuildabot.actions import WitchAction
from clashroyalebuildabot.bot import Bot
from clashroyalebuildabot.gui.log_handler import QTextEditLogger
from clashroyalebuildabot.gui.main_window import MainWindow
from clashroyalebuildabot.gui.utils import load_config

logger.remove()
logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    backtrace=False,
    diagnose=False,
)


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
        config = load_config()

        app = QApplication(sys.argv)
        window = MainWindow(config, actions)

        log_handler = QTextEditLogger(window.log_display)
        log_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.add(log_handler)

        window.show()
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        sys.exit(1)


main()
