"""The controller runs the bot without any GUI, so these tests need no Qt."""

import threading
import time
from typing import ClassVar

import numpy as np
import pytest

import clashroyalebuildabot.bot.controller as controller_module
from clashroyalebuildabot.bot.controller import BotController, BotStatus
from tests.conftest import default_config


class FakeBot:
    """Runs until stopped. `gate` holds the bot mid-construction."""

    instances: ClassVar[list["FakeBot"]] = []
    gate: ClassVar[threading.Event | None] = None

    def __init__(self, actions, config, on_frame=None):
        if FakeBot.gate is not None:
            FakeBot.gate.wait(timeout=5)
        self.on_frame = on_frame
        self.stopped = threading.Event()
        self.is_paused = False
        self.finished = False
        FakeBot.instances.append(self)

    def run(self):
        self.stopped.wait(timeout=5)
        self.finished = True

    def stop(self):
        self.stopped.set()

    def toggle_pause(self):
        self.is_paused = not self.is_paused


class FakeVLMServer:
    def __init__(self):
        self.ready = threading.Event()
        self.ready.set()
        self.stopped = False

    def ensure_running(self, config, cancelled=lambda: False):
        while not self.ready.wait(0.01):
            if cancelled():
                return False
        return True

    def stop(self):
        self.stopped = True


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
    monkeypatch.setattr(controller_module, "Bot", FakeBot)
    monkeypatch.setattr(controller_module, "VLMServer", FakeVLMServer)
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

    assert controller.stop()
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
    controller.start()
    wait_until(lambda: len(FakeBot.instances) == 1)
    controller.stop()
    assert controller.status == BotStatus.STOPPING
    assert not controller.start()

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


def test_stop_while_the_server_is_starting(controller):
    controller.vlm_server.ready.clear()
    controller.start()
    controller.stop()
    wait_until(lambda: not controller.is_running)
    assert FakeBot.instances == []


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


def test_close_stops_the_bot_and_the_server(controller):
    controller.start()
    wait_until(lambda: len(FakeBot.instances) == 1)
    controller.close()
    assert FakeBot.instances[0].finished
    assert controller.vlm_server.stopped
