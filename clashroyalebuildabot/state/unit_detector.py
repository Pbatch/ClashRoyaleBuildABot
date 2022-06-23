
import numpy as np
from PIL import Image

from clashroyalebuildabot.data.constants import UNITS, UNIT_Y_END, UNIT_Y_START, UNIT_SIZE, DATA_DIR
from clashroyalebuildabot.state.onnx_detector import OnnxDetector


class UnitDetector(OnnxDetector):
    def __init__(self, model_path):
        super().__init__(model_path)

        self.card_to_info = self._set_card_to_info()

    @staticmethod
    def _set_card_to_info():
        card_to_info = {}
        with open(f'{DATA_DIR}/cards.csv') as f:
            for line in f:
                name, _, _, type_, target, transport = line.strip().replace('"', '').split(',')
                card_to_info[name] = {'type': type_, 'target': target, 'transport': transport}
        return card_to_info

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
        height, width = kwargs['height'], kwargs['width']
        pred[:, [1, 3]] *= UNIT_Y_END - UNIT_Y_START
        pred[:, [1, 3]] += UNIT_Y_START * height

        clean_pred = {}
        for p in pred:
            name = UNITS[round(p[5])]
            info = {'bounding_box': [round(i) for i in p[:4]],
                    'confidence': p[4]}
            if name in clean_pred:
                clean_pred[name]['positions'].append(info)
            else:
                key = name.replace('ally_', '').replace('enemy_', '').replace('muskateer', 'musketeer')
                try:
                    clean_pred[name] = self.card_to_info[key]
                except KeyError:
                    print(f'Could not find metadata for key "{key}"')
                    clean_pred[name] = {'type': '', 'target': '', 'transport': ''}
                clean_pred[name]['positions'] = [info]
        return clean_pred

    def run(self, image):
        height, width = image.height, image.width

        # Preprocessing
        image = self._preprocess(image)

        # Inference
        pred = self.sess.run([self.output_name], {self.input_name: image})[0]

        # Forced post-processing
        pred = np.array(self.nms(pred)[0])
        pred[:, [0, 2]] *= width / UNIT_SIZE
        pred[:, [1, 3]] *= height / UNIT_SIZE

        # Custom post-processing
        pred = self._post_process(pred, width=width, height=height)

        return pred
