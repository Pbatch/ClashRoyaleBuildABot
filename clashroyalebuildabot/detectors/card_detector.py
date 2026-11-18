import os
from collections.abc import Sequence

import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

from clashroyalebuildabot.constants.paths import IMAGES_DIR
from clashroyalebuildabot.constants.screenshot import CARD_BOXES
from clashroyalebuildabot.game.cards import Card, Cards
from clashroyalebuildabot.utils.error_handling import WikifiedError


class CardDetector:
    """Reads the next card and the four cards in hand, and which of those
    can be played.

    Each card position is shrunk to a tiny greyscale thumbnail and compared
    with the deck's card art. A card in colour is drawn as the art is. A
    card the player can't afford yet is drawn in grey and washed out, apart
    from a darker wedge that sweeps round from 12 o'clock as elixir fills,
    so each of its pixels is compared with the art as drawn normally, washed
    out or in the wedge, whichever is closest.

    Washed-out cards can look alike, so the detector also remembers what it
    saw: a card stays in its position until it's played, and the card that
    replaces it is the one that was next. Call ``reset`` between battles.
    """

    # The next card plus the four in hand.
    HAND_SIZE = 5
    HASH_WIDTH = 8
    HASH_HEIGHT = 10
    # The bottom rows hold the cost badge, which the card art doesn't have.
    HASH_ROWS = 8
    # How a greyed card's brightness relates to the art's, as (scale,
    # offset), outside the wedge and inside it. Measured on battle frames.
    WASHED_OUT = (0.355, 163.0)
    WEDGE = (0.592, 36.0)
    # How much a position prefers the card it held last frame, or the card
    # that was next, in the same units as the match cost (mean brightness
    # difference per pixel). Clear evidence of another card still wins.
    MEMORY_BONUS = 4.0

    def __init__(
        self,
        cards: Sequence[Card],
        grey_std_threshold: int = 5,
    ):
        # Build a new list rather than extending the caller's. The blanks let
        # the matcher assign empty hand slots.
        self.cards = [*cards, *([Cards.BLANK] * self.HAND_SIZE)]
        self.grey_std_threshold = grey_std_threshold

        self.card_hashes, self.hash_owners = self._calculate_card_hashes()
        self._last: list[Card] | None = None

    def reset(self):
        """Forget the last hand, for the start of a new battle."""
        self._last = None

    def _calculate_hash(self, image):
        small = image.resize(
            (self.HASH_WIDTH, self.HASH_HEIGHT), Image.Resampling.BILINEAR
        ).convert("L")
        return np.asarray(small, dtype=np.float32)[: self.HASH_ROWS].ravel()

    def _calculate_multi_hash(self, image):
        """The art's hash as drawn normally (first), washed out and in the
        wedge."""
        gray = self._calculate_hash(image)
        variants = [gray]
        for scale, offset in (self.WASHED_OUT, self.WEDGE):
            variants.append(scale * gray + offset)
        return np.stack(variants)

    @staticmethod
    def _art_paths(card: Card) -> list[str]:
        """The card's art, plus its evolution's art if it has one: an
        evolved card is drawn with that instead."""
        base = os.path.join(IMAGES_DIR, "cards", card.name)
        paths = [f"{base}.jpg"]
        if os.path.exists(f"{base}_ev1.jpg"):
            paths.append(f"{base}_ev1.jpg")
        return paths

    def _calculate_card_hashes(self):
        """Every art's multi-hash, and the index in self.cards it belongs
        to."""
        hashes, owners = [], []
        try:
            for i, card in enumerate(self.cards):
                for path in self._art_paths(card):
                    hashes.append(self._calculate_multi_hash(Image.open(path)))
                    owners.append(i)
        except Exception as e:
            raise WikifiedError(
                "005", "Can't load cards and their images."
            ) from e
        return np.stack(hashes), np.array(owners)

    def _match_costs(self, crops, coloured):
        """(positions, cards): how unlike each card each position looks."""
        crop_hashes = np.stack([self._calculate_hash(c) for c in crops])
        # (positions, arts, variants, pixels).
        diffs = np.abs(
            crop_hashes[:, None, None, :] - self.card_hashes[None, :, :, :]
        )
        # A coloured card is drawn as the art is. A greyed one may have any
        # variant at each pixel.
        art_costs = np.where(
            np.array(coloured)[:, None],
            diffs[:, :, 0].mean(axis=2),
            diffs.min(axis=2).mean(axis=2),
        )
        # A card matches as well as its closest art.
        costs = np.full((len(crops), len(self.cards)), np.inf)
        for art, owner in enumerate(self.hash_owners):
            costs[:, owner] = np.minimum(costs[:, owner], art_costs[:, art])
        return costs

    def _apply_memory(self, costs):
        if self._last is None:
            return costs
        costs = costs.copy()
        last_next = self._last[0]
        for position in range(1, self.HAND_SIZE):
            for j, card in enumerate(self.cards):
                if card == Cards.BLANK:
                    continue
                if card in (self._last[position], last_next):
                    costs[position, j] -= self.MEMORY_BONUS
        return costs

    def _detect_cards(self, crops, coloured):
        costs = self._apply_memory(self._match_costs(crops, coloured))
        # Every position holds a different card.
        _, idx = linear_sum_assignment(costs)
        return [self.cards[i] for i in idx]

    @staticmethod
    def _art_area(crop):
        """The middle of a card's art: clear of the blue panel around the
        card and the cost badge along its bottom, which keep some colour
        even when the card is greyed out."""
        width, height = crop.size
        return crop.crop(
            (
                round(0.2 * width),
                round(0.1 * height),
                round(0.8 * width),
                round(0.7 * height),
            )
        )

    def _is_coloured(self, crop) -> bool:
        """Whether the card is drawn in colour rather than grey. An empty
        slot's blue counts as colour."""
        art = np.asarray(self._art_area(crop), dtype=np.float32)
        # How far each pixel is from grey, on average.
        return bool(np.mean(np.std(art, axis=2)) > self.grey_std_threshold)

    @staticmethod
    def _detect_if_ready(cards, coloured):
        """Hand positions whose card is in colour. A card the player can't
        afford is drawn in grey, and an empty slot is never ready."""
        return [
            i
            for i, (card, colour) in enumerate(
                zip(cards[1:], coloured[1:], strict=True)
            )
            if colour and card != Cards.BLANK
        ]

    def run(self, image):
        crops = [image.crop(position) for position in CARD_BOXES]
        coloured = [self._is_coloured(crop) for crop in crops]
        cards = self._detect_cards(crops, coloured)
        ready = self._detect_if_ready(cards, coloured)
        self._last = cards
        return cards, ready
