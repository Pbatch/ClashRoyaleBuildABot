import os

from clashroyalebuildabot.constants import MODELS_DIR
from clashroyalebuildabot.state.card_detector import CardDetector
from clashroyalebuildabot.state.debugger import Debugger
from clashroyalebuildabot.state.number_detector import NumberDetector
from clashroyalebuildabot.state.screen_detector import ScreenDetector
from clashroyalebuildabot.state.unit_detector import UnitDetector


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
        state = {
            "units": self.unit_detector.run(image),
            "numbers": self.number_detector.run(image),
            "cards": self.card_detector.run(image),
            "screen": self.screen_detector.run(image),
        }

        if self.debugger is not None:
            self.debugger.run(image, state)

        return state
