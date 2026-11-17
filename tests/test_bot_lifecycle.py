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
    instances: list["FakeEmulator"] = []

    def __init__(self, device_serial):
        self.device_serial = device_serial
        self.closed = False
        FakeEmulator.instances.append(self)

    def take_screenshot(self):
        time.sleep(0.01)
        return None

    def load_deck(self, cards):
        raise RuntimeError("deck link failed")

    def close(self):
        self.closed = True


class FakeDetector:
    def __init__(self, cards, screen_config=None):
        pass

    def close(self):
        pass


class FakeVisualizer:
    def __init__(self, **kwargs):
        pass


def make_config(load_deck=False):
    return {
        "bot": {"auto_start_game": False, "load_deck": load_deck},
        "adb": {"device_serial": "test-device"},
        "visuals": {},
        "ingame": {"play_action": 1},
    }


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    FakeEmulator.instances = []
    monkeypatch.setattr(bot_module, "Emulator", FakeEmulator)
    monkeypatch.setattr(bot_module, "Detector", FakeDetector)
    monkeypatch.setattr(bot_module, "Visualizer", FakeVisualizer)


def run_in_thread(bot):
    thread = threading.Thread(target=bot.run, daemon=True)
    thread.start()
    return thread


def test_stop_ends_run_and_closes_emulator():
    bot = bot_module.Bot(ACTIONS, make_config())
    thread = run_in_thread(bot)

    bot.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert FakeEmulator.instances[0].closed


def test_stop_interrupts_a_long_wait():
    bot = bot_module.Bot(ACTIONS, make_config())
    thread = threading.Thread(
        target=bot._log_and_wait, args=("Waiting", 30), daemon=True
    )
    thread.start()

    bot.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()


def test_paused_bot_does_not_step(monkeypatch):
    bot = bot_module.Bot(ACTIONS, make_config())
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
    bot = bot_module.Bot(ACTIONS, make_config())
    assert not bot.is_paused
    bot.toggle_pause()
    assert bot.is_paused
    bot.toggle_pause()
    assert not bot.is_paused


def test_failed_setup_closes_emulator():
    with pytest.raises(RuntimeError, match="deck link failed"):
        bot_module.Bot(ACTIONS, make_config(load_deck=True))

    assert len(FakeEmulator.instances) == 1
    assert FakeEmulator.instances[0].closed


def test_wrong_deck_size_fails_before_creating_the_emulator(monkeypatch):
    # Use the real Detector, which owns the deck-size check.
    from clashroyalebuildabot.detectors.detector import Detector

    monkeypatch.setattr(bot_module, "Detector", Detector)

    with pytest.raises(WikifiedError, match="E005"):
        bot_module.Bot(ACTIONS[:7], make_config())

    assert FakeEmulator.instances == []
