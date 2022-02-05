from PIL import Image, ImageDraw
from src.state.card_detector import CardDetector
from src.state.number_detector import NumberDetector
from src.state.unit_detector import UnitDetector
from src.state.screen_detector import ScreenDetector
from src.data.constants import DATA_DIR


class Detector:
    def __init__(self, card_names):
        if len(card_names) != 8:
            raise ValueError('You must specify all 8 of your cards')

        self.card_names = card_names

        self.card_detector = CardDetector(self.card_names)
        self.number_detector = NumberDetector(f'{DATA_DIR}/number.onnx')
        self.unit_detector = UnitDetector(f'{DATA_DIR}/unit.onnx')
        self.screen_detector = ScreenDetector()

    def run(self, image, debug=False):
        state = {'units': self.unit_detector.run(image),
                 'numbers': self.number_detector.run(image),
                 'cards': self.card_detector.run(image),
                 'screen': self.screen_detector.run(image)}

        if debug:
            d = ImageDraw.Draw(image)

            for k, v in state['numbers'].items():
                d.rectangle(tuple(v['bounding_box']))
                d.text((v['bounding_box'][0], v['bounding_box'][3] + 2), text=str(v['number']))

            for k, v in state['units'].items():
                for i in v:
                    d.rectangle(tuple(i['bounding_box']))
                    d.text((i['bounding_box'][0], i['bounding_box'][3] + 2), text=k)
            image.save('debug.jpg')

        return state


def main():
    from pprint import pprint

    image_path = '../../screenshots/19.jpg'
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']

    detector = Detector(card_names)

    result = detector.run(Image.open(image_path), debug=True)

    pprint(result, compact=True)
    # pprint(result['hp'], compact=True)


if __name__ == '__main__':
    main()
