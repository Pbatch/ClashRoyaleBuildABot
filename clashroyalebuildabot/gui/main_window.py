from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import keyboard
import numpy as np
from loguru import logger
from PyQt6.QtCore import QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clashroyalebuildabot.actions.generic.action import Action
from clashroyalebuildabot.bot.controller import BotController, BotStatus
from clashroyalebuildabot.config import Config, LogLevel
from clashroyalebuildabot.gui.animations import start_play_button_animation
from clashroyalebuildabot.gui.gameplay_widget import ImageStreamWindow
from clashroyalebuildabot.gui.layout_setup import setup_tabs, setup_top_bar
from clashroyalebuildabot.gui.styles import set_styles
from clashroyalebuildabot.utils.error_handling import WikifiedError
from clashroyalebuildabot.utils.logger import colorize_log, setup_logger

if TYPE_CHECKING:
    from loguru import Message


PAUSE_HOTKEY = "ctrl+p"

STATUS_LABELS = {
    BotStatus.STOPPED: "Stopped",
    BotStatus.RUNNING: "Running",
    BotStatus.PAUSED: "Paused",
    BotStatus.STOPPING: "Stopping...",
}


class MainWindow(QMainWindow):
    # Other threads never touch widgets directly. They emit these signals,
    # and Qt runs the connected slots on the GUI thread.
    # (The ignores work around PyQt6 6.12's stubs, which wrongly mark the
    # optional `arguments` parameter of pyqtSignal as required.)
    log_received = pyqtSignal(str)  # ty: ignore[missing-argument]
    status_changed = pyqtSignal()  # ty: ignore[missing-argument]
    frame_received = pyqtSignal(np.ndarray)  # ty: ignore[missing-argument]
    pause_hotkey_pressed = pyqtSignal()  # ty: ignore[missing-argument]

    # Widgets attached by layout_setup.py and animations.py
    server_id_label: QLabel
    play_pause_button: QPushButton
    start_stop_button: QPushButton
    log_display: QTextEdit
    visualize_tab: ImageStreamWindow
    log_level_dropdown: QComboBox
    device_serial_input: QLineEdit
    save_labels_checkbox: QCheckBox
    save_images_checkbox: QCheckBox
    show_images_checkbox: QCheckBox
    play_action_delay_input: QDoubleSpinBox
    load_deck_checkbox: QCheckBox
    auto_start_game_checkbox: QCheckBox
    screen_server_url_input: QLineEdit
    screen_model_input: QLineEdit
    screen_interval_input: QDoubleSpinBox
    screen_max_age_input: QDoubleSpinBox
    screen_timeout_input: QDoubleSpinBox
    glow_effect: QGraphicsDropShadowEffect
    glow_animation: QPropertyAnimation

    def __init__(
        self, config: Config, actions: Sequence[type[Action]]
    ) -> None:
        try:
            super().__init__()
            self.config = config
            self.controller = BotController(config, actions)
            self._shown_status: BotStatus | None = None

            self.setWindowTitle(" ")
            self.setGeometry(100, 100, 900, 600)

            transparent_pixmap = QPixmap(1, 1)
            transparent_pixmap.fill(Qt.GlobalColor.transparent)
            self.setWindowIcon(QIcon(transparent_pixmap))

            main_widget = QWidget(self)
            self.setCentralWidget(main_widget)
            main_layout = QVBoxLayout(main_widget)

            top_bar = setup_top_bar(self)
            tab_widget = setup_tabs(self)

            main_layout.addWidget(top_bar)
            main_layout.addWidget(tab_widget)

            set_styles(self)
            start_play_button_animation(self)

            self.log_received.connect(self._append_log)
            self.status_changed.connect(self._show_status)
            self.frame_received.connect(self.visualize_tab.update_frame)
            # The controller may call these on the bot's thread; the signals
            # carry them over to the GUI thread. (Emitted on the GUI thread,
            # they run straight away.)
            self.controller.add_status_listener(
                lambda _status: self.status_changed.emit()
            )
            self.controller.add_frame_listener(self.frame_received.emit)
            self._show_status()
            self.pause_hotkey_pressed.connect(
                self.toggle_pause_resume_and_display
            )
            self._register_pause_hotkey()
        except Exception as e:
            raise WikifiedError("004", "Error in GUI initialization.") from e

    def _register_pause_hotkey(self) -> None:
        # Registered once per app. keyboard calls it on its own thread,
        # so it only emits a signal.
        try:
            keyboard.add_hotkey(PAUSE_HOTKEY, self.pause_hotkey_pressed.emit)
        except Exception as e:  # e.g. keyboard needs root on Linux
            logger.warning(f"Pause shortcut ({PAUSE_HOTKEY}) unavailable: {e}")

    @property
    def is_running(self) -> bool:
        return self.controller.is_running

    def log_handler_function(self, message: "Message") -> None:
        # Loguru sink: called on whichever thread logged the message.
        self.log_received.emit(colorize_log(message))

    def _append_log(self, formatted_message: str) -> None:
        self.log_display.append(formatted_message)
        scrollbar = self.log_display.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def toggle_start_stop(self) -> None:
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def toggle_pause_resume_and_display(self) -> None:
        self.controller.toggle_pause()

    def start_bot(self) -> None:
        # The controller refuses to start until the previous bot has fully
        # shut down, so two bots can never run at the same time.
        if self.is_running:
            return
        self.update_config()
        self.controller.start()

    def stop_bot(self) -> None:
        self.controller.stop()

    def _show_status(self) -> None:
        """Make the controls match the controller. It reads the status
        afresh, since queued signals may arrive after later changes."""
        status = self.controller.status
        if status == self._shown_status:
            return
        self._shown_status = status

        stopped = status == BotStatus.STOPPED
        active = status in (BotStatus.RUNNING, BotStatus.PAUSED)
        self.start_stop_button.setText("▶" if stopped else "■")
        self.start_stop_button.setEnabled(status != BotStatus.STOPPING)
        self.play_pause_button.setText(
            "▶" if status == BotStatus.PAUSED else "⏸️"
        )
        self.play_pause_button.setVisible(active)
        self.server_id_label.setText(f"Status - {STATUS_LABELS[status]}")
        if stopped:
            self.glow_animation.start()
        else:
            self.glow_animation.stop()

    def update_config(self) -> Config:
        self.config.visuals.save_labels = self.save_labels_checkbox.isChecked()
        self.config.visuals.save_images = self.save_images_checkbox.isChecked()
        self.config.visuals.show_images = self.show_images_checkbox.isChecked()
        self.visualize_tab.update_active_state(self.config.visuals.show_images)
        self.config.bot.load_deck = self.load_deck_checkbox.isChecked()
        self.config.bot.auto_start_game = (
            self.auto_start_game_checkbox.isChecked()
        )
        # The dropdown only offers valid levels.
        log_level = cast("LogLevel", self.log_level_dropdown.currentText())
        log_level_changed = self.config.bot.log_level != log_level
        self.config.bot.log_level = log_level
        if log_level_changed:
            setup_logger(self, self.config)
        self.config.ingame.play_action = round(
            float(self.play_action_delay_input.value()), 2
        )
        self.config.adb.device_serial = self.device_serial_input.text()

        screen = self.config.screen_detector
        server_url = self.screen_server_url_input.text().strip()
        if server_url:  # an empty box keeps the current address
            screen.base_url = server_url
        model = self.screen_model_input.text().strip()
        if model:  # an empty box keeps the current model
            screen.model = model
        screen.interval = round(self.screen_interval_input.value(), 2)
        screen.max_age = round(self.screen_max_age_input.value(), 2)
        screen.timeout = round(self.screen_timeout_input.value(), 1)
        return self.config

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.controller.close()
        super().closeEvent(a0)
