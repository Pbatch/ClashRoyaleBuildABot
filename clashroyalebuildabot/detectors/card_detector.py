from collections.abc import Sequence
from functools import cache

import numpy as np
from scipy.optimize import linear_sum_assignment

from clashroyalebuildabot.constants.card_hashes import CARD_HASHES
from clashroyalebuildabot.constants.screenshot import CARD_BOXES
from clashroyalebuildabot.game.cards import Card, Cards
from clashroyalebuildabot.utils.error_handling import WikifiedError
from clashroyalebuildabot.utils.image import crop
from clashroyalebuildabot.utils.thumbnail import from_hex, thumbnail

# Card thumbnails are this many pixels across and down.
THUMBNAIL_SIZE = (8, 10)


def card_thumbnail(image: np.ndarray) -> np.ndarray:
    """A card, or a card's art, as the greyscale thumbnail it's matched
    by."""
    return thumbnail(image, THUMBNAIL_SIZE, grey=True)


@cache
def art_thumbnails() -> dict[str, np.ndarray]:
    """Every card art's thumbnail, by art name (``<card>`` and, for an
    evolution, ``<card>_ev1``). They're made from the art by maintainers,
    so the art itself doesn't ship with the bot."""
    return {
        name: from_hex(h, THUMBNAIL_SIZE, grey=True)
        for name, h in CARD_HASHES.items()
    }


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
    # The bottom rows hold the cost badge, which the card art doesn't have.
    MATCH_ROWS = 8
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
    ) -> None:
        # Build a new list rather than extending the caller's. The blanks let
        # the matcher assign empty hand slots.
        self.cards = [*cards, *([Cards.BLANK] * self.HAND_SIZE)]
        self.grey_std_threshold = grey_std_threshold

        self.art_variants, self.art_owners = self._deck_art()
        self._last: list[Card] | None = None

    def reset(self) -> None:
        """Forget the last hand, for the start of a new battle."""
        self._last = None

    def _pixels(self, thumb: np.ndarray) -> np.ndarray:
        """The thumbnail pixels a card is matched on, as floats."""
        return thumb.astype(np.float32)[: self.MATCH_ROWS].ravel()

    def _variants(self, thumb: np.ndarray) -> np.ndarray:
        """An art's pixels as drawn normally (first), washed out and in the
        wedge."""
        gray = self._pixels(thumb)
        variants = [gray]
        for scale, offset in (self.WASHED_OUT, self.WEDGE):
            variants.append(scale * gray + offset)
        return np.stack(variants)

    @staticmethod
    def _art_thumbnails(card: Card) -> list[np.ndarray]:
        """The card's art, plus its evolution's art if it has one: an
        evolved card is drawn with that instead."""
        thumbs = art_thumbnails()
        if card.name not in thumbs:
            raise WikifiedError("005", f"No card hash for {card.name}.")
        names = [card.name, f"{card.name}_ev1"]
        return [thumbs[n] for n in names if n in thumbs]

    def _deck_art(self) -> tuple[np.ndarray, np.ndarray]:
        """Every art's variants, and the index in self.cards it belongs
        to."""
        variants, owners = [], []
        for i, card in enumerate(self.cards):
            for thumb in self._art_thumbnails(card):
                variants.append(self._variants(thumb))
                owners.append(i)
        return np.stack(variants), np.array(owners)

    def _match_costs(
        self, crops: list[np.ndarray], coloured: list[bool]
    ) -> np.ndarray:
        """(positions, cards): how unlike each card each position looks."""
        seen = np.stack([self._pixels(card_thumbnail(c)) for c in crops])
        # (positions, arts, variants, pixels).
        diffs = np.abs(
            seen[:, None, None, :] - self.art_variants[None, :, :, :]
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
        for art, owner in enumerate(self.art_owners):
            costs[:, owner] = np.minimum(costs[:, owner], art_costs[:, art])
        return costs

    def _apply_memory(self, costs: np.ndarray) -> np.ndarray:
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

    def _detect_cards(
        self, crops: list[np.ndarray], coloured: list[bool]
    ) -> list[Card]:
        costs = self._apply_memory(self._match_costs(crops, coloured))
        # Every position holds a different card.
        _, idx = linear_sum_assignment(costs)
        return [self.cards[i] for i in idx]

    @staticmethod
    def _art_area(card: np.ndarray) -> np.ndarray:
        """The middle of a card's art: clear of the blue panel around the
        card and the cost badge along its bottom, which keep some colour
        even when the card is greyed out."""
        height, width = card.shape[:2]
        return crop(
            card,
            (0.2 * width, 0.1 * height, 0.8 * width, 0.7 * height),
        )

    def _is_coloured(self, card: np.ndarray) -> bool:
        """Whether the card is drawn in colour rather than grey. An empty
        slot's blue counts as colour."""
        art = self._art_area(card).astype(np.float32)
        # How far each pixel is from grey, on average.
        return bool(np.mean(np.std(art, axis=2)) > self.grey_std_threshold)

    @staticmethod
    def _detect_if_ready(cards: list[Card], coloured: list[bool]) -> list[int]:
        """Hand positions whose card is in colour. A card the player can't
        afford is drawn in grey, and an empty slot is never ready."""
        return [
            i
            for i, (card, colour) in enumerate(
                zip(cards[1:], coloured[1:], strict=True)
            )
            if colour and card != Cards.BLANK
        ]

    def run(self, image: np.ndarray) -> tuple[list[Card], list[int]]:
        crops = [crop(image, position) for position in CARD_BOXES]
        coloured = [self._is_coloured(card) for card in crops]
        cards = self._detect_cards(crops, coloured)
        ready = self._detect_if_ready(cards, coloured)
        self._last = cards
        return cards, ready
