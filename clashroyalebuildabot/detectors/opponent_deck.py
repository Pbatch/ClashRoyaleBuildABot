"""Work out the opponent's cards from the units they put down.

There's no seeing the opponent's hand, so their deck is learnt the way a
player learns it: a unit of theirs that has been seen as the same unit for
a while names the card that played it. Most units come from one card; a unit
several cards make (a goblin: Goblins, Goblin Gang, Goblin Barrel, Goblin
Drill) stays unresolved until a card of theirs that makes it is known.

Spells leave no units, so they're never known, and the deck is rarely
complete: it's complete once the cards known and the fewest cards that
make the unresolved units fill a deck.

The unit detector and tracker use this to name the opponent's units (see
favour): they favour their known cards' units, and once their deck is
complete, they name only those.
"""

from collections.abc import Iterable
from itertools import combinations
from typing import TYPE_CHECKING

from loguru import logger

from clashroyalebuildabot.detectors.unit_tracker import ENEMY
from clashroyalebuildabot.game.cards import DECK_SIZE, Card, Cards
from clashroyalebuildabot.game.units import Unit

if TYPE_CHECKING:
    from clashroyalebuildabot.detectors.unit_tracker import Track

# The cards that put each unit on the battlefield.
CARDS_OF: dict[Unit, tuple[Card, ...]] = {}
for _card in Cards.all():
    for _unit in _card.units:
        CARDS_OF[_unit] = (*CARDS_OF.get(_unit, ()), _card)


class OpponentDeck:
    """The opponent's cards seen so far this battle. Call ``reset`` between
    battles."""

    # A track of theirs counts once it's been detected this many times. It
    # counts as the unit its scores over all those frames say it is
    # (Track.best_unit), which is checked again every frame: a unit is
    # often misnamed for its first few frames, as it's deployed (on a
    # recorded battle, a Dark Prince was a Rascal Boy for 4 frames before
    # it was a Dark Prince for 16), so a card it was wrongly counted for is
    # dropped once it's seen better.
    MIN_FRAMES = 5
    # A unit names a card once it's been seen in two plays: tracks that
    # started at least this far apart, in seconds. A card is played again
    # within a cycle of the deck, while a unit misread as theirs for one
    # track (on a recorded battle, our Baby Dragon under their Goblin
    # Giant) would otherwise fill their deck with a card they don't have.
    # A unit's track that breaks and starts again in the same fight
    # doesn't count twice.
    REPLAY_GAP = 5.0
    # How much an enemy unit from a card the opponent hasn't been seen to
    # play is rated, against one from a card they have (see favour).
    NEW_CARD_WEIGHT = 0.5

    def __init__(self) -> None:
        self.cards: list[Card] = []  # in the order they were found
        # Units seen whose card isn't known yet: more than one card makes
        # them, and none of those is known.
        self.unresolved: set[Unit] = set()
        # What each of their tracks is, and when it started, by track id,
        # in the order they were first counted. Sightings from saw() have
        # negative ids and no start: they count as sure.
        self._seen: dict[int, tuple[Unit, float | None]] = {}

    def reset(self) -> None:
        self.cards = []
        self.unresolved = set()
        self._seen = {}

    def update(self, tracks: Iterable["Track"]) -> None:
        """Learn from the tracked units after a frame: the opponent's that
        have been detected at least MIN_FRAMES times."""
        changed = False
        for track in tracks:
            if track.ally or track.hits < self.MIN_FRAMES:
                continue
            seen = (track.best_unit(ENEMY, recent=False), track.born)
            if self._seen.get(track.id) != seen:
                self._seen[track.id] = seen
                changed = True
        if changed:
            self._rebuild()

    def saw(self, unit: Unit) -> None:
        """Count a unit the opponent surely played."""
        self._seen[-1 - len(self._seen)] = (unit, None)
        self._rebuild()

    def favour(self) -> tuple[set[Unit], float]:
        """How to name the opponent's units: (favoured, others) for
        Track.best_unit and UnitDetector.name_enemies. Their known cards'
        units are favoured, and others rated at NEW_CARD_WEIGHT, or not at
        all once their deck is complete. Knowing nothing, nothing is."""
        possible = self.possible_units()
        if not possible:
            return set(), 1.0
        return possible, 0.0 if self.complete else self.NEW_CARD_WEIGHT

    def _rebuild(self) -> None:
        """Work out their cards from what every track was seen as. A unit
        seen in two plays (REPLAY_GAP) and made by one card names it; a
        card named by more tracks than another is kept first, should the
        units seen name more cards than a deck holds (some must be
        misnamed)."""
        support: dict[Card, int] = {}
        ambiguous: list[Unit] = []
        for unit in self._played_twice():
            cards = CARDS_OF.get(unit, ())
            if len(cards) == 1:
                support[cards[0]] = support.get(cards[0], 0) + sum(
                    u == unit for u, _ in self._seen.values()
                )
            elif cards:
                ambiguous.append(unit)
        cards = list(support)  # first seen first
        if len(cards) > DECK_SIZE:
            kept = sorted(cards, key=lambda c: -support[c])[:DECK_SIZE]
            logger.debug(
                f"Units name {len(cards)} opponent cards, more than a "
                f"deck: dropping {[c.name for c in cards if c not in kept]}"
            )
            cards = [c for c in cards if c in kept]
        for card in cards:
            if card not in self.cards:
                logger.info(f"Opponent plays {card.name}")
        self.cards = cards
        self.unresolved = {u for u in ambiguous if not self._made_by_known(u)}

    def _played_twice(self) -> list[Unit]:
        """The units seen in two plays, or surely played (saw), in the order
        they were first seen."""
        starts: dict[Unit, list[float | None]] = {}
        for unit, born in self._seen.values():
            starts.setdefault(unit, []).append(born)
        units = []
        for unit, born in starts.items():
            times = [t for t in born if t is not None]
            sure = len(times) < len(born)
            if sure or max(times) - min(times) >= self.REPLAY_GAP:
                units.append(unit)
        return units

    @property
    def complete(self) -> bool:
        """Whether every card of theirs that makes units is known: the deck
        has no room for another."""
        return len(self.cards) + len(self._cover()) >= DECK_SIZE

    def possible_units(self) -> set[Unit]:
        """The units their known cards make, plus the unresolved units.
        Once the deck is complete, any unit the opponent can play is one
        of these, as the unresolved units must come from one of their
        cards and every card that makes them is counted."""
        units = {unit for card in self.cards for unit in card.units}
        units |= self.unresolved
        if self.complete:
            for unit in self.unresolved:
                for card in CARDS_OF[unit]:
                    units.update(card.units)
        return units

    def _made_by_known(self, unit: Unit) -> bool:
        return any(unit in card.units for card in self.cards)

    def _cover(self) -> tuple[Card, ...]:
        """The fewest cards that make every unresolved unit. There are only
        ever a handful of unresolved units, so every set of their cards is
        tried, smallest first."""
        candidates = sorted(
            {c for u in self.unresolved for c in CARDS_OF[u]},
            key=lambda c: c.name,
        )
        for size in range(len(self.unresolved) + 1):
            for cover in combinations(candidates, size):
                made = {u for card in cover for u in card.units}
                if self.unresolved <= made:
                    return cover
        raise AssertionError("every unresolved unit has a card")
