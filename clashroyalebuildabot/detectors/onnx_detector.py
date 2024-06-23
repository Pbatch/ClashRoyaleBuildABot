import numpy as np
import onnxruntime as ort


class OnnxDetector:
    def __init__(self, model_path):
        self.model_path = model_path

        providers = list(
            set(ort.get_available_providers())
            & {"CUDAExecutionProvider", "CPUExecutionProvider"}
        )
        self.sess = ort.InferenceSession(
            self.model_path,
            providers=providers,
        )
        self.output_name = self.sess.get_outputs()[0].name

        input_ = self.sess.get_inputs()[0]
        self.input_name = input_.name
        self.model_height, self.model_width = input_.shape[2:]

    def resize(self, x):
        ratio = x.height / x.width
        if ratio > self.model_height / self.model_width:
            height = self.model_height
            width = int(self.model_height / ratio)
        else:
            width = self.model_width
            height = int(self.model_width * ratio)

        x = x.resize((width, height))
        return x

    def pad(self, x):
        height, width = x.shape[:2]
        dx = self.model_width - width
        dy = self.model_height - height
        pad_right = dx // 2
        pad_left = dx - pad_right
        pad_bottom = dy // 2
        pad_top = dy - pad_bottom
        padding = [pad_left, pad_right, pad_top, pad_bottom]
        x = np.pad(
            x,
            ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)),
            mode="constant",
            constant_values=114,
        )
        return x, padding

    def resize_pad_transpose_and_scale(self, image):
        image = self.resize(image)
        image = np.array(image, dtype=np.float16)
        image, padding = self.pad(image)
        image = image.transpose(2, 0, 1)
        image /= 255
        return image, padding

    def fix_bboxes(self, x, width, height, padding):
        x[:, [0, 2]] -= padding[0]
        x[:, [1, 3]] -= padding[2]
        x[..., [0, 2]] *= width / (self.model_width - padding[0] - padding[1])
        x[..., [1, 3]] *= height / (
            self.model_height - padding[2] - padding[3]
        )
        return x

    def _infer(self, x):
        return self.sess.run([self.output_name], {self.input_name: x})[0]

    def run(self, image):
        raise NotImplementedError
