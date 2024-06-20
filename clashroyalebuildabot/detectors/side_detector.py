import numpy as np
from PIL import Image

from clashroyalebuildabot.detectors.onnx_detector import OnnxDetector


class SideDetector(OnnxDetector):
    SIDE_SIZE = 16

    def _preprocess(self, image):
        image = image.resize(
            (self.SIDE_SIZE, self.SIDE_SIZE), Image.Resampling.BICUBIC
        )
        image = np.array(image, dtype=np.float32) / 255
        return np.expand_dims(image, axis=0)

    @staticmethod
    def _post_process(pred):
        return ("ally", "enemy")[np.argmax(pred[0])]

    def run(self, image):
        image = self._preprocess(image)
        pred = self._infer(image)
        return self._post_process(pred)
