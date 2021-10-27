from src.state.onnx_detector import OnnxDetector
import os
from src.data.constants import UNITS

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class UnitDetector(OnnxDetector):
    def _post_process(self, pred, **kwargs):
        clean_pred = {}
        for p in pred:
            name = UNITS[round(p[5])]
            info = {'bounding_box': p[:4].tolist(),
                    'confidence': p[4]}
            if name in clean_pred:
                clean_pred[name].append(info)
            else:
                clean_pred[name] = [info]
        return clean_pred
