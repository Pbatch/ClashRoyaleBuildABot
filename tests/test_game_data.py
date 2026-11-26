import pytest

from clashroyalebuildabot.game import game_data
from clashroyalebuildabot.game.cards import Cards
from clashroyalebuildabot.game.timer import Timer
from clashroyalebuildabot.game.units import Units


def test_knight_matches_the_published_level_11_stats():
    knight = game_data.unit_stats("knight", 11)
    assert (knight["hitpoints"], knight["damage"]) == (1766, 202)


def test_level_1_is_the_stored_value():
    assert game_data.unit_stats("knight", 1)["hitpoints"] == 690


def test_stats_that_dont_grow_with_level_dont():
    low = game_data.unit_stats("musketeer", 1)
    high = game_data.unit_stats("musketeer", 14)
    for key in ("range", "hit_speed", "speed", "deploy_time", "flying"):
        assert low[key] == high[key]
    assert high["hitpoints"] > low["hitpoints"]


def test_every_card_has_data():
    """A card added to game/cards.py needs export_game_data.py re-run."""
    assert {card.name for card in Cards.all()} <= set(game_data.card_names())


def test_summoned_units_are_bot_units():
    names = {unit.name for unit in Units.all()}
    for card in game_data.card_names():
        for summon in game_data.data()["cards"][card]["summons"]:
            assert summon["unit"] is None or summon["unit"] in names


def test_a_card_starts_at_its_rarity_level():
    assert game_data.card_stats("knight", 1)["min_level"] == 1
    assert game_data.card_stats("musketeer")["min_level"] == 3
    with pytest.raises(game_data.BadLevel):
        game_data.card_stats("musketeer", 2)
    # Champions start above the default level.
    assert game_data.card_stats("archer_queen")["level"] == 11
    assert game_data.card_stats("golden_knight")["level"] == 11


def test_a_card_comes_with_its_units_stats():
    card = game_data.card_stats("three_musketeers", 11)
    assert [s["unit"] for s in card["summons"]] == ["musketeer"] * 3
    assert card["summons"][0]["stats"]["level"] == 11
    army = game_data.card_stats("skeleton_army")
    assert army["summons"][0]["count"] == 15


def test_spells_scale_and_hit_towers_for_less():
    fireball = game_data.card_stats("fireball", 11)["spell"]
    assert fireball["damage"] == 269 * 256 // 100
    assert 0 < fireball["crown_tower_damage"] < fireball["damage"]
    assert game_data.card_stats("arrows")["spell"]["waves"] == 3


@pytest.mark.parametrize(
    ("name", "level"), [("knight", 0), ("knight", 99), ("fireball", 0)]
)
def test_levels_out_of_range(name, level):
    get = game_data.card_stats if name == "fireball" else game_data.unit_stats
    with pytest.raises(game_data.BadLevel):
        get(name, level)


def test_unknown_names():
    with pytest.raises(game_data.UnknownName):
        game_data.unit_stats("dragon_knight")
    with pytest.raises(game_data.UnknownName):
        game_data.card_stats("dragon_knight")


@pytest.mark.parametrize(
    ("timer", "expected"),
    [
        (Timer(), None),
        (Timer(time_left=180), 2.8),
        (Timer(time_left=61), 2.8),
        # The last minute of regulation time is double elixir...
        (Timer(time_left=60), 1.4),
        # ...and so is the first minute of overtime...
        (Timer(time_left=120, overtime=True), 1.4),
        # ...and the last is triple.
        (Timer(time_left=59, overtime=True), 0.93),
        (Timer(time_left=0, overtime=True), 0.93),
    ],
)
def test_elixir_rate_follows_the_timer(timer, expected):
    assert game_data.seconds_per_elixir(timer) == expected


def test_tower_level_from_princess_hp():
    # Seen in real battles: level 9 and 11 princess towers.
    assert game_data.tower_level(2534) == 9
    assert game_data.tower_level(3052) == 11
    assert game_data.tower_level(3051) is None
    assert game_data.king_hitpoints(11) == 4824
    assert game_data.king_hitpoints(99) is None
    # Level 1 matches the game's files.
    assert (
        game_data.king_hitpoints(1)
        == game_data.towers()["king"]["hitpoints_level_1"]
    )
    assert (
        game_data.TOWER_HITPOINTS["princess"][0]
        == (game_data.towers()["princess"]["hitpoints_level_1"])
    )
