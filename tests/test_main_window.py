import copy
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
from clashroyalebuildabot.gui.utils import (  # noqa: E402
    load_config,
    save_config,
)
from clashroyalebuildabot.utils.error_handling import (
    WikifiedError,  # noqa: E402
)


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


@pytest.fixture
def window(qapp, monkeypatch):
    FakeBot.instances = []
    FakeBot.gate = None
    monkeypatch.setattr(main_window_module, "Bot", FakeBot)
    monkeypatch.setattr(
        main_window_module.keyboard, "add_hotkey", lambda *args: None
    )
    # Defaults only, so a local config.yaml can't affect the tests.
    config = load_config(user_config_path=os.devnull + ".missing")
    win = main_window_module.MainWindow(copy.deepcopy(config), [])
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
    screen = window.config["screen_detector"]
    assert window.screen_server_url_input.text() == screen["base_url"]
    assert window.screen_min_confidence_input.value() == pytest.approx(
        screen["min_confidence"]
    )
    assert window.screen_interval_input.value() == pytest.approx(
        screen["interval"]
    )
    assert window.screen_max_age_input.value() == pytest.approx(
        screen["max_age"]
    )
    assert window.screen_timeout_input.value() == pytest.approx(
        screen["timeout"]
    )


def test_screen_detector_settings_update_config(window):
    window.screen_server_url_input.setText(" http://gpu-box:9000 ")
    window.screen_min_confidence_input.setValue(0.7)
    window.screen_interval_input.setValue(2.5)
    window.screen_max_age_input.setValue(8)
    window.screen_timeout_input.setValue(20)

    screen = window.update_config()["screen_detector"]

    assert screen == {
        "base_url": "http://gpu-box:9000",
        "min_confidence": 0.7,
        "interval": 2.5,
        "max_age": 8.0,
        "timeout": 20.0,
    }


def test_empty_server_url_keeps_current_address(window):
    before = window.config["screen_detector"]["base_url"]
    window.screen_server_url_input.setText("   ")
    assert window.update_config()["screen_detector"]["base_url"] == before


def test_saving_writes_only_changed_screen_settings(window, tmp_path):
    window.screen_min_confidence_input.setValue(0.8)
    user_config = tmp_path / "config.yaml"

    save_config(window.update_config(), user_config)

    saved = yaml.safe_load(user_config.read_text(encoding="utf-8"))
    assert saved == {"screen_detector": {"min_confidence": 0.8}}
