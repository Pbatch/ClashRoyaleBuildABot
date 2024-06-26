import os

from clashroyalebuildabot.constants import MODELS_DIR
from clashroyalebuildabot.debugger import Debugger
from clashroyalebuildabot.detectors.card_detector import CardDetector
from clashroyalebuildabot.detectors.number_detector import NumberDetector
from clashroyalebuildabot.detectors.screen_detector import ScreenDetector
from clashroyalebuildabot.detectors.unit_detector import UnitDetector
from clashroyalebuildabot.namespaces import State


class Detector:
    DECK_SIZE = 8

    def __init__(self, cards, debug=False):
        if len(cards) != self.DECK_SIZE:
            raise ValueError(
                f"You must specify all {self.DECK_SIZE} of your cards"
            )

        self.cards = cards
        self.debug = debug

        self.card_detector = CardDetector(self.cards)
        self.number_detector = NumberDetector(
            os.path.join(MODELS_DIR, "numbers_S_128x32.onnx")
        )
        self.unit_detector = UnitDetector(
            os.path.join(MODELS_DIR, "units_M_480x352.onnx"), self.cards
        )
        self.screen_detector = ScreenDetector()

        self.debugger = None
        if self.debug:
            self.debugger = Debugger()

    def run(self, image):
        cards, ready = self.card_detector.run(image)
        units = self.unit_detector.run(image)
        numbers = self.number_detector.run(image)
        screen = self.screen_detector.run(image)

        state = State(
            units["enemy"], units["ally"], numbers, cards, ready, screen
        )
        if self.debugger is not None:
            self.debugger.run(image, state)

        return state
