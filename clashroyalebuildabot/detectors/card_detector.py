"""Read the next card and the four cards in hand.

A small CNN (models/card_embedder.onnx) turns each card position into a
vector, trained so a position's vector lies close to its card art's,
whether the card is drawn in colour, greyed out with the elixir wedge, raised
or as the small next card. Every card art's vector ships in
models/card_embeddings.npz, so the art itself doesn't, and a card the game
adds later needs only its art's vector, not a new model (see dev/cards).
"""

import os
from collections.abc import Sequence
from functools import cache

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

from clashroyalebuildabot.constants.paths import MODELS_DIR
from clashroyalebuildabot.constants.screenshot import CARD_BOXES
from clashroyalebuildabot.detectors import onnx_model
from clashroyalebuildabot.game.cards import Card
from clashroyalebuildabot.utils.error_handling import WikifiedError
from clashroyalebuildabot.utils.image import crop

MODEL_PATH = os.path.join(MODELS_DIR, "card_embedder.onnx")
EMBEDDINGS_PATH = os.path.join(MODELS_DIR, "card_embeddings.npz")
# The art name of an empty hand slot, read as None.
EMPTY_ART = "blank"


@cache
def art_embeddings(path: str = EMBEDDINGS_PATH) -> dict[str, np.ndarray]:
    """Every card art's vector, by art name: ``<card>`` and, for an
    evolution, ``<card>_ev1``."""
    data = np.load(path)
    return dict(zip(data["names"].tolist(), data["vectors"], strict=True))


class CardDetector:
    """Reads the next card and the four cards in hand, and which of those
    can be played.

    Each position is matched to the deck card whose art's vector is most
    alike (by cosine similarity), every position holding a different card.
    An empty slot reads as None. The detector also remembers what it saw: a
    card stays in its position until it's played, and the card that
    replaces it is the one that was next. Call ``reset`` between battles.
    """

    # The next card plus the four in hand.
    HAND_SIZE = 5
    # How much a position prefers the card it held last frame, or the card
    # that was next, in cosine distance. On battle frames the right card is
    # typically 0.5 more alike than the best wrong one, and at least 0.14 in
    # 95% of positions, so this settles close calls while clear evidence of
    # another card still wins.
    MEMORY_BONUS = 0.1

    def __init__(
        self,
        cards: Sequence[Card],
        grey_std_threshold: int = 5,
        model_path: str = MODEL_PATH,
        embeddings_path: str = EMBEDDINGS_PATH,
    ) -> None:
        # What a position can hold: a deck card, or nothing (one None per
        # position, since every position holds a different entry).
        self.cards: list[Card | None] = [*cards, *([None] * self.HAND_SIZE)]
        self.grey_std_threshold = grey_std_threshold
        self.model = onnx_model.load(model_path)
        self.art_vectors, self.art_owners = self._deck_art(embeddings_path)
        self._last: list[Card | None] | None = None

    def reset(self) -> None:
        """Forget the last hand, for the start of a new battle."""
        self._last = None

    def _deck_art(self, path: str) -> tuple[np.ndarray, np.ndarray]:
        """The vector of every art of the deck's cards (a card with an
        evolution has both arts, since an evolved card is drawn with the
        other), and the index in self.cards each belongs to. An empty slot
        has the blank slot's art."""
        vectors = art_embeddings(path)
        arts, owners = [], []
        for i, card in enumerate(self.cards):
            art = EMPTY_ART if card is None else card.name
            if art not in vectors:
                raise WikifiedError("005", f"No card embedding for {art}.")
            for name in (art, f"{art}_ev1"):
                if name in vectors:
                    arts.append(vectors[name])
                    owners.append(i)
        return np.stack(arts), np.array(owners)

    def embed(self, crops: Sequence[np.ndarray]) -> np.ndarray:
        """(positions, dim) unit vectors, one per card position. Each is
        resized to the model's input as it was in training."""
        height, width = self.model.input_size
        batch = np.stack(
            [
                cv2.resize(
                    c,
                    (width, height),
                    interpolation=cv2.INTER_AREA
                    if c.shape[0] > height
                    else cv2.INTER_LINEAR,
                )
                for c in crops
            ]
        )
        return self.model(batch)

    def _match_costs(self, crops: list[np.ndarray]) -> np.ndarray:
        """(positions, cards): how unlike each card each position looks, as
        cosine distance to the card's closest art."""
        art_costs = 1 - self.embed(crops) @ self.art_vectors.T
        costs = np.full((len(crops), len(self.cards)), np.inf)
        for art, owner in enumerate(self.art_owners):
            costs[:, owner] = np.minimum(costs[:, owner], art_costs[:, art])
        return costs

    def _apply_memory(self, costs: np.ndarray) -> np.ndarray:
        """Each hand position's costs, less MEMORY_BONUS for the card it
        held last frame and for the card that was next."""
        if self._last is None:
            return costs
        costs = costs.copy()
        for position in range(1, self.HAND_SIZE):
            kept = {self._last[position], self._last[0]} - {None}
            for j, card in enumerate(self.cards):
                if card in kept:
                    costs[position, j] -= self.MEMORY_BONUS
        return costs

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

    def run(self, image: np.ndarray) -> tuple[list[Card | None], list[int]]:
        crops = [crop(image, position) for position in CARD_BOXES]
        costs = self._apply_memory(self._match_costs(crops))
        # Every position holds a different card.
        _, idx = linear_sum_assignment(costs)
        cards = [self.cards[i] for i in idx]
        # A card the player can't afford is drawn in grey, and an empty slot
        # is never ready.
        ready = [
            i
            for i, (card, image_crop) in enumerate(
                zip(cards[1:], crops[1:], strict=True)
            )
            if card is not None and self._is_coloured(image_crop)
        ]
        self._last = cards
        return cards, ready
