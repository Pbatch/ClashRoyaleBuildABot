import os
import threading
import time
from types import SimpleNamespace

import pytest
import yaml

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from loguru import logger  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import clashroyalebuildabot.gui.main_window as main_window_module  # noqa: E402
from clashroyalebuildabot.config import save_config  # noqa: E402
from clashroyalebuildabot.utils.error_handling import (
    WikifiedError,  # noqa: E402
)
from tests.conftest import default_config  # noqa: E402


class FakeBot:
    """Runs until stopped. `gate` lets a test hold the bot mid-construction."""

    instances: list["FakeBot"] = []
    gate: threading.Event | None = None

    def __init__(self, actions, config):
        if FakeBot.gate is not None:
            FakeBot.gate.wait(timeout=5)
        self.visualizer = SimpleNamespace(
            frame_ready=SimpleNamespace(connect=lambda slot: None)
        )
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


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


class FakeVLMServer:
    """Stands in for the vision model server, so tests never start vLLM.
    ``ready`` is whether it's up; until then, ensure_running waits."""

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


@pytest.fixture
def window(qapp, monkeypatch):
    FakeBot.instances = []
    FakeBot.gate = None
    monkeypatch.setattr(main_window_module, "Bot", FakeBot)
    monkeypatch.setattr(main_window_module, "VLMServer", FakeVLMServer)
    monkeypatch.setattr(
        main_window_module.keyboard, "add_hotkey", lambda *args: None
    )
    # Defaults only, so a local config.yaml can't affect the tests.
    win = main_window_module.MainWindow(default_config(), [])
    yield win
    win.close()


def wait_until(condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError("condition not met in time")


def test_start_then_stop(window):
    window.start_bot()
    wait_until(lambda: window.bot is not None)
    assert window.is_running
    assert window.server_id_label.text() == "Status - Running"

    window.stop_bot()
    assert window.server_id_label.text() == "Status - Stopping..."
    assert not window.start_stop_button.isEnabled()

    wait_until(lambda: not window.is_running)
    assert window.bot is None
    assert window.server_id_label.text() == "Status - Stopped"
    assert window.start_stop_button.isEnabled()
    assert FakeBot.instances[0].finished


def test_cannot_start_while_previous_bot_is_stopping(window):
    window.start_bot()
    wait_until(lambda: window.bot is not None)
    window.stop_bot()

    window.start_bot()  # ignored: the first bot hasn't finished yet
    assert len(FakeBot.instances) == 1

    wait_until(lambda: not window.is_running)
    window.start_bot()
    wait_until(lambda: len(FakeBot.instances) == 2)
    assert window.bot is FakeBot.instances[1]
    assert not FakeBot.instances[1].stopped.is_set()


def test_stop_while_bot_is_being_created(window):
    FakeBot.gate = threading.Event()
    window.start_bot()
    window.stop_bot()  # bot not created yet, so there's nothing to call stop() on

    FakeBot.gate.set()
    wait_until(lambda: not window.is_running)
    assert FakeBot.instances[0].stopped.is_set()


def test_bot_waits_for_the_vision_model_server(window):
    window.vlm_server.ready.clear()
    window.start_bot()
    time.sleep(0.1)
    assert FakeBot.instances == []

    window.vlm_server.ready.set()
    wait_until(lambda: len(FakeBot.instances) == 1)


def test_stop_while_the_server_is_starting(window):
    window.vlm_server.ready.clear()
    window.start_bot()
    window.stop_bot()
    wait_until(lambda: not window.is_running)
    assert FakeBot.instances == []  # no bot was created


def test_closing_window_stops_the_server(window):
    window.close()
    assert window.vlm_server.stopped


def test_logs_from_other_threads_reach_the_log_panel(window):
    sink_id = logger.add(window.log_handler_function)
    try:
        thread = threading.Thread(target=lambda: logger.info("hello from bot"))
        thread.start()
        thread.join()
        wait_until(
            lambda: "hello from bot" in window.log_display.toPlainText()
        )
    finally:
        logger.remove(sink_id)


def test_closing_window_stops_running_bot(window):
    window.start_bot()
    wait_until(lambda: window.bot is not None)
    bot = window.bot

    window.close()

    assert bot.stopped.is_set()
    assert bot.finished


def test_bot_error_is_logged_and_window_resets(window, monkeypatch):
    def failing_run(self):
        raise WikifiedError("008", "Lost the video stream from the device.")

    monkeypatch.setattr(FakeBot, "run", failing_run)
    messages = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]))
    try:
        window.start_bot()
        wait_until(lambda: not window.is_running)
    finally:
        logger.remove(sink_id)

    assert window.server_id_label.text() == "Status - Stopped"
    assert any("E008" in m for m in messages)


def test_screen_detector_settings_show_config_values(window):
    screen = window.config.screen_detector
    assert window.screen_server_url_input.text() == screen.base_url
    assert window.screen_model_input.text() == screen.model
    assert window.screen_interval_input.value() == pytest.approx(
        screen.interval
    )
    assert window.screen_max_age_input.value() == pytest.approx(screen.max_age)
    assert window.screen_timeout_input.value() == pytest.approx(screen.timeout)


def test_screen_detector_settings_update_config(window):
    window.screen_server_url_input.setText(" http://gpu-box:9000 ")
    window.screen_model_input.setText(" Qwen/Qwen3.5-2B ")
    window.screen_interval_input.setValue(2.5)
    window.screen_max_age_input.setValue(8)
    window.screen_timeout_input.setValue(20)

    screen = window.update_config().screen_detector.model_dump()

    expected = {
        "base_url": "http://gpu-box:9000",
        "model": "Qwen/Qwen3.5-2B",
        "interval": 2.5,
        "max_age": 8.0,
        "timeout": 20.0,
    }
    # The server settings without a box in the GUI keep their values.
    assert {key: screen[key] for key in expected} == expected


def test_empty_server_url_keeps_current_address(window):
    before = window.config.screen_detector.base_url
    window.screen_server_url_input.setText("   ")
    assert window.update_config().screen_detector.base_url == before


def test_saving_writes_only_changed_screen_settings(window, tmp_path):
    window.screen_interval_input.setValue(2.5)
    user_config = tmp_path / "config.yaml"

    save_config(window.update_config(), user_config)

    saved = yaml.safe_load(user_config.read_text(encoding="utf-8"))
    assert saved == {"screen_detector": {"interval": 2.5}}
