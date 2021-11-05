from src.state.onnx_detector import OnnxDetector
import os
from src.data.constants import HP_CONFIG
import numpy as np
from PIL import Image
import cv2

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class HPDetector(OnnxDetector):
    IMAGE_SIZE = 64

    def _post_process(self, pred, **kwargs):
        clean_pred = {}
        for p, (name, bounding_box) in zip(pred, HP_CONFIG):
            if len(p) != 0:
                # Sort by confidence
                p = sorted(p.tolist(), key=lambda x: x[4])

                # Keep only 4 digits
                p = p[:4]

                # Sort from left-to-right
                p.sort(key=lambda x: x[0])

                hp = ''.join([str(int(i[5])) for i in p])
                confidence = [i[4] for i in p]
            else:
                confidence = []
                hp = ''
            clean_pred[name] = {'bounding_box': bounding_box,
                                'confidence': confidence,
                                'hp': hp}

        return clean_pred

    def _preprocess(self, image):
        # Resize the image
        height = self.IMAGE_SIZE // 4
        image = image.resize((self.IMAGE_SIZE, height), Image.BICUBIC)

        # Convert the image to grayscale
        image = np.array(image, dtype=np.float32)
        gray = np.dot(image[:, :, :3], [0.2125, 0.7154, 0.0721])
        for i in range(3):
            image[:, :, i] = gray

        # Add padding
        padded_image = 114 * np.ones((self.IMAGE_SIZE, self.IMAGE_SIZE, 3), dtype=np.float32)
        top = 3 * self.IMAGE_SIZE // 8
        padded_image[top: top+height, :, :] = image

        padded_image = padded_image / 255
        padded_image = np.expand_dims(padded_image.transpose(2, 0, 1), axis=0)
        return padded_image

    def run(self, image):
        # Preprocessing
        crops = np.empty((len(HP_CONFIG), 3, self.IMAGE_SIZE, self.IMAGE_SIZE), dtype=np.float32)
        for i, (_, bounding_box) in enumerate(HP_CONFIG):
            crop = image.crop(bounding_box)
            crops[i] = self._preprocess(crop)

        # Inference
        pred = self.sess.run([self.output_name], {self.input_name: crops})[0]

        # Forced post-processing
        pred = self.nms(pred)

        # Custom post-processing
        pred = self._post_process(pred)

        return pred
