import onnxruntime
import numpy as np


class OnnxDetector:
    def __init__(self, model_path):
        self.model_path = model_path

        self.sess = onnxruntime.InferenceSession(self.model_path)
        self.output_name = self.sess.get_outputs()[0].name
        self.input_name = self.sess.get_inputs()[0].name

    @staticmethod
    def _xywh_to_xyxy(boxes):
        boxes[:, 0] -= boxes[:, 2] / 2
        boxes[:, 1] -= boxes[:, 3] / 2
        boxes[:, 2] += boxes[:, 0]
        boxes[:, 3] += boxes[:, 1]

    @staticmethod
    def _nms(boxes, scores, thresh):
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]  # get boxes with more ious first

        keep = []
        while order.size > 0:
            i = order[0]  # pick maximum iou box
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)  # maximum width
            h = np.maximum(0.0, yy2 - yy1 + 1)  # maximum height
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)

            inds = np.where(ovr <= thresh)[0]
            order = order[inds + 1]

        return keep

    def nms(self, prediction, conf_thres=0.35, iou_thres=0.45):
        """
        Runs Non-Maximum Suppression (NMS) on inference results
        """
        output = [np.zeros((0, 6))] * len(prediction)
        for i in range(len(prediction)):
            # Mask out predictions below the confidence threshold
            mask = prediction[i, :, 4] > conf_thres
            x = prediction[i][mask]

            if not x.shape[0]:
                continue

            # Calculate the best scores
            # score = object confidence * class confidence
            scores = x[:, 4:5] * x[:, 5:]
            best_scores_idx = np.argmax(scores, axis=1).reshape(-1, 1)
            best_scores = np.take_along_axis(scores, best_scores_idx, axis=1)

            # Again, mask out predictions below the confidence threshold
            mask = np.ravel(best_scores > conf_thres)
            best_scores = best_scores[mask]
            best_scores_idx = best_scores_idx[mask]

            # Convert the xywh of each box to xyxy inplace
            boxes = x[mask, :4]
            self._xywh_to_xyxy(boxes)

            # Work out which boxes to keep
            keep = self._nms(boxes, np.ravel(best_scores), iou_thres)

            # Keep only the best class
            best = np.hstack([boxes[keep], best_scores[keep], best_scores_idx[keep]])
            output[i] = best

        return output

    def _post_process(self, pred):
        raise NotImplementedError

    def run(self, image):
        raise NotImplementedError
