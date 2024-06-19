import numpy as np

from clashroyalebuildabot.constants import ELIXIR_BOUNDING_BOX
from clashroyalebuildabot.constants import KING_HP
from clashroyalebuildabot.constants import KING_LEVEL_2_X
from clashroyalebuildabot.constants import NUMBER_CONFIG
from clashroyalebuildabot.constants import NUMBER_HEIGHT
from clashroyalebuildabot.constants import NUMBER_WIDTH
from clashroyalebuildabot.state.onnx_detector import OnnxDetector


class NumberDetector(OnnxDetector):
    MIN_CONF = 0.5

    @staticmethod
    def _calculate_elixir(image):
        crop = image.crop(ELIXIR_BOUNDING_BOX)
        std = np.array(crop).std(axis=(0, 2))
        rolling_std = np.convolve(std, np.ones(10) / 10, mode="valid")
        change_points = np.nonzero(rolling_std < 50)[0]
        return (change_points[0] + 10) // 25 if len(change_points) > 0 else 10

    @staticmethod
    def _clean_king_levels(pred):
        for side in ["ally", "enemy"]:
            vals = [pred[f"{side}_king_level{s}"] for s in ["", "_2"]]
            pred[f"{side}_king_level"] = max(
                vals, key=lambda x: np.prod(x["confidence"])
            )
            del pred[f"{side}_king_level_2"]
        return pred

    @staticmethod
    def _clean_king_hp(pred):
        for side in ["ally", "enemy"]:
            valid_bounding_box = (
                pred[f"{side}_king_level"]["bounding_box"][0] == KING_LEVEL_2_X
            )
            valid_king_level = pred[f"{side}_king_level"]["number"] <= 14
            if valid_bounding_box and valid_king_level:
                pred[f"{side}_king_hp"]["number"] = KING_HP[
                    pred[f"{side}_king_level"]["number"] - 1
                ]
                pred[f"{side}_king_hp"]["confidence"] = pred[
                    f"{side}_king_level"
                ]["confidence"]
        return pred

    def _calculate_confidence_and_number(self, pred):
        pred = [p for p in pred.tolist() if p[4] > self.MIN_CONF][:4]
        pred.sort(key=lambda x: x[0])
        confidence = [p[4] for p in pred]
        number = "".join([str(int(p[5])) for p in pred])
        return confidence if confidence else [-1], (
            int(number) if number else -1
        )

    def _post_process(self, pred):
        clean_pred = {}
        for p, (name, x, y) in zip(pred, NUMBER_CONFIG):
            confidence, number = self._calculate_confidence_and_number(p)
            clean_pred[name] = {
                "bounding_box": [x, y, x + NUMBER_WIDTH, y + NUMBER_HEIGHT],
                "confidence": confidence,
                "number": number,
            }
            if name == "ally_king_level_2":
                clean_pred = self._clean_king_levels(clean_pred)
        clean_pred = self._clean_king_hp(clean_pred)
        return clean_pred

    def _preprocess(self, image):
        image = self.resize(image)
        image = np.array(image, dtype=np.float32)
        image, padding = self.pad(image)
        image = image.transpose(2, 0, 1)
        image /= 255
        return image, padding

    def run(self, image):
        crops = []
        paddings = []
        for i, (_, x, y) in enumerate(NUMBER_CONFIG):
            crop = image.crop([x, y, x + NUMBER_WIDTH, y + NUMBER_HEIGHT])
            crop, padding = self._preprocess(crop)
            crops.append(crop)
            paddings.append(padding)

        crops = np.array(crops, dtype=np.float16)
        preds = self._infer(crops).astype(np.float32)

        for i, padding in enumerate(paddings):
            preds[i] = self.fix_bboxes(
                preds[i], NUMBER_WIDTH, NUMBER_HEIGHT, padding
            )

        pred = self._post_process(preds)
        pred["elixir"] = {
            "bounding_box": ELIXIR_BOUNDING_BOX,
            "confidence": 1.0,
            "number": self._calculate_elixir(image),
        }
        return pred
