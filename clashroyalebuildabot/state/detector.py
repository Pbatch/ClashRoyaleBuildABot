import os

from PIL import ImageDraw, ImageFont

from clashroyalebuildabot.state.card_detector import CardDetector
from clashroyalebuildabot.state.number_detector import NumberDetector
from clashroyalebuildabot.state.side_detector import SideDetector
from clashroyalebuildabot.state.unit_detector import UnitDetector
from clashroyalebuildabot.state.screen_detector import ScreenDetector
from clashroyalebuildabot.data.constants import DATA_DIR, SCREENSHOTS_DIR, CARD_CONFIG, DECK_SIZE


class Detector:
    def __init__(self, card_names, debug=False, min_conf=0.5):
        if len(card_names) != DECK_SIZE:
            raise ValueError(f'You must specify all {DECK_SIZE} of your cards')

        self.card_names = card_names
        self.debug = debug
        self.min_conf = min_conf

        self.font = None
        if self.debug:
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            self.font = ImageFont.load_default()

        self.card_detector = CardDetector(self.card_names)
        self.number_detector = NumberDetector(os.path.join(DATA_DIR, 'number.onnx'))
        self.unit_detector = UnitDetector(os.path.join(DATA_DIR, 'unit.onnx'), self.card_names)
        self.screen_detector = ScreenDetector()
        self.side_detector = SideDetector(os.path.join(DATA_DIR, 'side.onnx'))

    def _draw_text(self, d, bbox, text):
        text_width, text_height = self.font.getsize(text)
        x = (bbox[0] + bbox[2] - text_width) / 2
        y = bbox[3] + 2
        for xy in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            d.text(xy, text=text, fill='black')
        d.text((x, y), text=text)

    def run(self, image):
        state = {'units': self.unit_detector.run(image),
                 'numbers': self.number_detector.run(image),
                 'cards': self.card_detector.run(image),
                 'screen': self.screen_detector.run(image)}

        if self.debug:
            d = ImageDraw.Draw(image)

            for k, v in state['numbers'].items():
                d.rectangle(tuple(v['bounding_box']))
                self._draw_text(d, v['bounding_box'], str(v['number']))

            for side in ['ally', 'enemy']:
                for k, v in state['units'][side].items():
                    for i in v['positions']:
                        if i['confidence'] > self.min_conf:
                            d.rectangle(tuple(i['bounding_box']))
                            self._draw_text(d, i['bounding_box'], f'{side}_{k}')

            for card, position in zip(state['cards'], CARD_CONFIG):
                d.rectangle(tuple(position))
                self._draw_text(d, position, card['name'])

            save_path = os.path.join(SCREENSHOTS_DIR, f"{len(os.listdir(SCREENSHOTS_DIR)) + 1}.jpg")
            image.save(save_path)

        return state