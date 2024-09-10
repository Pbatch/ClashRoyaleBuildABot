from threading import Thread

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from clashroyalebuildabot import Bot
from clashroyalebuildabot.bot.bot import pause_event
from clashroyalebuildabot.gui.layout_setup import setup_tabs
from clashroyalebuildabot.gui.layout_setup import setup_top_bar
from clashroyalebuildabot.gui.styles import set_styles


class MainWindow(QMainWindow):
    def __init__(self, config, actions):
        super().__init__()


        self.config = config
        self.actions = actions
        self.bot = None
        self.bot_thread = None
        self.is_running = False

        self.setWindowTitle("Clash Royale Build-A-Bot")
        self.setGeometry(100, 100, 900, 600)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Setup GUI components
        top_bar = setup_top_bar(self)
        tab_widget = setup_tabs(self)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(tab_widget)

        set_styles(self)

    def toggle_start_stop(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

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
        self.append_log("Bot started")

    def stop_bot(self):
        if not self.bot:
            return
        self.bot.stop()
        self.is_running = False
        self.start_stop_button.setText("▶")
        self.play_pause_button.hide()
        self.server_id_label.setText("Status - Stopped")
        self.append_log("Bot stopped")

    def restart_bot(self):
        if self.is_running:
            self.stop_bot()
        self.update_config()
        self.start_bot()

    def update_config(self):
        self.config["visuals"][
            "save_labels"
        ] = self.save_labels_checkbox.isChecked()
        self.config["visuals"][
            "save_images"
        ] = self.save_images_checkbox.isChecked()
        self.config["visuals"][
            "show_images"
        ] = self.show_images_checkbox.isChecked()
        self.config["bot"]["load_deck"] = self.load_deck_checkbox.isChecked()
        self.config["bot"][
            "auto_start_game"
        ] = self.auto_start_game_checkbox.isChecked()
        self.config["bot"]["log_level"] = self.log_level_dropdown.currentText()
        self.config["ingame"]["play_action"] = float(
            self.play_action_delay_input.value()
        )
        self.config["adb"]["ip"] = self.adb_ip_input.text()
        self.config["adb"]["device_serial"] = self.device_serial_input.text()

    def bot_task(self):
        self.bot = Bot(actions=self.actions, config=self.config)
        self.bot.visualizer.frame_ready.connect(self.visualize_tab.update_frame)
        self.bot.run()

    def append_log(self, message):
        self.log_display.append(message)
