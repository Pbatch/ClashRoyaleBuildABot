import pytest

from clashroyalebuildabot.actions import (
    FireballAction,
    GiantAction,
    KnightAction,
    MinipekkaAction,
)
from clashroyalebuildabot.actions.generic.bridge_action import (
    LEFT_BRIDGE,
    RIGHT_BRIDGE,
)
from clashroyalebuildabot.constants.device_screen import ALLY_TILES


class TestDefenseAction:
    def test_no_enemies_scores_zero(self, state_factory):
        state = state_factory()
        assert KnightAction(0, 8, 9).calculate_score(state) == [0]

    def test_enemies_on_their_side_are_ignored(
        self, state_factory, unit_factory
    ):
        state = state_factory(enemies=[unit_factory(4, 20)])
        assert KnightAction(0, 8, 9).calculate_score(state) == [0]

    def test_non_defensive_tile_scores_zero(self, state_factory, unit_factory):
        state = state_factory(enemies=[unit_factory(4, 10)])
        assert KnightAction(0, 3, 3).calculate_score(state) == [0]

    @pytest.mark.parametrize(
        ("enemy_x", "good_x", "bad_x"),
        [(4, 8, 9), (13, 9, 8)],
        ids=["threat-left", "threat-right"],
    )
    def test_defends_on_threatened_side(
        self, state_factory, unit_factory, enemy_x, good_x, bad_x
    ):
        state = state_factory(enemies=[unit_factory(enemy_x, 10)])
        assert KnightAction(0, good_x, 9).calculate_score(state) == [1]
        assert KnightAction(0, bad_x, 9).calculate_score(state) == [0]


class TestBridgeAction:
    def test_requires_full_elixir(self, state_factory):
        state = state_factory(elixir=9)
        assert MinipekkaAction(0, *LEFT_BRIDGE).calculate_score(state) == [0]

    def test_prefers_weaker_tower(self, state_factory):
        state = state_factory(elixir=10, left_enemy_hp=0.3, right_enemy_hp=0.8)
        left = MinipekkaAction(0, *LEFT_BRIDGE).calculate_score(state)
        right = MinipekkaAction(0, *RIGHT_BRIDGE).calculate_score(state)
        assert left > right

    @pytest.mark.parametrize("tile", [LEFT_BRIDGE, RIGHT_BRIDGE])
    def test_bridge_tiles_are_always_offered(self, tile):
        # The bot only scores tiles it offers, and the bridge itself isn't
        # offered while the enemy princess tower stands.
        assert list(tile) in ALLY_TILES

    def test_giant_plays_at_bridge(self, state_factory):
        state = state_factory(elixir=10)
        assert GiantAction(0, *LEFT_BRIDGE).calculate_score(state)[0] == 1


class TestSpellAction:
    def test_no_enemies_does_not_fire(self, state_factory):
        state = state_factory()
        assert FireballAction(0, 9, 20).calculate_score(state)[0] == 0

    def test_fires_on_cluster(self, state_factory, unit_factory):
        # Spell hits are offset two tiles down from the target tile.
        enemies = [unit_factory(9, 22) for _ in range(3)]
        state = state_factory(enemies=enemies)
        assert FireballAction(0, 9, 20).calculate_score(state)[0] == 1
