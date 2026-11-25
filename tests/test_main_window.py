import os
import threading
import time
from typing import ClassVar

import pytest
import yaml

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from loguru import logger
from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import QApplication

import clashroyalebuildabot.bot.controller as controller_module
import clashroyalebuildabot.gui.main_window as main_window_module
from clashroyalebuildabot.config import save_config
from clashroyalebuildabot.utils.error_handling import (
    WikifiedError,
)
from tests.conftest import default_config


class FakeBot:
    """Runs until stopped. `gate` lets a test hold the bot mid-construction."""

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


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch):
    FakeBot.instances = []
    FakeBot.gate = None
    FakeBot.hold = None
    monkeypatch.setattr(controller_module, "Bot", FakeBot)
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
    FakeBot.hold = threading.Event()
    window.start_bot()
    wait_until(lambda: window.controller._bot is not None)
    assert window.is_running
    assert window.server_id_label.text() == "Status - Running"

    window.stop_bot()
    assert window.server_id_label.text() == "Status - Stopping..."
    assert not window.start_stop_button.isEnabled()

    FakeBot.hold.set()
    # is_running clears on the bot's thread; the label follows once the
    # queued status signal reaches the GUI thread.
    wait_until(lambda: window.server_id_label.text() == "Status - Stopped")
    assert window.start_stop_button.isEnabled()
    assert FakeBot.instances[0].finished


def test_cannot_start_while_previous_bot_is_stopping(window):
    FakeBot.hold = threading.Event()
    window.start_bot()
    wait_until(lambda: window.controller._bot is not None)
    window.stop_bot()

    window.start_bot()  # ignored: the first bot hasn't finished yet
    assert len(FakeBot.instances) == 1

    FakeBot.hold.set()
    wait_until(lambda: not window.is_running)
    window.start_bot()
    wait_until(lambda: len(FakeBot.instances) == 2)
    # The bot is handed to the controller just after it's constructed.
    wait_until(lambda: window.controller._bot is FakeBot.instances[1])
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
    wait_until(lambda: window.controller._bot is not None)
    bot = window.controller._bot

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
        wait_until(lambda: window.server_id_label.text() == "Status - Stopped")
    finally:
        logger.remove(sink_id)

    assert window.server_id_label.text() == "Status - Stopped"
    assert any("E008" in m for m in messages)


def test_saving_writes_only_changed_settings(window, tmp_path):
    window.play_action_delay_input.setValue(2.5)
    user_config = tmp_path / "config.yaml"

    save_config(window.config, user_config)

    saved = yaml.safe_load(user_config.read_text(encoding="utf-8"))
    assert saved == {"ingame": {"play_action": 2.5}}


def wait_for_label(window, text):
    wait_until(lambda: window.server_id_label.text() == f"Status - {text}")


def test_pause_shows_in_the_controls(window):
    window.start_bot()
    wait_until(lambda: window.controller._bot is not None)

    window.toggle_pause_resume_and_display()
    assert window.server_id_label.text() == "Status - Paused"
    assert window.play_pause_button.text() == "▶"

    window.toggle_pause_resume_and_display()
    assert window.server_id_label.text() == "Status - Running"
    assert window.play_pause_button.text() == "⏸️"


def test_controls_follow_changes_made_outside_the_window(window):
    """An API driving the controller from another thread must show up in
    the window too."""
    thread = threading.Thread(target=window.controller.start)
    thread.start()
    thread.join()
    wait_for_label(window, "Running")
    assert window.start_stop_button.text() == "■"
    assert window.play_pause_button.isVisibleTo(window)

    wait_until(lambda: window.controller._bot is not None)
    thread = threading.Thread(target=window.controller.stop)
    thread.start()
    thread.join()
    wait_for_label(window, "Stopped")
    assert window.start_stop_button.text() == "▶"
    assert window.start_stop_button.isEnabled()
    assert not window.play_pause_button.isVisibleTo(window)


def test_widget_edits_reach_the_config_straight_away(window):
    config = window.config
    window.load_deck_checkbox.setChecked(not config.bot.load_deck)
    window.log_level_dropdown.setCurrentText("ERROR")
    window.play_action_delay_input.setValue(3.3)
    # Typing sets the text and fires textEdited; setText alone doesn't.
    window.device_serial_input.setText("emulator-5556")
    window.device_serial_input.textEdited.emit("emulator-5556")

    assert config.bot.load_deck == window.load_deck_checkbox.isChecked()
    assert config.bot.log_level == "ERROR"
    assert config.ingame.play_action == 3.3
    assert config.adb.device_serial == "emulator-5556"


def test_widgets_follow_changes_made_elsewhere(window):
    """A PATCH from the API runs on a server thread."""
    changes = {
        "bot": {"log_level": "WARNING", "auto_start_game": True},
        "adb": {"device_serial": "from-the-api"},
        "visuals": {"save_images": True},
        "ingame": {"play_action": 1.7},
    }
    thread = threading.Thread(
        target=window.controller.update_config, args=(changes,)
    )
    thread.start()
    thread.join()
    wait_until(lambda: window.device_serial_input.text() == "from-the-api")

    assert window.log_level_dropdown.currentText() == "WARNING"
    assert window.auto_start_game_checkbox.isChecked()
    assert window.save_images_checkbox.isChecked()
    assert window.play_action_delay_input.value() == pytest.approx(1.7)


def test_showing_a_change_doesnt_send_it_back(window):
    sent = []
    window.controller.update_config = sent.append
    window.config.bot.load_deck = not window.config.bot.load_deck
    window._show_config()
    assert window.load_deck_checkbox.isChecked() == window.config.bot.load_deck
    assert sent == []


def test_starting_doesnt_overwrite_config_from_the_widgets(window):
    """Before, start copied every widget into the config."""
    window.controller.update_config({"adb": {"device_serial": "from-api"}})
    with QSignalBlocker(window.device_serial_input):
        window.device_serial_input.setText("stale")
    window.start_bot()
    wait_until(lambda: len(FakeBot.instances) == 1)
    assert FakeBot.instances[0].config.adb.device_serial == "from-api"


def test_visualizer_notice_follows_show_images(window):
    shown = not window.config.visuals.show_images
    window.show_images_checkbox.setChecked(shown)
    assert window.visualize_tab.inactiveIndicator.isHidden() == shown
