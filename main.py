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
from clashroyalebuildabot.gui.main_window import MainWindow
from clashroyalebuildabot.gui.utils import load_config
from clashroyalebuildabot.utils.logger import setup_logger


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
        setup_logger(window)

        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
