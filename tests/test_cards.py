"""The card and unit tables in game/cards.py and game/units.py."""

import pytest

from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.units import Units


@pytest.mark.parametrize("table", [Cards, Units], ids=["cards", "units"])
def test_names_match_their_attributes(table):
    wrong = [
        (attr, entry.name)
        for attr, entry in vars(table).items()
        if not attr.startswith("_") and entry.name != attr.lower()
    ]
    assert not wrong


@pytest.mark.parametrize("table", [Cards, Units], ids=["cards", "units"])
def test_names_are_unique(table):
    names = [entry.name for entry in table.all()]
    assert len(names) == len(set(names))


def test_card_ids_are_unique():
    ids = [card.id_ for card in Cards.all()]
    assert len(ids) == len(set(ids))


def test_costs_are_affordable():
    # Mirror costs one more than the card it copies, so it has no fixed cost.
    fixed = [card for card in Cards.all() if card != Cards.MIRROR]
    assert all(1 <= card.cost <= 10 for card in fixed)


def test_card_units_are_known():
    units = set(Units.all())
    unknown = [
        (card.name, unit.name)
        for card in Cards.all()
        for unit in card.units
        if unit not in units
    ]
    assert not unknown


@pytest.mark.parametrize("table", [Cards, Units], ids=["cards", "units"])
def test_by_name(table):
    for entry in table.all():
        assert table.by_name(entry.name) is entry
    with pytest.raises(KeyError):
        table.by_name("no_such_thing")
