from PIL import Image, ImageOps
import numpy as np
import cv2
from src.constants import OCR_CONFIG, PRINCESS_HP


class OCR:
    def __init__(self):
        self.digits = []
        for i in range(10):
            image = Image.open(f'digits/{i}.png')
            image = image.convert('L')
            image = image.point(lambda x: 1 if x > 0 else 0)
            self.digits.append(np.array(image))

    @staticmethod
    def _preprocess_state(state):
        """
        Preprocess the state from OCR

        TODO: Can't distinguish between (full hp, no hp) and (no hp, full hp)
        """
        for i, j in [['ally', 'enemy'], ['enemy', 'ally']]:
            if state[f'{i}_crowns'] == 2:
                state[f'left_{j}_princess'] = 0
                state[f'right_{j}_princess'] = 0
            elif state[f'{i}_crowns'] == 1 and state[f'left_{j}_princess'] == -1 and state[f'right_{j}_princess'] != -1:
                state[f'left_{j}_princess'] = 0
            elif state[f'{i}_crowns'] == 1 and state[f'right_{j}_princess'] == -1 and state[f'left_{j}_princess'] != -1:
                state[f'right_{j}_princess'] = 0
            elif state[f'{i}_crowns'] == 0 and state[f'right_{j}_princess'] == -1 and state[f'left_{j}_princess'] == -1:
                state[f'right_{j}_princess'] = PRINCESS_HP[state[f'{j}_level'] - 1]
                state[f'left_{j}_princess'] = PRINCESS_HP[state[f'{j}_level'] - 1]
        return state

    @staticmethod
    def _calculate_bounding_boxes(image):
        """
        Find all bounding boxes in the image (with no parents)
        """
        contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Find the contours with no parents
        contours = [contours[i] for i in range(len(contours)) if hierarchy[0][i][3] == -1]
        bounding_boxes = sorted([cv2.boundingRect(contour) for contour in contours])
        return bounding_boxes

    def _calculate_match_scores(self, image):
        """
        Calculate scores between the image and the digits 0 to 9
        """
        match_scores = []
        for digit in self.digits:
            resized_crop = np.array(image.resize(digit.shape[::-1]))
            match_score = cv2.matchTemplate(resized_crop, digit, cv2.TM_CCOEFF_NORMED)[0][0]
            match_scores.append(match_score)
        return match_scores

    def _infer_number(self, image, threshold, height=200, min_confidence=0.3):
        """
        Use template matching on bounding boxes to infer the number in the image
        """
        image = image.resize((height * image.size[0] // image.size[1], height),
                             Image.BICUBIC)
        image = image.convert('L')
        image = 255 * np.array(np.array(image) > threshold, dtype=np.uint8)
        bounding_boxes = self._calculate_bounding_boxes(image)
        image = Image.fromarray(image)
        image = ImageOps.invert(image)

        number = ''
        for x, y, w, h in bounding_boxes:
            # Skip regions which are not tall enough (I.e. random blobs)
            if h < 0.6 * image.height:
                continue
            crop = image.crop((x, y, x + w, y + h))
            match_scores = self._calculate_match_scores(crop)
            if np.max(match_scores) > min_confidence:
                number += str(np.argmax(match_scores))

        if number == '':
            number = '-1'
        number = int(number)

        return number

    def run(self, image):
        state = {}
        for name, position, threshold in OCR_CONFIG:
            crop = image.crop(position)
            number = self._infer_number(crop, threshold)
            state[name] = number
        state = self._preprocess_state(state)

        return state


def main():
    from pprint import pprint
    image_path = 'battle.jpg'
    cls = OCR()
    result = cls.run(Image.open(image_path))
    pprint(result)


if __name__ == '__main__':
    main()
