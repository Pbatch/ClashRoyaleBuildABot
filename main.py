import os
import signal
import sys

import yaml
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
from clashroyalebuildabot.constants import SRC_DIR

logger.remove()
logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    backtrace=False,
    diagnose=False,
)


def load_config():
    try:
        config_path = os.path.join(SRC_DIR, "config.yaml")
        with open(config_path, encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Can't parse config, stacktrace: {e}")

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

        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"An error occurred in main loop: {e}")
        sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
