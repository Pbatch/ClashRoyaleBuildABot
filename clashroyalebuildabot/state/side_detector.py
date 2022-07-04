import numpy as np
from PIL import Image

from clashroyalebuildabot.data.constants import SIDE_SIZE
from clashroyalebuildabot.state.onnx_detector import OnnxDetector


class SideDetector(OnnxDetector):
    def _preprocess(self, image):
        image = image.resize((SIDE_SIZE, SIDE_SIZE), Image.BICUBIC)
        image = np.array(image, dtype=np.float32)
        image = image / 255
        image = np.expand_dims(image, axis=0)
        return image

    def _post_process(self, pred):
        return ('ally', 'enemy')[np.argmax(pred[0])]

    def run(self, image):
        # Preprocessing
        image = self._preprocess(image)

        # Inference
        pred = self.sess.run([self.output_name], {self.input_name: image})[0]

        # Postprocessing
        side = self._post_process(pred)

        return side
