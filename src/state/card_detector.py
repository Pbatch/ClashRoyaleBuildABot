from PIL import Image
import os
from imagehash import average_hash
import numpy as np
from src.data.constants import CARD_CONFIG

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


class CardDetector:
    def __init__(self, card_names):
        self.card_names = card_names

        self.cards, self.card_hashes = self._calculate_cards_and_card_hashes()

    def _calculate_cards_and_card_hashes(self):
        """
        Get a list of the card names and their 'hashes'
        """
        cards = []
        card_hashes = []
        with open(f'{DATA_DIR}/cards.csv') as f:
            for line in f:
                name, _, cost, type_ = line.strip().replace('"', '').split(',')
                if name in self.card_names:
                    path = f'{DATA_DIR}/images/cards/{name}.png'
                    card = Image.open(path)
                    card_hash = average_hash(card, hash_size=16)
                    cards.append([name, int(cost), type_])
                    card_hashes.append(card_hash)
        return cards, card_hashes

    def run(self, image):
        """
        Detect the cards in the image by comparing hashes
        """
        cards = []
        for i, position in enumerate(CARD_CONFIG):
            crop = image.crop(position)
            hash_diff = [average_hash(crop, hash_size=16) - h for h in self.card_hashes]
            card = self.cards[np.argmin(hash_diff)]
            cards.append({'name': card[0], 'cost': card[1], 'type': card[2]})

        return cards
