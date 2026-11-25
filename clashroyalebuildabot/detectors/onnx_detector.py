import functools
from typing import cast

import numpy as np
import onnxruntime as ort
from loguru import logger

from clashroyalebuildabot.utils import image as image_utils

CUDA = "CUDAExecutionProvider"
CPU = "CPUExecutionProvider"


@functools.cache
def _providers() -> list[str]:
    """The execution providers to use, fastest first.

    onnxruntime-gpu can't find the CUDA and cuDNN libraries installed as
    pip wheels (nvidia-cublas and friends) on its own, so they're loaded
    first. Without them, the CUDA provider fails to load and onnxruntime
    quietly falls back to the CPU, which is about ten times slower.
    """
    available = ort.get_available_providers()
    if CUDA not in available:
        return [CPU]
    try:
        ort.preload_dlls()
    except Exception as e:
        logger.warning(f"Couldn't preload the CUDA libraries: {e}")
    return [CUDA, CPU]


class OnnxDetector:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

        providers = _providers()
        self.sess = ort.InferenceSession(
            self.model_path,
            providers=providers,
        )
        if CUDA in providers and CUDA not in self.sess.get_providers():
            logger.warning(
                f"{self.model_path} runs on the CPU: the CUDA provider "
                "didn't load. Check that the CUDA and cuDNN libraries "
                "match onnxruntime-gpu's version."
            )
        self.output_name = self.sess.get_outputs()[0].name

        # Models take uint8 RGB in NHWC layout; the cast, scaling and any
        # transpose are folded into the graph.
        input_ = self.sess.get_inputs()[0]
        self.input_name = input_.name
        self.model_height, self.model_width = input_.shape[1:3]

    def resize(self, x: np.ndarray) -> np.ndarray:
        ratio = x.shape[0] / x.shape[1]
        if ratio > self.model_height / self.model_width:
            height = self.model_height
            width = int(self.model_height / ratio)
        else:
            width = self.model_width
            height = int(self.model_width * ratio)

        return image_utils.resize(x, (width, height))

    def pad(self, x: np.ndarray) -> tuple[np.ndarray, list[int]]:
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

    def resize_and_pad(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, list[int]]:
        return self.pad(self.resize(image))

    def fix_bboxes(
        self, x: np.ndarray, width: int, height: int, padding: list[int]
    ) -> np.ndarray:
        x[:, [0, 2]] -= padding[0]
        x[:, [1, 3]] -= padding[2]
        x[..., [0, 2]] *= width / (self.model_width - padding[0] - padding[1])
        x[..., [1, 3]] *= height / (
            self.model_height - padding[2] - padding[3]
        )
        return x

    def _infer(self, x: np.ndarray) -> np.ndarray:
        outputs = self.sess.run([self.output_name], {self.input_name: x})
        return cast("np.ndarray", outputs[0])

    def run(self, image: np.ndarray) -> object:

        raise NotImplementedError
