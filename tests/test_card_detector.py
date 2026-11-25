from pathlib import Path

import cv2
import numpy as np
import pytest

from clashroyalebuildabot.constants.screenshot import CARD_BOXES
from clashroyalebuildabot.detectors.card_detector import (
    EMPTY_ART,
    CardDetector,
    art_embeddings,
)
from clashroyalebuildabot.game.cards import Card, Cards
from clashroyalebuildabot.utils.image import load, resize

# The art of the cards these tests draw. The bot ships only the art's
# vectors; the rest of the art is kept by maintainers (see dev/cards).
ART_DIR = Path(__file__).parent / "data" / "cards"
# How the game greys a card the player can't afford, from the art's
# brightness, as (scale, offset): washed out, and in the darker wedge.
WASHED_OUT = (0.355, 163.0)
WEDGE = (0.592, 36.0)

DECK = [
    Cards.ARCHERS,
    Cards.BABY_DRAGON,
    Cards.CANNON,
    Cards.GOBLIN_BARREL,
    Cards.KNIGHT,
    Cards.MINIPEKKA,
    Cards.MUSKETEER,
    Cards.WITCH,
]


def test_does_not_modify_the_given_cards():
    cards = list(DECK)
    CardDetector(cards)
    assert cards == DECK


def test_adds_an_empty_slot_for_each_hand_position():
    detector = CardDetector(DECK)
    assert detector.cards == DECK + [None] * CardDetector.HAND_SIZE


def test_accepts_a_tuple():
    detector = CardDetector(tuple(DECK))
    assert detector.cards[: len(DECK)] == DECK


def test_every_card_has_an_embedding():
    arts = [EMPTY_ART, *(card.name for card in Cards.all())]
    missing = [art for art in arts if art not in art_embeddings()]
    assert not missing


@pytest.mark.parametrize(
    "path", sorted(ART_DIR.glob("*.jpg")), ids=lambda p: p.stem
)
def test_embeddings_match_the_art(path):
    """The shipped vectors are the model's, for this art: so the vectors
    and the model belong together."""
    (vector,) = CardDetector(DECK).embed([load(str(path))])
    assert float(vector @ art_embeddings()[path.stem]) > 0.999


def test_unknown_card_fails_clearly():
    unknown = Card("not_a_card", cost=1, id_=0)
    with pytest.raises(Exception, match="No card embedding for not_a_card"):
        CardDetector([*DECK[:7], unknown])


def card_art(name, look, size):
    """A card's art as the game draws it: "colour", "grey" (can't be
    afforded, with the wedge over the whole card) or "washed" (can't be
    afforded, no wedge yet)."""
    art = resize(load(str(ART_DIR / f"{name}.jpg")), size)
    if look == "colour":
        return art
    grey = cv2.cvtColor(art, cv2.COLOR_RGB2GRAY).astype(np.float32)
    scale, offset = WEDGE if look == "grey" else WASHED_OUT
    grey = (scale * grey + offset).clip(0, 255).astype(np.uint8)
    return cv2.cvtColor(grey, cv2.COLOR_GRAY2RGB)


def screenshot(slots):
    """A 368x652 frame on the blue hand panel, with each (art name, look)
    pasted into its box in CARD_BOXES."""
    image = np.full((652, 368, 3), (30, 110, 200), np.uint8)
    for (name, look), box in zip(slots, CARD_BOXES, strict=True):
        left, top, right, bottom = box
        size = (right - left, bottom - top)
        image[top:bottom, left:right] = card_art(name, look, size)
    return image


def test_reads_the_hand_and_which_cards_are_ready():
    image = screenshot(
        [
            ("musketeer", "colour"),
            ("archers", "colour"),
            ("knight", "grey"),
            ("blank", "colour"),
            ("witch", "colour"),
        ]
    )
    cards, ready = CardDetector(DECK).run(image)
    assert cards == [
        Cards.MUSKETEER,
        Cards.ARCHERS,
        Cards.KNIGHT,
        None,
        Cards.WITCH,
    ]
    # The greyed knight can't be afforded, and an empty slot is never
    # ready, though both sit on the coloured panel.
    assert ready == [0, 3]


def test_reads_washed_out_cards():
    image = screenshot(
        [
            ("cannon", "colour"),
            ("archers", "washed"),
            ("goblin_barrel", "washed"),
            ("knight", "washed"),
            ("minipekka", "washed"),
        ]
    )
    cards, ready = CardDetector(DECK).run(image)
    assert cards == [
        Cards.CANNON,
        Cards.ARCHERS,
        Cards.GOBLIN_BARREL,
        Cards.KNIGHT,
        Cards.MINIPEKKA,
    ]
    assert ready == []


def test_reads_an_evolved_card_as_its_card():
    image = screenshot(
        [
            ("musketeer", "colour"),
            ("archers_ev1", "colour"),
            ("minipekka", "colour"),
            ("goblin_barrel", "colour"),
            ("knight", "colour"),
        ]
    )
    cards, _ = CardDetector(DECK).run(image)
    assert cards[1] == Cards.ARCHERS


def test_reset_forgets_the_last_hand():
    detector = CardDetector(DECK)
    detector.run(
        screenshot(
            [
                ("musketeer", "colour"),
                ("archers", "colour"),
                ("minipekka", "colour"),
                ("goblin_barrel", "colour"),
                ("knight", "colour"),
            ]
        )
    )
    assert detector._last is not None
    detector.reset()
    assert detector._last is None
