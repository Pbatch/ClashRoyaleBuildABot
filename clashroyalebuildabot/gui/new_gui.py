import logging

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QFrame,
    QTabWidget,
    QCheckBox,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QDoubleSpinBox,
    QGroupBox,
    QGridLayout,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG
from threading import Thread


from clashroyalebuildabot import Bot
from clashroyalebuildabot.actions.generic.action import Action
import sys

class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        log_entry = self.format(record)
        QMetaObject.invokeMethod(
            self.text_edit,
            "append",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, log_entry)
        )

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

        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #1E272E;")
        top_bar_layout = QHBoxLayout(top_bar)

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        server_name = QLabel("Clash Royale Build-A-Bot")
        server_name.setStyleSheet("font-weight: bold; font-size: 16pt; color: white;")
        left_layout.addWidget(server_name)

        server_details = QLabel('<a href="https://github.com/Pbatch/ClashRoyaleBuildABot">https://github.com/Pbatch/ClashRoyaleBuildABot</a>')
        server_details.setOpenExternalLinks(True)
        server_details.setStyleSheet("color: #57A6FF;")
        left_layout.addWidget(server_details)

        self.server_id_label = QLabel("Status")
        self.server_id_label.setStyleSheet("color: #999;")
        left_layout.addWidget(self.server_id_label)

        port_link = QLabel('<a href="http://localhost:5555" style="color: #57A6FF;">127.0.0.1:5555</a>')
        port_link.setOpenExternalLinks(True)
        left_layout.addWidget(port_link)

        top_bar_layout.addLayout(left_layout)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.start_stop_button = QPushButton("▶")
        self.start_stop_button.setFont(QFont("Arial", 18))
        self.start_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #4B6EAF;
                color: white;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5C7EBF;
            }
        """)
        self.start_stop_button.clicked.connect(self.toggle_start_stop)

        restart_button = QPushButton("↻")
        restart_button.setFont(QFont("Arial", 18))
        restart_button.setStyleSheet("""
            QPushButton {
                background-color: #4B6EAF;
                color: white;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5C7EBF;
            }
        """)
        restart_button.clicked.connect(self.restart_bot)

        delete_button = QPushButton("🗑")
        delete_button.setFont(QFont("Arial", 18))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e04f5f;
                color: white;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F06F6F;
            }
        """)

        button_layout.addWidget(self.start_stop_button)
        button_layout.addWidget(restart_button)
        button_layout.addWidget(delete_button)

        top_bar_layout.addStretch()
        top_bar_layout.addLayout(right_layout)
        top_bar_layout.addLayout(button_layout)

        main_layout.addWidget(top_bar)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
        QTabWidget::pane { border: 0; }
        QTabBar::tab {
            background: #333;
            color: white;
            padding: 8px;
            margin-bottom: -1px;
        }
        QTabBar::tab:selected {
            background: #1E272E;
            border-bottom: 2px solid #57A6FF;
        }
        """)

        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setText("Lorem Ipsum - Press Start for Text")
        self.log_display.setStyleSheet("background-color: #1e1e1e; color: lightgrey; font-family: monospace;")
        logs_layout.addWidget(self.log_display)
        tab_widget.addTab(logs_tab, "Logs")

        settings_tab = QWidget()
        settings_layout = QGridLayout(settings_tab)

        bot_group = QGroupBox("Bot ")
        bot_layout = QFormLayout()
        self.log_level_dropdown = QComboBox()
        self.log_level_dropdown.addItems(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        bot_layout.addRow("Log Level:", self.log_level_dropdown)

        self.adb_ip_input = QLineEdit()
        self.adb_ip_input.setPlaceholderText("127.0.0.1")
        self.device_serial_input = QLineEdit()
        self.device_serial_input.setPlaceholderText("emulator-5554")
        bot_layout.addRow("ADB IP Address:", self.adb_ip_input)
        bot_layout.addRow("Device Serial:", self.device_serial_input)

        bot_group.setLayout(bot_layout)

        visuals_group = QGroupBox("Visuals Settings")
        visuals_layout = QFormLayout()
        self.save_labels_checkbox = QCheckBox("Save labels")
        self.save_images_checkbox = QCheckBox("Save images")
        self.show_images_checkbox = QCheckBox("Show images")
        visuals_layout.addRow(self.save_labels_checkbox)
        visuals_layout.addRow(self.save_images_checkbox)
        visuals_layout.addRow(self.show_images_checkbox)
        visuals_group.setLayout(visuals_layout)

        ingame_group = QGroupBox("Ingame Settings")
        ingame_layout = QFormLayout()

        self.play_action_delay_input = QDoubleSpinBox()
        self.play_action_delay_input.setRange(0.1, 5.0)
        self.play_action_delay_input.setSingleStep(0.1)
        self.play_action_delay_input.setValue(0.5)
        ingame_layout.addRow("Action Delay (sec):", self.play_action_delay_input)

        self.load_deck_checkbox = QCheckBox("Create deck code on game start")
        ingame_layout.addRow(self.load_deck_checkbox)

        self.auto_start_game_checkbox = QCheckBox("Auto start game")
        ingame_layout.addRow(self.auto_start_game_checkbox)

        ingame_group.setLayout(ingame_layout)



        settings_layout.addWidget(bot_group, 0, 0)
        settings_layout.addWidget(visuals_group, 1, 0)
        settings_layout.addWidget(ingame_group, 0, 1, 2, 1)

        tab_widget.addTab(settings_tab, "Settings")

        stats_tab = QWidget()
        tab_widget.addTab(stats_tab, "Stats")

        main_layout.addWidget(tab_widget)

        self.setStyleSheet("""
        QMainWindow {
            background-color: #0D1117;
        }
        QLabel {
            color: white;
            padding: 2px;
        }
        QPushButton {
            border: none;
            padding: 8px;
        }
        QFrame {
            background-color: #1E272E;
        }
        """)



    def toggle_start_stop(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        if self.is_running:
            return
        self.update_config()
        self.is_running = True
        self.bot_thread = Thread(target=self.bot_task)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        self.start_stop_button.setText("■")
        self.start_stop_button.setFont(QFont("Arial", 18))
        self.start_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e04f5f;
                color: white;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F06F6F;
            }
        """)
        self.server_id_label.setText("Status - Running")
        self.append_log("Bot started")

    def stop_bot(self):
        if not self.bot:
            return
        self.bot.stop()
        self.is_running = False
        self.start_stop_button.setText("▶")
        self.start_stop_button.setFont(QFont("Arial", 18))
        self.start_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #4B6EAF;
                color: white;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5C7EBF;
            }
        """)
        self.server_id_label.setText("Status - Stopped")
        self.append_log("Bot stopped")

    def restart_bot(self):
        if self.is_running:
            self.stop_bot()
        self.update_config()
        self.start_bot()

    def update_config(self):
        self.config["visuals"]["save_labels"] = self.save_labels_checkbox.isChecked()
        self.config["visuals"]["save_images"] = self.save_images_checkbox.isChecked()
        self.config["visuals"]["show_images"] = self.show_images_checkbox.isChecked()
        self.config["bot"]["load_deck"] = self.load_deck_checkbox.isChecked()
        self.config["bot"]["auto_start_game"] = self.auto_start_game_checkbox.isChecked()
        self.config["bot"]["log_level"] = self.log_level_dropdown.currentText()
        self.config["ingame"]["play_action"] = float(self.play_action_delay_input.value())
        self.config["adb"]["ip"] = self.adb_ip_input.text()
        self.config["adb"]["device_serial"] = self.device_serial_input.text()

    def bot_task(self):
        self.bot = Bot(actions=self.actions, config=self.config)
        self.bot.run()

    def append_log(self, message):
        self.log_display.append(message)
