"""The bot only pauses after playing a card, and the ONNX models ask for
the GPU first. Taps are tested in test_input_shell.py."""

import pytest

import clashroyalebuildabot.bot.bot as bot_module
import clashroyalebuildabot.bot.policy as policy_module
import clashroyalebuildabot.detectors.onnx_model as onnx_model
from clashroyalebuildabot.game.cards import Cards
from tests.conftest import make_state
from tests.test_bot_lifecycle import ACTIONS, make_bot


class TapEmulator:
    def __init__(self):
        self.sequences = []

    def tap_sequence(self, points):
        self.sequences.append(list(points))

    def close(self):
        pass


@pytest.fixture
def bot(monkeypatch):
    bot = make_bot(TapEmulator())
    waits: list[float] = []
    monkeypatch.setattr(
        bot, "_log_and_wait", lambda prefix, delay: waits.append(delay)
    )
    return bot, waits


def test_no_wait_without_affordable_cards(bot):
    bot, waits = bot
    bot._handle_game_step(make_state(elixir=0))
    assert waits == []
    assert bot.emulator.sequences == []


def test_no_wait_without_a_good_action(bot, monkeypatch):
    bot, waits = bot
    monkeypatch.setattr(policy_module.random, "shuffle", lambda actions: None)
    for action in ACTIONS:
        monkeypatch.setattr(action, "calculate_score", lambda self, s: [0])
    state = make_state(elixir=10, cards=[Cards.KNIGHT] * 5, ready=[0, 1, 2, 3])
    bot._handle_game_step(state)
    assert waits == []


# The next card, then the hand. Hand position 0 holds the knight.
HAND = [
    Cards.ARCHERS,
    Cards.KNIGHT,
    Cards.CANNON,
    Cards.WITCH,
    Cards.MUSKETEER,
]


@pytest.fixture
def playing(bot, monkeypatch):
    """Every action scores well, the bot can only play hand position 0,
    and the clock is under the test's control."""
    bot, waits = bot
    for action in ACTIONS:
        monkeypatch.setattr(action, "calculate_score", lambda self, s: [1])
    clock = [100.0]
    monkeypatch.setattr(bot_module.time, "monotonic", lambda: clock[0])
    return bot, waits, clock


def battle_frame(cards=HAND, elixir=10):
    return make_state(elixir=elixir, cards=list(cards), ready=[0])


def test_plays_a_card_without_sleeping(playing):
    bot, waits, _ = playing
    bot._handle_game_step(battle_frame())
    assert waits == []
    # The card, then the tile, in one go.
    assert len(bot.emulator.sequences) == 1
    assert len(bot.emulator.sequences[0]) == 2
    assert bot.pending_play.card == Cards.KNIGHT


def test_does_not_play_again_until_the_card_shows_played(playing):
    bot, _, clock = playing
    bot._handle_game_step(battle_frame())
    clock[0] += 0.5
    # The frame still shows the knight in hand and the elixir unspent.
    bot._handle_game_step(battle_frame())
    assert len(bot.emulator.sequences) == 1


def test_plays_again_once_the_card_leaves_the_hand(playing):
    bot, _, clock = playing
    bot._handle_game_step(battle_frame())
    clock[0] += 0.2
    # The next card, archers, has taken the knight's place.
    bot._handle_game_step(
        battle_frame(cards=[Cards.WITCH, *HAND[0:1], *HAND[2:]])
    )
    assert len(bot.emulator.sequences) == 2
    assert bot.pending_play.card == Cards.ARCHERS


def test_plays_again_once_elixir_drops(playing):
    bot, _, clock = playing
    bot._handle_game_step(battle_frame(elixir=10))
    clock[0] += 0.2
    bot._handle_game_step(battle_frame(elixir=7))
    assert len(bot.emulator.sequences) == 2


def test_stops_waiting_after_the_delay(playing):
    # E.g. the tap missed, so the card never leaves the hand.
    bot, _, clock = playing
    bot._handle_game_step(battle_frame())
    clock[0] += bot.play_action_delay
    bot._handle_game_step(battle_frame())
    assert len(bot.emulator.sequences) == 2


@pytest.mark.parametrize(
    ("available", "expected"),
    [
        (
            [
                "TensorrtExecutionProvider",
                "CPUExecutionProvider",
                "CUDAExecutionProvider",
            ],
            ["CUDAExecutionProvider", "CPUExecutionProvider"],
        ),
        (["CPUExecutionProvider"], ["CPUExecutionProvider"]),
    ],
)
def test_providers_put_cuda_first(monkeypatch, available, expected):
    preloads = []
    monkeypatch.setattr(
        onnx_model.ort, "get_available_providers", lambda: available
    )
    monkeypatch.setattr(
        onnx_model.ort, "preload_dlls", lambda: preloads.append(True)
    )
    onnx_model._providers.cache_clear()
    try:
        assert onnx_model._providers() == expected
        assert bool(preloads) == ("CUDAExecutionProvider" in expected)
    finally:
        onnx_model._providers.cache_clear()
