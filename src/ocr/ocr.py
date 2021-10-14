from PIL import Image, ImageOps, ImageDraw
import numpy as np
import cv2
from src.data.constants import NUMBER_CONFIG, CARD_CONFIG, PRINCESS_HP, UNITS, KING_HP
import onnxruntime
from src.ocr.non_max_suppression import non_max_suppression
from glob import glob
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class OCR:
    def __init__(self, card_names):
        self.card_names = card_names
        if len(self.card_names) != 8:
            raise ValueError('You must specify all 8 of your cards')

        self.sess = onnxruntime.InferenceSession(f'{DATA_DIR}/yolo.onnx')

        self.digits = []
        # Because the paths are sorted, we don't need to record the digit names
        for path in sorted(glob(f'{DATA_DIR}/images/digits/*.png')):
            image = Image.open(path)
            image = image.convert('L')
            image = image.point(lambda x: 1 if x > 0 else 0)
            image = np.array(image)
            self.digits.append(image)

        # Get all the card metadata and images
        self.cards = []
        self.card_images = []
        with open(f'{DATA_DIR}/cards.csv') as f:
            for line in f:
                name, _, cost = line.strip().replace('"', '').split(',')
                if name in self.card_names:
                    path = f'{DATA_DIR}/images/cards/{name}.png'
                    image = Image.open(path)
                    image = np.array(image)[:, :, :3]
                    self.cards.append([name, int(cost)])
                    self.card_images.append(image)

    @staticmethod
    def _preprocess_state(state):
        """
        Preprocess the state from OCR

        TODO: Can't distinguish between (full hp, no hp) and (no hp, full hp)
        """
        # Clean up the princess HP
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

        # Clean up the king tower HP
        for side in ['ally', 'enemy']:
            if state[f'{side}_hp'] == -1 and state[f'{side}_level'] != -1:
                state[f'{side}_hp'] = KING_HP[state[f'{side}_level'] - 1]

        # Clean up the time
        # I.e. 123 -> 60 + 23 = 83
        str_time = str(state['timer'])
        if len(str_time) >= 3:
            state['timer'] = 60 * int(str_time[0]) + int(str_time[1:])
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

    @staticmethod
    def _calculate_match_scores(image, target_images):
        """
        Calculate match scores between the image and the target images
        """
        match_scores = []
        for target in target_images:
            resized_image = np.array(image.resize((target.shape[1], target.shape[0])))
            match_score = cv2.matchTemplate(resized_image, target, cv2.TM_CCOEFF_NORMED)[0][0]
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
            match_scores = self._calculate_match_scores(crop, self.digits)
            if np.max(match_scores) > min_confidence:
                number += str(np.argmax(match_scores))

        if number == '':
            number = '-1'
        number = int(number)

        return number

    def _infer_card(self, image, min_confidence=0.3):
        """
        Use template matching to infer the card in the image
        """
        match_scores = self._calculate_match_scores(image, self.card_images)
        if np.max(match_scores) > min_confidence:
            card = self.cards[np.argmax(match_scores)]
        else:
            card = ['', 11]
        return card

    def _infer_unit_positions(self, image):
        """
        Use the pretrained YOLOv5 model to identify and give the positions of each unit
        """
        height, width = image.height, image.width

        # YOLOv5 preprocesses the images to 416x416 (by default)
        image = image.resize((416, 416), Image.BICUBIC)
        image = np.array(image, dtype=np.float32)
        image = np.expand_dims(image.transpose(2, 0, 1), axis=0)
        image = image / 255

        # Inference
        pred = self.sess.run([self.sess.get_outputs()[0].name], {self.sess.get_inputs()[0].name: image})[0]
        pred = np.array(non_max_suppression(pred)[0])

        # Rescale the bounding boxes
        pred[:, [0, 2]] *= width / 416
        pred[:, [1, 3]] *= height / 416

        # Reformat the prediction
        unit_positions = [{'bounding_box': p[:4].tolist(),
                           'confidence': p[4],
                           'unit': UNITS[round(p[5])]}
                          for p in pred]
        return unit_positions

    def run(self, image, positions=True, debug=False):
        # Start with empty state
        state = {}

        # Get the positions of each unit
        if positions:
            unit_positions = self._infer_unit_positions(image)
            state['unit_positions'] = unit_positions

        # Get the names of the cards
        state['cards'] = []
        for i, position in enumerate(CARD_CONFIG):
            crop = image.crop(position)
            card = self._infer_card(crop)
            state['cards'].append({'name': card[0], 'cost': card[1]})

        # Get all the numbers
        for name, position, threshold in NUMBER_CONFIG:
            crop = image.crop(position)
            number = self._infer_number(crop, threshold)
            if number == -1 and name in {'ally_level', 'enemy_level'}:
                # Try again with X shifted by 25
                position = (position[0] + 25, position[1], position[2] + 25, position[3])
                crop = image.crop(position)
                number = self._infer_number(crop, threshold)

            state[name] = number
        state = self._preprocess_state(state)

        if debug:
            d = ImageDraw.Draw(image)
            for i in state['unit_positions']:
                d.ellipse(tuple(i['bounding_box']), outline='white')
            image.show()

        return state


def main():
    from pprint import pprint
    image_path = '../data/screenshots/154.jpg'
    card_names = ['minions', 'archers', 'arrows', 'giant',
                  'minipekka', 'fireball', 'knight', 'musketeer']
    cls = OCR(card_names)
    result = cls.run(Image.open(image_path), debug=True)
    pprint(result)


if __name__ == '__main__':
    main()
