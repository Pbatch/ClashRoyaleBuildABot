"""The controller runs the bot without any GUI, so these tests need no Qt."""

import threading
import time
from typing import ClassVar

import numpy as np
import pytest
from pydantic import ValidationError

import clashroyalebuildabot.bot.controller as controller_module
from clashroyalebuildabot.bot.controller import BotController, BotStatus
from tests.conftest import default_config


class FakeBot:
    """Runs until stopped. `gate` holds the bot mid-construction."""

    instances: ClassVar[list["FakeBot"]] = []
    gate: ClassVar[threading.Event | None] = None
    # When set, run() keeps going after stop() until it's released.
    hold: ClassVar[threading.Event | None] = None

    def __init__(self, actions, config, on_frame=None):
        if FakeBot.gate is not None:
            FakeBot.gate.wait(timeout=5)
        self.on_frame = on_frame
        self.config = config
        self.stopped = threading.Event()
        self.is_paused = False
        self.finished = False
        FakeBot.instances.append(self)

    def run(self):
        self.stopped.wait(timeout=5)
        if FakeBot.hold is not None:
            FakeBot.hold.wait(timeout=5)
        self.finished = True

    def stop(self):
        self.stopped.set()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False


def wait_until(condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError("condition not met in time")


@pytest.fixture
def controller(monkeypatch):
    FakeBot.instances = []
    FakeBot.gate = None
    FakeBot.hold = None
    monkeypatch.setattr(controller_module, "Bot", FakeBot)
    ctrl = BotController(default_config(), [])
    yield ctrl
    ctrl.close(timeout=5)


def test_start_pause_stop(controller):
    statuses = []
    controller.add_status_listener(statuses.append)

    assert controller.start()
    wait_until(lambda: controller._bot is not None)
    assert controller.status == BotStatus.RUNNING

    assert controller.toggle_pause() is True
    assert controller.status == BotStatus.PAUSED
    assert controller.toggle_pause() is False

    FakeBot.hold = threading.Event()
    assert controller.stop()
    FakeBot.hold.set()
    wait_until(lambda: not controller.is_running)
    wait_until(lambda: statuses[-1] == BotStatus.STOPPED)
    assert statuses == [
        BotStatus.RUNNING,
        BotStatus.PAUSED,
        BotStatus.RUNNING,
        BotStatus.STOPPING,
        BotStatus.STOPPED,
    ]
    assert FakeBot.instances[0].finished


def test_second_start_is_refused_until_the_first_bot_finishes(controller):
    FakeBot.hold = threading.Event()
    controller.start()
    wait_until(lambda: controller._bot is not None)
    controller.stop()
    assert controller.status == BotStatus.STOPPING
    assert not controller.start()
    FakeBot.hold.set()

    wait_until(lambda: not controller.is_running)
    assert controller.start()
    wait_until(lambda: len(FakeBot.instances) == 2)


def test_stop_while_bot_is_being_created(controller):
    FakeBot.gate = threading.Event()
    controller.start()
    controller.stop()  # nothing to call stop() on yet

    FakeBot.gate.set()
    wait_until(lambda: not controller.is_running)
    assert FakeBot.instances[0].stopped.is_set()


def test_frames_reach_listeners(controller):
    frames = []
    controller.add_frame_listener(frames.append)
    controller.start()
    wait_until(lambda: len(FakeBot.instances) == 1)

    frame = np.zeros((4, 4, 3), np.uint8)
    on_frame = FakeBot.instances[0].on_frame
    assert on_frame is not None
    on_frame(frame)
    assert frames == [frame]


def test_crash_is_logged_and_listeners_still_run(controller, monkeypatch):
    def failing_run(self):
        raise RuntimeError("boom")

    monkeypatch.setattr(FakeBot, "run", failing_run)
    statuses = []
    controller.add_status_listener(statuses.append)
    controller.start()
    wait_until(lambda: statuses[-1] == BotStatus.STOPPED)
    assert controller.status == BotStatus.STOPPED


def test_close_stops_the_bot(controller):
    controller.start()
    wait_until(lambda: len(FakeBot.instances) == 1)
    controller.close()
    assert FakeBot.instances[0].finished


def test_last_status_reported_is_the_current_one(controller):
    """The bot may finish while stop() is still reporting STOPPING. The
    listener must still end up with STOPPED."""
    for _ in range(20):
        statuses = []
        controller._status_listeners = [statuses.append]
        controller.start()
        wait_until(lambda: controller._bot is not None)
        controller.stop()  # FakeBot.run returns at once
        wait_until(lambda: not controller.is_running)
        assert statuses[-1] == BotStatus.STOPPED


def test_config_changes_reach_listeners(controller):
    seen = []
    controller.add_config_listener(
        lambda config: seen.append(config.bot.load_deck)
    )
    controller.update_config({"bot": {"load_deck": True}})
    assert controller.config.bot.load_deck is True
    assert seen == [True]


def test_invalid_config_changes_nothing_and_tells_no_one(controller):
    seen = []
    controller.add_config_listener(seen.append)
    before = controller.config.model_dump()
    with pytest.raises(ValidationError):
        controller.update_config(
            {"bot": {"load_deck": True}, "ingame": {"play_action": 0}}
        )
    assert controller.config.model_dump() == before
    assert seen == []


def test_a_running_bot_keeps_the_config_it_started_with(controller):
    controller.update_config({"adb": {"device_serial": "first"}})
    controller.start()
    wait_until(lambda: len(FakeBot.instances) == 1)
    controller.update_config({"adb": {"device_serial": "second"}})

    assert FakeBot.instances[0].config.adb.device_serial == "first"
    assert controller.config.adb.device_serial == "second"
