import os

from clashroyalebuildabot.data.constants import (
    DATA_DIR,
    DECK_SIZE,
)
from clashroyalebuildabot.state.card_detector import CardDetector
from clashroyalebuildabot.state.debugger import Debugger
from clashroyalebuildabot.state.number_detector import NumberDetector
from clashroyalebuildabot.state.screen_detector import ScreenDetector
from clashroyalebuildabot.state.side_detector import SideDetector
from clashroyalebuildabot.state.unit_detector import UnitDetector


class Detector:
    def __init__(self, card_names, debug=False, min_conf=0.5):
        if len(card_names) != DECK_SIZE:
            raise ValueError(f"You must specify all {DECK_SIZE} of your cards")

        self.card_names = card_names
        self.debug = debug
        self.min_conf = min_conf

        self.card_detector = CardDetector(self.card_names)
        self.number_detector = NumberDetector(
            os.path.join(DATA_DIR, "numbers_S_128x32.onnx")
        )
        self.unit_detector = UnitDetector(
            os.path.join(DATA_DIR, "units_S_480x352.onnx"), self.card_names
        )
        self.screen_detector = ScreenDetector()
        self.side_detector = SideDetector(os.path.join(DATA_DIR, "side.onnx"))

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


def main():
    from clashroyalebuildabot.data.constants import Cards
    from PIL import Image

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
    detector = Detector(card_names, debug=True)
    image = Image.open("test.jpg")
    detector.run(image)


if __name__ == "__main__":
    main()
