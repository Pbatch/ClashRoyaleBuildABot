from threading import Thread

import keyboard
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

from clashroyalebuildabot import Bot
from clashroyalebuildabot.gui.animations import start_play_button_animation
from clashroyalebuildabot.gui.gameplay_widget import ImageStreamWindow
from clashroyalebuildabot.gui.layout_setup import setup_tabs, setup_top_bar
from clashroyalebuildabot.gui.styles import set_styles
from clashroyalebuildabot.utils.error_handling import WikifiedError
from clashroyalebuildabot.utils.logger import colorize_log, setup_logger

PAUSE_HOTKEY = "ctrl+p"


class MainWindow(QMainWindow):
    # Other threads never touch widgets directly. They emit these signals,
    # and Qt runs the connected slots on the GUI thread.
    # (The ignores work around PyQt6 6.12's stubs, which wrongly mark the
    # optional `arguments` parameter of pyqtSignal as required.)
    log_received = pyqtSignal(str)  # ty: ignore[missing-argument]
    bot_finished = pyqtSignal()  # ty: ignore[missing-argument]
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
    screen_min_confidence_input: QDoubleSpinBox
    screen_interval_input: QDoubleSpinBox
    screen_max_age_input: QDoubleSpinBox
    screen_timeout_input: QDoubleSpinBox
    glow_effect: QGraphicsDropShadowEffect
    glow_animation: QPropertyAnimation

    def __init__(self, config, actions):
        try:
            super().__init__()
            self.config = config
            self.actions = actions
            self.bot: Bot | None = None
            self.bot_thread: Thread | None = None
            self._stop_requested = False

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
            self.bot_finished.connect(self._on_bot_finished)
            self.pause_hotkey_pressed.connect(
                self.toggle_pause_resume_and_display
            )
            self._register_pause_hotkey()
        except Exception as e:
            raise WikifiedError("004", "Error in GUI initialization.") from e

    def _register_pause_hotkey(self):
        # Registered once per app. keyboard calls it on its own thread,
        # so it only emits a signal.
        try:
            keyboard.add_hotkey(PAUSE_HOTKEY, self.pause_hotkey_pressed.emit)
        except Exception as e:  # e.g. keyboard needs root on Linux
            logger.warning(f"Pause shortcut ({PAUSE_HOTKEY}) unavailable: {e}")

    @property
    def is_running(self) -> bool:
        return self.bot_thread is not None

    def log_handler_function(self, message):
        # Loguru sink: called on whichever thread logged the message.
        self.log_received.emit(colorize_log(message))

    def _append_log(self, formatted_message):
        self.log_display.append(formatted_message)
        scrollbar = self.log_display.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def toggle_start_stop(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def toggle_pause_resume_and_display(self):
        if self.bot is None or self._stop_requested:
            return
        self.bot.toggle_pause()
        self.play_pause_button.setText("▶" if self.bot.is_paused else "⏸️")

    def start_bot(self):
        # bot_thread is only cleared once the previous bot has fully shut
        # down, so two bots can never run at the same time.
        if self.is_running:
            return
        self.update_config()
        self._stop_requested = False
        self.bot_thread = Thread(target=self.bot_task, daemon=True)
        self.bot_thread.start()

        self.glow_animation.stop()
        self.start_stop_button.setText("■")
        self.play_pause_button.setText("⏸️")
        self.play_pause_button.show()
        self.server_id_label.setText("Status - Running")
        logger.info("Starting bot")

    def stop_bot(self):
        if not self.is_running or self._stop_requested:
            return
        self._stop_requested = True
        if self.bot is not None:
            self.bot.stop()
        # If the bot is still being created, bot_task sees _stop_requested.

        self.start_stop_button.setEnabled(False)
        self.play_pause_button.hide()
        self.server_id_label.setText("Status - Stopping...")
        logger.info("Stopping bot")

    def _on_bot_finished(self):
        if self.bot_thread is not None:
            self.bot_thread.join()
        self.bot_thread = None
        self.bot = None
        self._stop_requested = False

        self.start_stop_button.setEnabled(True)
        self.start_stop_button.setText("▶")
        self.play_pause_button.hide()
        self.server_id_label.setText("Status - Stopped")
        self.glow_animation.start()
        logger.info("Bot stopped")

    def update_config(self) -> dict:
        self.config["visuals"]["save_labels"] = (
            self.save_labels_checkbox.isChecked()
        )
        self.config["visuals"]["save_images"] = (
            self.save_images_checkbox.isChecked()
        )
        self.config["visuals"]["show_images"] = (
            self.show_images_checkbox.isChecked()
        )
        self.visualize_tab.update_active_state(
            self.config["visuals"]["show_images"]
        )
        self.config["bot"]["load_deck"] = self.load_deck_checkbox.isChecked()
        self.config["bot"]["auto_start_game"] = (
            self.auto_start_game_checkbox.isChecked()
        )
        log_level_changed = (
            self.config["bot"]["log_level"]
            != self.log_level_dropdown.currentText()
        )
        self.config["bot"]["log_level"] = self.log_level_dropdown.currentText()
        if log_level_changed:
            setup_logger(self, self.config)
        self.config["ingame"]["play_action"] = round(
            float(self.play_action_delay_input.value()), 2
        )
        self.config["adb"]["device_serial"] = self.device_serial_input.text()

        screen = self.config["screen_detector"]
        server_url = self.screen_server_url_input.text().strip()
        if server_url:  # an empty box keeps the current address
            screen["base_url"] = server_url
        screen["min_confidence"] = round(
            self.screen_min_confidence_input.value(), 2
        )
        screen["interval"] = round(self.screen_interval_input.value(), 2)
        screen["max_age"] = round(self.screen_max_age_input.value(), 2)
        screen["timeout"] = round(self.screen_timeout_input.value(), 1)
        return self.config

    def bot_task(self):
        """Runs on bot_thread. Talks to the GUI only through signals."""
        try:
            bot = Bot(actions=self.actions, config=self.config)
            bot.visualizer.frame_ready.connect(self.visualize_tab.update_frame)
            self.bot = bot
            if self._stop_requested:
                bot.stop()
            bot.run()
        except Exception as e:
            # Raising here would only reach the console, so log instead:
            # that reaches the console, the log file and the Logs tab.
            if not isinstance(e, WikifiedError):
                crash = WikifiedError("003", "Bot crashed.")
                crash.__cause__ = e
                e = crash
            logger.opt(exception=e).error(str(e).strip())
        finally:
            self.bot_finished.emit()

    def closeEvent(self, a0: QCloseEvent | None):
        # Shut the bot down cleanly so the screen recording doesn't outlive
        # the app.
        if self.is_running:
            self._stop_requested = True
            if self.bot is not None:
                self.bot.stop()
            if self.bot_thread is not None:
                self.bot_thread.join(timeout=10)
        super().closeEvent(a0)
