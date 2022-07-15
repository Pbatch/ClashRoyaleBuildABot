import os

from PIL import ImageDraw, ImageFont

from clashroyalebuildabot.state.card_detector import CardDetector
from clashroyalebuildabot.state.number_detector import NumberDetector
from clashroyalebuildabot.state.side_detector import SideDetector
from clashroyalebuildabot.state.unit_detector import UnitDetector
from clashroyalebuildabot.state.screen_detector import ScreenDetector
from clashroyalebuildabot.data.constants import DATA_DIR, SCREENSHOTS_DIR, CARD_CONFIG, DECK_SIZE, LABELS_DIR, UNITS


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
            os.makedirs(LABELS_DIR, exist_ok=True)
            self.font = ImageFont.load_default()

        self.card_detector = CardDetector(self.card_names)
        self.number_detector = NumberDetector(os.path.join(DATA_DIR, 'number.onnx'))
        self.unit_detector = UnitDetector(os.path.join(DATA_DIR, 'unit.onnx'), self.card_names)
        self.screen_detector = ScreenDetector()
        self.side_detector = SideDetector(os.path.join(DATA_DIR, 'side.onnx'))

    def _draw_text(self, d, bbox, text):
        text_width, text_height = self.font.getsize(text)
        y_offset = 5
        x = (bbox[0] + bbox[2] - text_width) / 2
        y = bbox[1] - y_offset

        mid_x = (bbox[0] + bbox[2]) / 2
        text_bbox = (mid_x - text_width/2 - 5,
                     bbox[1] - y_offset - text_height,
                     mid_x + text_width / 2 + 5,
                     bbox[1] - y_offset)
        d.rectangle(text_bbox,
                    fill='black')
        d.rectangle(tuple(bbox))
        d.text((x, y - text_height), text=text)

    def run(self, image):
        state = {'units': self.unit_detector.run(image),
                 'numbers': self.number_detector.run(image),
                 'cards': self.card_detector.run(image),
                 'screen': self.screen_detector.run(image)}

        if self.debug:
            d = ImageDraw.Draw(image)
            width, height = image.width, image.height
            labels = []

            for k, v in state['numbers'].items():
                d.rectangle(tuple(v['bounding_box']))
                self._draw_text(d, v['bounding_box'], str(v['number']))

            for side in ['ally', 'enemy']:
                for unit_name, v in state['units'][side].items():
                    for i in v['positions']:
                        bbox = i['bounding_box']
                        # Save the bboxes in the YOLOv5 format (unit_id, center_x, center_y, width, height)
                        # where center_x, center_y, width, height are scaled to 0-1
                        yolov5_bbox = [(bbox[0] + bbox[2]) / (2 * width),
                                       (bbox[1] + bbox[3]) / (2 * height),
                                       (bbox[2] - bbox[0]) / width,
                                       (bbox[3] - bbox[1]) / height]
                        labels.append([unit_name, *yolov5_bbox])
                        self._draw_text(d, bbox, unit_name)

            for card, position in zip(state['cards'], CARD_CONFIG):
                d.rectangle(tuple(position))
                self._draw_text(d, position, card['name'])

            n_screenshots = len(os.listdir(SCREENSHOTS_DIR))
            n_labels = len(os.listdir(LABELS_DIR))
            basename = max(n_labels, n_screenshots) + 1
            image_save_path = os.path.join(SCREENSHOTS_DIR, f"{basename}.jpg")
            image.save(image_save_path)

            label_save_path = os.path.join(LABELS_DIR, f"{basename}.txt")
            with open(label_save_path, 'w') as f:
                label_string = '\n'.join([' '.join(map(str, label)) for label in labels])
                f.write(label_string)

        return state
