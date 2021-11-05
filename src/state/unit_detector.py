from src.state.onnx_detector import OnnxDetector
import os
from src.data.constants import UNITS
import numpy as np
from PIL import Image

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class UnitDetector(OnnxDetector):
    IMAGE_SIZE = 832

    def _post_process(self, pred, **kwargs):
        clean_pred = {}
        for p in pred:
            name = UNITS[round(p[5])]
            info = {'bounding_box': [round(i) for i in p[:4]],
                    'confidence': p[4]}
            if name in clean_pred:
                clean_pred[name].append(info)
            else:
                clean_pred[name] = [info]
        return clean_pred

    def _preprocess(self, image):
        """
        Preprocess an image
        """
        image = image.resize((self.IMAGE_SIZE, self.IMAGE_SIZE), Image.BICUBIC)
        image = np.array(image, dtype=np.float32)
        image = np.expand_dims(image.transpose(2, 0, 1), axis=0)
        image = image / 255
        return image

    def run(self, image):
        height, width = image.height, image.width

        # Preprocessing
        image = self._preprocess(image)

        # Inference
        pred = self.sess.run([self.output_name], {self.input_name: image})[0]

        # Forced post-processing
        pred = np.array(self.nms(pred)[0])
        pred[:, [0, 2]] *= width / self.IMAGE_SIZE
        pred[:, [1, 3]] *= height / self.IMAGE_SIZE

        # Custom post-processing
        pred = self._post_process(pred)

        return pred
