"""The bot only pauses after playing a card, taps go to the device in one
command, and the ONNX models ask for the GPU first."""

import pytest

import clashroyalebuildabot.bot.bot as bot_module
import clashroyalebuildabot.detectors.onnx_detector as onnx_detector
from clashroyalebuildabot.emulator.emulator import Emulator
from clashroyalebuildabot.game.cards import Cards
from tests.conftest import make_state
from tests.test_bot_lifecycle import (
    ACTIONS,
    FakeDetector,
    FakeVisualizer,
    make_config,
)


class TapEmulator:
    def __init__(self, device_serial):
        self.sequences = []

    def tap_sequence(self, points):
        self.sequences.append(list(points))

    def close(self):
        pass


@pytest.fixture
def bot(monkeypatch):
    monkeypatch.setattr(bot_module, "Emulator", TapEmulator)
    monkeypatch.setattr(bot_module, "Detector", FakeDetector)
    monkeypatch.setattr(bot_module, "Visualizer", FakeVisualizer)
    bot = bot_module.Bot(ACTIONS, make_config())
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
    monkeypatch.setattr(bot_module.random, "shuffle", lambda actions: None)
    for action in ACTIONS:
        monkeypatch.setattr(action, "calculate_score", lambda self, s: [0])
    state = make_state(elixir=10, cards=[Cards.KNIGHT] * 5, ready=[0, 1, 2, 3])
    bot._handle_game_step(state)
    assert waits == []


def test_waits_after_playing_a_card(bot, monkeypatch):
    bot, waits = bot
    for action in ACTIONS:
        monkeypatch.setattr(action, "calculate_score", lambda self, s: [1])
    state = make_state(elixir=10, cards=[Cards.KNIGHT] * 5, ready=[0, 1, 2, 3])
    bot._handle_game_step(state)
    assert waits == [bot.play_action_delay]
    # The card, then the tile, in one go.
    assert len(bot.emulator.sequences) == 1
    assert len(bot.emulator.sequences[0]) == 2


def test_taps_are_one_adb_command(monkeypatch):
    emulator = Emulator.__new__(Emulator)
    commands = []
    monkeypatch.setattr(emulator, "_run_command", commands.append)

    emulator.tap_sequence([(10.4, 20.6), (30, 40)])
    emulator.click(5, 6)

    assert commands == [
        ["shell", "input tap 10 21 && input tap 30 40"],
        ["shell", "input tap 5 6"],
    ]


@pytest.mark.parametrize(
    "available, expected",
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
        onnx_detector.ort, "get_available_providers", lambda: available
    )
    monkeypatch.setattr(
        onnx_detector.ort, "preload_dlls", lambda: preloads.append(True)
    )
    onnx_detector._providers.cache_clear()
    try:
        assert onnx_detector._providers() == expected
        assert bool(preloads) == ("CUDAExecutionProvider" in expected)
    finally:
        onnx_detector._providers.cache_clear()
