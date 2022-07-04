import os

import numpy as np
from PIL import Image

from clashroyalebuildabot.data.constants import UNITS, UNIT_Y_END, UNIT_Y_START, UNIT_SIZE, DATA_DIR, CARD_TO_UNITS
from clashroyalebuildabot.state.onnx_detector import OnnxDetector
from clashroyalebuildabot.state.side_detector import SideDetector


class UnitDetector(OnnxDetector):
    def __init__(self, model_path, card_names):
        super().__init__(model_path)
        self.card_names = card_names

        self.card_to_info = self._set_card_to_info()
        self.possible_ally_units = self._set_possible_ally_units()

        self.side_detector = SideDetector(os.path.join(DATA_DIR, 'side.onnx'))

    @staticmethod
    def _set_card_to_info():
        card_to_info = {}
        with open(os.path.join(DATA_DIR, 'cards.csv')) as f:
            for line in f:
                name, _, _, type_, target, transport = line.strip().replace('"', '').split(',')
                card_to_info[name] = {'type': type_, 'target': target, 'transport': transport}
        return card_to_info

    def _set_possible_ally_units(self):
        possible_ally_units = []
        for name in self.card_names:
            if name in CARD_TO_UNITS:
                possible_ally_units.extend(CARD_TO_UNITS[name])
            elif self.card_to_info[name]['type'] == 'troop':
                possible_ally_units.append(name)
        return set(possible_ally_units)

    def _calculate_side(self, image, bbox, name):
        if name not in self.possible_ally_units:
            # Assume that the unit detection is correct, and say that the unit is an enemy
            side = 'enemy'
        else:
            crop = image.crop(bbox)
            side = self.side_detector.run(crop)

        return side

    @staticmethod
    def _preprocess(image):
        """
        Preprocess an image
        """
        image = image.crop((0, UNIT_Y_START * image.height, image.width, UNIT_Y_END * image.height))
        image = image.resize((UNIT_SIZE, UNIT_SIZE), Image.BICUBIC)
        image = np.array(image, dtype=np.float32)
        image = np.expand_dims(image.transpose(2, 0, 1), axis=0)
        image = image / 255
        return image

    def _post_process(self, pred, **kwargs):
        height, width, image = kwargs['height'], kwargs['width'], kwargs['image']
        pred[:, [1, 3]] *= UNIT_Y_END - UNIT_Y_START
        pred[:, [1, 3]] += UNIT_Y_START * height

        clean_pred = {'ally': {}, 'enemy': {}}
        for p in pred:
            name = UNITS[round(p[5])]
            bbox = [round(i) for i in p[:4]]
            info = {'bounding_box': bbox,
                    'confidence': p[4]}
            side = self._calculate_side(image, bbox, name)
            if name not in clean_pred[side]:
                try:
                    clean_pred[side][name] = self.card_to_info[name]
                except KeyError:
                    print(f'Could not find metadata for key "{name}"')
                    clean_pred[side][name] = {'type': '', 'target': '', 'transport': ''}
                clean_pred[side][name]['positions'] = []
            clean_pred[side][name]['positions'].append(info)
        return clean_pred

    def run(self, image):
        height, width = image.height, image.width

        # Preprocessing
        np_image = self._preprocess(image)

        # Inference
        pred = self.sess.run([self.output_name], {self.input_name: np_image})[0]

        # Forced post-processing
        pred = np.array(self.nms(pred)[0])
        pred[:, [0, 2]] *= width / UNIT_SIZE
        pred[:, [1, 3]] *= height / UNIT_SIZE

        # Custom post-processing
        pred = self._post_process(pred, width=width, height=height, image=image)

        return pred
