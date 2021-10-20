from PIL import Image, ImageDraw
from src.state.card_detector import CardDetector
from src.state.number_detector import NumberDetector
from src.state.number_detector_2 import NumberDetector2
from src.state.unit_detector import UnitDetector
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class Detector:
    def __init__(self, card_names, unit_image_size=416, number_image_size=832):
        if len(card_names) != 8:
            raise ValueError('You must specify all 8 of your cards')

        self.card_names = card_names
        self.unit_image_size = unit_image_size
        self.number_image_size = number_image_size

        self.card_detector = CardDetector(self.card_names)
        self.number_detector = NumberDetector2(self.number_image_size, f'{DATA_DIR}/digit.onnx')
        self.unit_detector = UnitDetector(self.unit_image_size, f'{DATA_DIR}/unit.onnx')

    def run(self, image, debug=False):
        state = {'units': self.unit_detector.run(image),
                 'numbers': self.number_detector.run(image),
                 'cards': self.card_detector.run(image)}

        if debug:
            d = ImageDraw.Draw(image)
            print(state)

            for v in state['units'].values():
                for i in v:
                    d.rectangle(tuple(i['bounding_box']), outline='white')

            for v in state['numbers'].values():
                d.rectangle(tuple(v['bounding_box']), outline='white')

            image.save('debug.jpg')

        return state


def main():
    from pprint import pprint
    image_path = '../data/screenshots/50.jpg'
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    detector = Detector(card_names)
    result = detector.run(Image.open(image_path), debug=True)
    pprint(result, compact=True)


if __name__ == '__main__':
    main()
