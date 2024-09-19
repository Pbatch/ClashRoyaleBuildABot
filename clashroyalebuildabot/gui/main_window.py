from threading import Thread

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from clashroyalebuildabot import Bot
from clashroyalebuildabot.bot.bot import pause_event
from clashroyalebuildabot.gui.animations import start_play_button_animation
from clashroyalebuildabot.gui.layout_setup import setup_tabs
from clashroyalebuildabot.gui.layout_setup import setup_top_bar
from clashroyalebuildabot.gui.styles import set_styles
from clashroyalebuildabot.utils.logger import colorize_log
from clashroyalebuildabot.utils.logger import setup_logger
from error_handling import WikifiedError


class MainWindow(QMainWindow):
    def __init__(self, config, actions):
        try:
            super().__init__()
            self.config = config
            self.actions = actions
            self.bot = None
            self.bot_thread = None
            self.is_running = False

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
        except Exception as e:
            raise WikifiedError("004", "Error in GUI initialization.") from e

    def log_handler_function(self, message):
        formatted_message = colorize_log(message)
        self.log_display.append(formatted_message)
        QApplication.processEvents()
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def toggle_start_stop(self):
        if self.is_running:
            self.stop_bot()
            self.glow_animation.start()
        else:
            self.start_bot()
            self.glow_animation.stop()

    def toggle_pause_resume_and_display(self):
        if not self.bot:
            return
        if pause_event.is_set():
            self.play_pause_button.setText("▶")
        else:
            self.play_pause_button.setText("⏸️")
        self.bot.pause_or_resume()

    def start_bot(self):
        if self.is_running:
            return
        self.update_config()
        self.is_running = True
        self.bot_thread = Thread(target=self.bot_task)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        self.start_stop_button.setText("■")
        self.play_pause_button.show()
        self.server_id_label.setText("Status - Running")
        logger.info("Starting bot")

    def stop_bot(self):
        if self.bot:
            self.bot.stop()
        self.is_running = False
        self.start_stop_button.setText("▶")
        self.play_pause_button.hide()
        self.server_id_label.setText("Status - Stopped")
        logger.info("Bot stopped")

    def restart_bot(self):
        if self.is_running:
            self.stop_bot()
        self.update_config()
        self.start_bot()

    def update_config(self) -> dict:
        self.config["visuals"][
            "save_labels"
        ] = self.save_labels_checkbox.isChecked()
        self.config["visuals"][
            "save_images"
        ] = self.save_images_checkbox.isChecked()
        self.config["visuals"][
            "show_images"
        ] = self.show_images_checkbox.isChecked()
        self.visualize_tab.update_active_state(
            self.config["visuals"]["show_images"]
        )
        self.config["bot"]["load_deck"] = self.load_deck_checkbox.isChecked()
        self.config["bot"][
            "auto_start_game"
        ] = self.auto_start_game_checkbox.isChecked()
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
        self.config["adb"]["ip"] = self.adb_ip_input.text()
        self.config["adb"]["device_serial"] = self.device_serial_input.text()
        return self.config

    def bot_task(self):
        try:
            self.bot = Bot(actions=self.actions, config=self.config)
            self.bot.visualizer.frame_ready.connect(
                self.visualize_tab.update_frame
            )
            self.bot.run()
            self.stop_bot()
        except WikifiedError:
            self.stop_bot()
            raise
        except Exception as e:
            self.stop_bot()
            raise WikifiedError("003", "Bot crashed.") from e

    def append_log(self, message):
        self.log_display.append(message)
