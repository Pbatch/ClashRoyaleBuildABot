import itertools
import threading
import time

import pytest

import clashroyalebuildabot.bot.bot as bot_module
from clashroyalebuildabot.actions import (
    ArchersAction,
    BabyDragonAction,
    CannonAction,
    GoblinBarrelAction,
    KnightAction,
    MinipekkaAction,
    MusketeerAction,
    WitchAction,
)
from clashroyalebuildabot.utils.error_handling import WikifiedError
from tests.conftest import default_config

ACTIONS = [
    ArchersAction,
    BabyDragonAction,
    CannonAction,
    GoblinBarrelAction,
    KnightAction,
    MinipekkaAction,
    MusketeerAction,
    WitchAction,
]


class FakeEmulator:
    def __init__(self):
        self.closed = False

    def take_screenshot(self):
        time.sleep(0.01)
        return

    def load_deck(self, cards):
        raise RuntimeError("deck link failed")

    def close(self):
        self.closed = True


class FakeStateReader:
    def run(self, image):
        return None

    def close(self):
        pass


class FakeVisualizer:
    def run(self, image, state):
        pass


def make_config(load_deck=False):
    config = default_config()
    config.bot.auto_start_game = False
    config.bot.load_deck = load_deck
    config.adb.device_serial = "test-device"
    config.ingame.play_action = 1
    return config


def make_bot(device, config=None, state_reader=None, visualizer=None):
    """A bot on ``device``, with a fake state reader and visualizer unless
    others are given."""
    return bot_module.Bot(
        ACTIONS,
        config or make_config(),
        device=device,
        state_reader=state_reader or FakeStateReader(),
        visualizer=visualizer or FakeVisualizer(),
    )


def run_in_thread(bot):
    thread = threading.Thread(target=bot.run, daemon=True)
    thread.start()
    return thread


def test_stop_ends_run_and_closes_emulator():
    emulator = FakeEmulator()
    bot = make_bot(emulator)
    thread = run_in_thread(bot)

    bot.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert emulator.closed


def test_stop_interrupts_a_long_wait():
    bot = make_bot(FakeEmulator())
    thread = threading.Thread(
        target=bot._log_and_wait, args=("Waiting", 30), daemon=True
    )
    thread.start()

    bot.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()


def test_paused_bot_does_not_step(monkeypatch):
    bot = make_bot(FakeEmulator())
    steps = []
    monkeypatch.setattr(bot, "step", lambda state: steps.append(state))

    bot.pause()
    thread = run_in_thread(bot)
    time.sleep(0.3)
    assert steps == []

    bot.resume()
    time.sleep(0.1)
    bot.stop()
    thread.join(timeout=2)
    assert steps


def test_toggle_pause():
    bot = make_bot(FakeEmulator())
    assert not bot.is_paused
    bot.toggle_pause()
    assert bot.is_paused
    bot.toggle_pause()
    assert not bot.is_paused


def test_failed_setup_closes_emulator():
    emulator = FakeEmulator()
    with pytest.raises(RuntimeError, match="deck link failed"):
        make_bot(emulator, make_config(load_deck=True))

    assert emulator.closed


def test_wrong_deck_size_fails_before_creating_the_emulator(monkeypatch):
    # The bot's own StateReader owns the deck-size check, and must fail before
    # the bot makes its own emulator.
    created = []
    monkeypatch.setattr(
        bot_module, "Emulator", lambda **kwargs: created.append(kwargs)
    )

    with pytest.raises(WikifiedError, match="E005"):
        bot_module.Bot(ACTIONS[:7], make_config(), visualizer=FakeVisualizer())

    assert created == []


def _step_times(bot, monkeypatch, seconds, slow_step=None):
    """When each step starts, over seconds of running. slow_step: the index
    of one step that takes 0.35 s."""
    times = []

    def step(state):
        times.append(time.monotonic())
        if len(times) - 1 == slow_step:
            time.sleep(0.35)

    monkeypatch.setattr(bot, "step", step)
    thread = run_in_thread(bot)
    time.sleep(seconds)
    bot.stop()
    thread.join(timeout=2)
    return times


def test_steps_are_capped_at_max_fps(monkeypatch):
    times = _step_times(make_bot(FakeEmulator()), monkeypatch, 1.0)
    # Frames are always ready, so only the cap holds the bot back.
    assert len(times) <= bot_module.MAX_FPS + 1
    gaps = [b - a for a, b in itertools.pairwise(times)]
    assert min(gaps) >= bot_module.STEP_PERIOD * 0.9


def test_a_slow_step_isnt_followed_by_catch_up_steps(monkeypatch):
    times = _step_times(
        make_bot(FakeEmulator()), monkeypatch, 1.0, slow_step=1
    )
    gaps = [b - a for a, b in itertools.pairwise(times)]
    # Every step after the slow one still waits a whole tick.
    assert min(gaps[2:]) >= bot_module.STEP_PERIOD * 0.9
