import os

import numpy as np

from clashroyalebuildabot.constants import DETECTOR_UNITS
from clashroyalebuildabot.constants import DISPLAY_HEIGHT
from clashroyalebuildabot.constants import DISPLAY_WIDTH
from clashroyalebuildabot.constants import MODELS_DIR
from clashroyalebuildabot.constants import SCREENSHOT_HEIGHT
from clashroyalebuildabot.constants import SCREENSHOT_WIDTH
from clashroyalebuildabot.constants import TILE_HEIGHT
from clashroyalebuildabot.constants import TILE_INIT_X
from clashroyalebuildabot.constants import TILE_INIT_Y
from clashroyalebuildabot.constants import TILE_WIDTH
from clashroyalebuildabot.detectors.onnx_detector import OnnxDetector
from clashroyalebuildabot.detectors.side_detector import SideDetector
from clashroyalebuildabot.namespaces.state import Position


class UnitDetector(OnnxDetector):
    MIN_CONF = 0.3
    UNIT_Y_START = 0.05
    UNIT_Y_END = 0.80

    def __init__(self, model_path, cards):
        super().__init__(model_path)
        self.cards = cards

        self.side_detector = SideDetector(
            os.path.join(MODELS_DIR, "side.onnx")
        )
        self.possible_ally_units = self._get_possible_ally_units()

    @staticmethod
    def _get_tile_xy(bbox):
        x = (bbox[0] + bbox[2]) * DISPLAY_WIDTH / (2 * SCREENSHOT_WIDTH)
        y = bbox[3] * DISPLAY_HEIGHT / SCREENSHOT_HEIGHT
        tile_x = round(((x - TILE_INIT_X) / TILE_WIDTH) - 0.5)
        tile_y = round(
            ((DISPLAY_HEIGHT - TILE_INIT_Y - y) / TILE_HEIGHT) - 0.5
        )
        return tile_x, tile_y

    def _get_possible_ally_units(self):
        possible_ally_units = set()
        for card in self.cards:
            if card.units is None:
                continue
            for unit in card.units:
                possible_ally_units.add(unit)
        return possible_ally_units

    def _calculate_side(self, image, bbox, name):
        if name not in self.possible_ally_units:
            side = "enemy"
        else:
            crop = image.crop(bbox)
            side = self.side_detector.run(crop)
        return side

    def _preprocess(self, image):
        image = image.crop(
            (
                0,
                self.UNIT_Y_START * image.height,
                image.width,
                self.UNIT_Y_END * image.height,
            )
        )
        image = self.resize(image)
        image = np.array(image, dtype=np.float32)
        image, padding = self.pad(image)
        image = np.expand_dims(image.transpose(2, 0, 1), axis=0)
        image /= 255
        return image, padding

    def _post_process(self, pred, height, image):
        pred[:, [1, 3]] *= self.UNIT_Y_END - self.UNIT_Y_START
        pred[:, [1, 3]] += self.UNIT_Y_START * height
        clean_pred = {"ally": {}, "enemy": {}}
        for p in pred:
            l, t, r, b, conf, cls = p
            bbox = (round(l), round(t), round(r), round(b))
            tile_x, tile_y = self._get_tile_xy(bbox)
            position = Position(bbox, conf, tile_x, tile_y)
            name, category, target, transport = DETECTOR_UNITS[int(cls)]
            side = self._calculate_side(image, bbox, name)
            if name not in clean_pred[side]:
                clean_pred[side][name] = {
                    "type": category,
                    "target": target,
                    "transport": transport,
                    "positions": [],
                }

            clean_pred[side][name]["positions"].append(position)
        return clean_pred

    def run(self, image):
        height, width = image.height, image.width
        np_image, padding = self._preprocess(image)
        pred = self._infer(np_image.astype(np.float16)).astype(np.float32)[0]
        pred = pred[pred[:, 4] > self.MIN_CONF]
        pred = self.fix_bboxes(pred, width, height, padding)
        pred = self._post_process(pred, height, image)
        return pred
