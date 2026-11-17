import os

from loguru import logger

from clashroyalebuildabot.constants import DECK_SIZE, MODELS_DIR
from clashroyalebuildabot.detectors.card_detector import CardDetector
from clashroyalebuildabot.detectors.number_detector import NumberDetector
from clashroyalebuildabot.detectors.screen_detector import ScreenDetector
from clashroyalebuildabot.detectors.unit_detector import UnitDetector
from clashroyalebuildabot.namespaces import State
from clashroyalebuildabot.utils.error_handling import WikifiedError


class Detector:
    def __init__(self, cards, screen_config=None):
        if len(cards) != DECK_SIZE:
            raise WikifiedError(
                "005",
                f"Your deck must have {DECK_SIZE} cards, "
                f"but {len(cards)} were given",
            )

        self.cards = cards

        self.card_detector = CardDetector(self.cards)
        self.number_detector = NumberDetector()
        self.unit_detector = UnitDetector(
            os.path.join(MODELS_DIR, "units_M_480x352.onnx"), self.cards
        )
        self.screen_detector = ScreenDetector.from_config(screen_config)

    def run(self, image) -> State | None:
        """
        Detect the state of one screenshot. Returns None if detection fails,
        and the bot moves on to the next screenshot. Retrying the same image
        would fail the same way, since detection is deterministic.
        """
        logger.debug("Setting state...")
        try:
            cards, ready = self.card_detector.run(image)
            allies, enemies = self.unit_detector.run(image)
            numbers = self.number_detector.run(image)
            screen = self.screen_detector.run(image)
        except Exception:
            logger.exception("Detection failed, skipping this screenshot.")
            return None
        return State(allies, enemies, numbers, cards, ready, screen)

    def close(self):
        self.screen_detector.close()
