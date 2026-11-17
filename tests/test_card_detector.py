from clashroyalebuildabot.detectors.card_detector import CardDetector
from clashroyalebuildabot.namespaces.cards import Cards

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
