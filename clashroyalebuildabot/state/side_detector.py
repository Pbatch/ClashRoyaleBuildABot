import numpy as np
from PIL import Image
from clashroyalebuildabot.data.constants import SIDE_SIZE
from clashroyalebuildabot.state.onnx_detector import OnnxDetector

class SideDetector(OnnxDetector):
    @staticmethod
    def _preprocess(image):
        image = image.resize((SIDE_SIZE, SIDE_SIZE), Image.BICUBIC)
        image = np.array(image, dtype=np.float32) / 255
        return np.expand_dims(image, axis=0)

    def _post_process(self, pred):
        return ("ally", "enemy")[np.argmax(pred[0])]

    def run(self, image):
        image = self._preprocess(image)
        pred = self._infer(image)
        return self._post_process(pred)
