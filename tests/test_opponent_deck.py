import numpy as np

from clashroyalebuildabot.detectors.opponent_deck import OpponentDeck
from clashroyalebuildabot.detectors.unit_tracker import (
    ALLY,
    ENEMY,
    ScoredDetection,
    Tracker,
)
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.units import Position, Units


def names(cards):
    return [card.name for card in cards]


def test_a_unit_one_card_makes_names_the_card():
    deck = OpponentDeck()
    deck.saw(Units.HOG_RIDER)
    deck.saw(Units.HOG_RIDER)
    deck.saw(Units.GOLEMITE)
    assert names(deck.cards) == ["hog_rider", "golem"]
    assert deck.unresolved == set()


def test_a_unit_several_cards_make_waits_for_one_of_them():
    deck = OpponentDeck()
    deck.saw(Units.SKELETON)  # skeletons, skeleton army, witch, ...
    assert deck.cards == []
    assert deck.unresolved == {Units.SKELETON}
    deck.saw(Units.WITCH)
    assert names(deck.cards) == ["witch"]
    assert deck.unresolved == set()
    # Their witch makes skeletons: more skeletons say nothing new.
    deck.saw(Units.SKELETON)
    assert deck.unresolved == set()


def test_possible_units_are_their_cards_units_and_the_unresolved():
    deck = OpponentDeck()
    deck.saw(Units.GOLEM)
    deck.saw(Units.GOBLIN)
    assert deck.possible_units() == {Units.GOLEM, Units.GOLEMITE, Units.GOBLIN}
    assert not deck.complete


def test_deck_is_complete_once_its_cards_and_unresolved_fill_it():
    deck = OpponentDeck()
    for unit in (
        Units.GOLEM,
        Units.BABY_DRAGON,
        Units.MEGA_MINION,
        Units.LUMBERJACK,
        Units.NIGHT_WITCH,
        Units.ELECTRO_DRAGON,
    ):
        deck.saw(unit)
    # Goblins and spear goblins could both be one Goblin Gang: a slot left.
    deck.saw(Units.GOBLIN)
    deck.saw(Units.SPEAR_GOBLIN)
    assert not deck.complete
    deck.saw(Units.TOMBSTONE)
    assert deck.complete
    possible = deck.possible_units()
    # Whichever cards made the goblins, their units are possible.
    assert {Units.GOBLIN_DRILL, Units.GOBLIN_GIANT} <= possible
    assert Units.PEKKA not in possible


def test_more_cards_than_a_deck_drops_the_least_seen():
    deck = OpponentDeck()
    for unit in 2 * (
        Units.GOLEM,
        Units.BABY_DRAGON,
        Units.MEGA_MINION,
        Units.LUMBERJACK,
        Units.NIGHT_WITCH,
        Units.ELECTRO_DRAGON,
        Units.TOMBSTONE,
        Units.PEKKA,
    ):
        deck.saw(unit)
    assert len(deck.cards) == 8
    deck.saw(Units.HOG_RIDER)  # one misnamed unit
    assert len(deck.cards) == 8
    assert Cards.HOG_RIDER not in deck.cards


def test_bombs_and_spawned_units_from_known_cards_are_ignored():
    deck = OpponentDeck()
    deck.saw(Units.BALLOON)
    deck.saw(Units.BOMB)
    assert names(deck.cards) == ["balloon"]
    assert deck.unresolved == set()


UNITS = (Units.RASCAL_BOY, Units.DARK_PRINCE, Units.PEKKA)


def play(tracker, frames, start=0.0, side=ENEMY):
    """Have tracker follow one unit from time start, scored over UNITS as
    each frame in frames says, on side."""
    for i, scores in enumerate(frames):
        both = np.zeros((2, len(UNITS)), np.float32)
        both[side] = scores
        unit = UNITS[int(np.argmax(scores))]
        det = ScoredDetection(
            unit, Position(0.9, 5, 20), scores=both, units=UNITS
        )
        tracker.step([det], [side], now=start + i * 0.1)
    return tracker


PEKKA = [0, 0, 0.9]
LATER = 2 * OpponentDeck.REPLAY_GAP  # a later play


def test_a_card_counts_once_its_unit_is_seen_in_two_plays():
    deck = OpponentDeck()
    tracker = play(Tracker(), [PEKKA] * OpponentDeck.MIN_FRAMES)
    deck.update(tracker.tracks)
    assert deck.cards == []  # one play could be a misread
    play(tracker, [PEKKA] * OpponentDeck.MIN_FRAMES, start=LATER)
    deck.update(tracker.tracks)
    deck.update(tracker.tracks)
    assert names(deck.cards) == ["pekka"]


def test_a_track_seen_briefly_doesnt_count():
    deck = OpponentDeck()
    tracker = Tracker()
    for start in (0, LATER):
        play(tracker, [PEKKA] * (OpponentDeck.MIN_FRAMES - 1), start)
        deck.update(tracker.tracks)
    assert deck.cards == []


def test_a_unit_whose_track_breaks_in_a_fight_is_one_play():
    deck = OpponentDeck()
    tracker = Tracker()
    for start in (0, OpponentDeck.REPLAY_GAP / 2):
        play(tracker, [PEKKA] * OpponentDeck.MIN_FRAMES, start)
        deck.update(tracker.tracks)
    assert deck.cards == []


def test_a_card_counted_too_soon_is_dropped_once_seen_better():
    # As on a recorded battle: a Dark Prince taken for a Rascal Boy as it's
    # deployed, then seen as a Dark Prince.
    deck = OpponentDeck()
    deck.saw(Units.RASCAL_BOY)  # the other play, sure of it
    rascal, prince = [0.8, 0.3, 0], [0.2, 0.9, 0]
    tracker = play(Tracker(), [rascal] * 5)
    deck.update(tracker.tracks)
    assert names(deck.cards) == ["rascals"]
    deck.saw(Units.DARK_PRINCE)
    play(tracker, [prince] * 10, start=0.5)
    deck.update(tracker.tracks)
    assert names(deck.cards) == ["rascals", "dark_prince"]
    assert deck._seen[1][0] == Units.DARK_PRINCE  # the track, seen better


def test_our_units_are_not_theirs():
    deck = OpponentDeck()
    tracker = Tracker()
    for start in (0, LATER):
        play(tracker, [PEKKA] * 6, start, side=ALLY)
        deck.update(tracker.tracks)
    assert deck.cards == []


def test_favours_their_cards_units_until_the_deck_is_complete():
    deck = OpponentDeck()
    assert deck.favour() == (set(), 1.0)
    deck.saw(Units.GOLEM)
    assert deck.favour() == (
        {Units.GOLEM, Units.GOLEMITE},
        OpponentDeck.NEW_CARD_WEIGHT,
    )


def test_reset_forgets_the_battle():
    deck = OpponentDeck()
    deck.saw(Units.PEKKA)
    deck.saw(Units.GOBLIN)
    deck.reset()
    assert deck.cards == []
    assert deck.unresolved == set()
    assert Cards.PEKKA not in deck.cards
