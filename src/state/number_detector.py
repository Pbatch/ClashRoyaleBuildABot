from PIL import Image, ImageOps
import os
from imagehash import average_hash
import numpy as np
import cv2
from glob import glob
from src.data.constants import NUMBER_CONFIG, KING_HP, PRINCESS_HP

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class NumberDetector:
    def __init__(self):
        self.digit_hashes = self._calculate_digit_hashes()

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
    def _calculate_digit_hashes():
        """
        Get the 'true' hashes for the digits 0 to 9
        """
        # Because the paths are sorted, we don't need to record the digit names
        digit_hashes = []
        for path in sorted(glob(f'{DATA_DIR}/images/digits/*.png')):
            digit = Image.open(path)
            digit = digit.convert('L')
            digit = digit.point(lambda x: 1 if x > 0 else 0)
            digit_hash = average_hash(digit, hash_size=16)
            digit_hashes.append(digit_hash)
        return digit_hashes

    def _calculate_number_and_hash_diffs(self, image, threshold, height=400):
        """
        Preprocess the image using the given height and threshold
        Create bounding boxes around the digits
        Hash and compare bounding boxes to predict digits
        Combine the digits to form a number
        """
        image = image.resize((height * image.size[0] // image.size[1], height),
                             Image.BICUBIC)
        image = image.convert('L')
        image = 255 * np.array(np.array(image) > threshold, dtype=np.uint8)
        bounding_boxes = self._calculate_bounding_boxes(image)
        image = Image.fromarray(image)
        image = ImageOps.invert(image)

        number = ''
        hash_diffs = []
        for x, y, w, h in bounding_boxes:
            # Skip regions which are not tall enough (I.e. random blobs)
            if h < 0.6 * image.height:
                continue
            crop = image.crop((x, y, x + w, y + h))
            hash_diff = [average_hash(crop, hash_size=16) - h for h in self.digit_hashes]
            best_idx = np.argmin(hash_diff)
            number += str(best_idx)
            hash_diffs.append(hash_diff[best_idx])

        if number == '':
            number = '-1'
            hash_diffs = [float('inf')]

        return number, hash_diffs

    def _calculate_hp(self, image, max_hp):
        """
        Calculate the health that the given health bar represents
        """
        image = image.convert('L')
        column_sums = np.array(np.sum(image, axis=0), dtype=np.int32)
        column_diff = np.diff(column_sums)
        column_change_idx = np.argmax(np.abs(column_diff))
        # Not sure whether to add 1 or 2 here
        hp_multiplier = (column_change_idx + 2) / len(column_sums)
        hp = round(hp_multiplier * max_hp)
        return hp

    def run(self, image):
        """
        Detect the numbers in the image
        """
        pred = {}
        # First predict the elixir, the timer and the crowns
        for name in ['timer', 'elixir', 'ally_crowns', 'enemy_crowns']:
            bounding_box, threshold = NUMBER_CONFIG[name]
            crop = image.crop(bounding_box)
            number, _ = self._calculate_number_and_hash_diffs(crop, threshold)
            pred[name] = {'bounding_box': bounding_box,
                          'number': number}

        # Then try to predict the king levels
        for name in ['enemy_king_level', 'ally_king_level']:
            *bounding_boxes, threshold = NUMBER_CONFIG[name]

            crops = [image.crop(bounding_box) for bounding_box in bounding_boxes]

            output = [[bounding_box, *self._calculate_number_and_hash_diffs(crop, threshold)]
                      for bounding_box, crop in zip(bounding_boxes, crops)]

            bounding_box, number, _ = min(output, key=lambda x: np.mean(x[2]))
            pred[name] = {'bounding_box': bounding_box,
                          'number': number}

        # End by predicting the hp of the towers
        ally_idx = min([int(pred['ally_king_level']['number']) - 1, 13])
        enemy_idx = min([int(pred['enemy_king_level']['number']) - 1, 13])
        for name in ['right_ally_princess_hp',
                     'left_ally_princess_hp',
                     'ally_king_hp',
                     'right_enemy_princess_hp',
                     'left_enemy_princess_hp',
                     'enemy_king_hp']:
            bounding_box = NUMBER_CONFIG[name]
            crop = image.crop(bounding_box)
            hp_list = PRINCESS_HP if 'princess' in name else KING_HP
            idx = ally_idx if 'ally' in name else enemy_idx
            max_hp = hp_list[idx]
            number = self._calculate_hp(crop, max_hp)
            pred[name] = {'bounding_box': bounding_box,
                          'number': number}

        return pred
