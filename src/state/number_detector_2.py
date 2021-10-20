from src.state.onnx_detector import OnnxDetector
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class NumberDetector2(OnnxDetector):
    PRINCESS_HEIGHT = 20
    PRINCESS_WIDTH = 40
    ENEMY_PRINCESS_Y = 87
    ALLY_PRINCESS_Y = 390
    LEFT_PRINCESS_X = 70
    RIGHT_PRINCESS_X = 260
    KING_X = 67
    KING_WIDTH = 233
    KING_HEIGHT = 30
    CROWN_X = 336
    CROWN_WIDTH = 24
    CROWN_HEIGHT = 34

    BOXES = {'left_enemy_princess': (LEFT_PRINCESS_X, ENEMY_PRINCESS_Y, LEFT_PRINCESS_X + PRINCESS_WIDTH, ENEMY_PRINCESS_Y + PRINCESS_HEIGHT),
             'right_enemy_princess': (RIGHT_PRINCESS_X, ENEMY_PRINCESS_Y, RIGHT_PRINCESS_X + PRINCESS_WIDTH, ENEMY_PRINCESS_Y + PRINCESS_HEIGHT),
             'left_ally_princess': (LEFT_PRINCESS_X, ALLY_PRINCESS_Y, LEFT_PRINCESS_X + PRINCESS_WIDTH, ALLY_PRINCESS_Y + PRINCESS_HEIGHT),
             'right_ally_princess': (RIGHT_PRINCESS_X, ALLY_PRINCESS_Y, RIGHT_PRINCESS_X + PRINCESS_WIDTH, ALLY_PRINCESS_Y + PRINCESS_HEIGHT),
             'timer': (300, 0, 367, 40),
             'enemy_king': (KING_X, 10, KING_X + KING_WIDTH, 10 + KING_HEIGHT),
             'ally_king': (KING_X, 475, KING_X + KING_WIDTH, 475 + KING_HEIGHT),
             'elixir': (100, 615, 130, 645),
             'enemy_crowns': (CROWN_X, 196, CROWN_X + CROWN_WIDTH, 196 + CROWN_HEIGHT),
             'ally_crowns': (CROWN_X, 321, CROWN_X + CROWN_WIDTH, 321 + CROWN_HEIGHT)}

    @staticmethod
    def _box1_in_box2(box1, box2):
        """
        Check if box1 lies completely inside box2
        """
        return (box2[0] < box1[0] and box2[1] < box1[1]) and (box2[2] > box1[2] and box2[3] > box1[3])

    def _get_number_and_confidence(self, pred, box):
        digits = []
        for p in pred:
            if self._box1_in_box2(p['bounding_box'], box):
                digits.append([p['bounding_box'][0], str(p['number']), p['confidence']])
        if len(digits) == 0:
            return '-1', []
        digits.sort()

        # It's better to leave the number as a string
        # for debugging errors like number = '0001'
        number = ''.join(i[1] for i in digits)
        confidence = [i[2] for i in digits]

        return number, confidence

    def _post_process(self, pred):
        pred = [{'bounding_box': p[:4].tolist(),
                 'confidence': p[4],
                 'number': round(p[5])}
                for p in pred]

        clean_pred = {}
        for name, box in self.BOXES.items():
            number, confidence = self._get_number_and_confidence(pred, box)
            clean_pred[name] = {'bounding_box': box,
                                'confidence': confidence,
                                'number': number}

        return clean_pred
