import ctypes.util
import functools
import importlib.util
from typing import cast

import numpy as np
import onnxruntime as ort
from loguru import logger

CUDA = "CUDAExecutionProvider"
CPU = "CPUExecutionProvider"


def _cuda_libraries_installed() -> bool:
    """Whether cuDNN is there: from the gpu extra's pip wheels, or
    installed system-wide."""
    try:
        if importlib.util.find_spec("nvidia.cudnn") is not None:
            return True
    except ModuleNotFoundError:  # no nvidia wheels at all
        pass
    return ctypes.util.find_library("cudnn") is not None


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
    if not _cuda_libraries_installed():
        # Trying CUDA anyway would only fail, loudly, and fall back.
        logger.info(
            "The unit detector runs on the CPU. With an NVIDIA GPU, run "
            "`uv sync --extra gpu` to run it on the GPU, several times "
            "faster."
        )
        return [CPU]
    try:
        ort.preload_dlls()
    except Exception as e:
        logger.warning(f"Couldn't preload the CUDA libraries: {e}")
    return [CUDA, CPU]


class OnnxModel:
    """An ONNX model on the fastest provider there is.

    Models take one uint8 RGB batch in NHWC layout and give one output; the
    cast, scaling and any transpose are folded into the graph.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        providers = _providers()
        self.session = ort.InferenceSession(path, providers=providers)
        if CUDA in providers and CUDA not in self.session.get_providers():
            logger.warning(
                f"{path} runs on the CPU: the CUDA provider didn't load. "
                "Check that the CUDA and cuDNN libraries match "
                "onnxruntime-gpu's version."
            )
        input_ = self.session.get_inputs()[0]
        self.input_name = input_.name
        self.output_name = self.session.get_outputs()[0].name
        # (height, width) of the images it takes.
        self.input_size: tuple[int, int] = tuple(input_.shape[1:3])

    def __call__(self, batch: np.ndarray) -> np.ndarray:
        outputs = self.session.run(
            [self.output_name], {self.input_name: batch}
        )
        return cast("np.ndarray", outputs[0])
