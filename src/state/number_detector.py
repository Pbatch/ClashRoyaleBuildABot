from PIL import Image, ImageOps
import os
from imagehash import average_hash
import numpy as np
import cv2
from glob import glob

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

    def run(self, image, threshold, height=400):
        """
        Detect the number in the image

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
        for x, y, w, h in bounding_boxes:
            # Skip regions which are not tall enough (I.e. random blobs)
            if h < 0.6 * image.height:
                continue
            crop = image.crop((x, y, x + w, y + h))
            hash_diff = [average_hash(crop, hash_size=16) - h for h in self.digit_hashes]
            number += str(np.argmin(hash_diff))

        if number == '':
            number = '-1'
        number = int(number)

        return number
