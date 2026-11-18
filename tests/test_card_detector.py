import os

import numpy as np
from PIL import Image

from clashroyalebuildabot.constants.paths import IMAGES_DIR
from clashroyalebuildabot.constants.screenshot import CARD_BOXES
from clashroyalebuildabot.detectors.card_detector import CardDetector
from clashroyalebuildabot.game.cards import Cards

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


def test_adds_a_blank_for_each_hand_slot():
    detector = CardDetector(DECK)
    assert detector.cards == DECK + [Cards.BLANK] * CardDetector.HAND_SIZE


def test_accepts_a_tuple():
    detector = CardDetector(tuple(DECK))
    assert detector.cards[: len(DECK)] == DECK


def card_art(name, look, size):
    """A card's art as the game draws it: "colour", "grey" (can't be
    afforded, with the wedge over the whole card) or "washed" (can't be
    afforded, no wedge yet)."""
    art = Image.open(os.path.join(IMAGES_DIR, "cards", f"{name}.jpg"))
    art = art.convert("RGB").resize(size)
    if look == "colour":
        return art
    grey = np.asarray(art.convert("L"), dtype=np.float32)
    scale, offset = (
        CardDetector.WEDGE if look == "grey" else CardDetector.WASHED_OUT
    )
    grey = (scale * grey + offset).clip(0, 255).astype(np.uint8)
    return Image.fromarray(grey).convert("RGB")


def screenshot(slots):
    """A 368x652 frame on the blue hand panel, with each (art name, look)
    pasted into its box in CARD_BOXES."""
    image = Image.new("RGB", (368, 652), (30, 110, 200))
    for (name, look), box in zip(slots, CARD_BOXES, strict=True):
        size = (box[2] - box[0], box[3] - box[1])
        image.paste(card_art(name, look, size), box[:2])
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
        Cards.BLANK,
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
