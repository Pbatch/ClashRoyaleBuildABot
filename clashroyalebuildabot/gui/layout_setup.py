from PyQt6.QtCore import Qt  # Fügen Sie den fehlenden Import für Qt hinzu
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.QtWidgets import QFormLayout
from PyQt6.QtWidgets import QFrame
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QGroupBox
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from clashroyalebuildabot.gui.gameplay_widget import ImageStreamWindow


def setup_top_bar(main_window):
    top_bar = QFrame()
    top_bar.setStyleSheet("background-color: #1E272E;")
    top_bar_layout = QHBoxLayout(top_bar)

    left_layout = QVBoxLayout()
    left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    server_name = QLabel("Clash Royale Build-A-Bot")
    server_name.setStyleSheet(
        "font-weight: bold; font-size: 16pt; color: white;"
    )
    left_layout.addWidget(server_name)

    server_details = QLabel(
        '<a href="https://github.com/Pbatch/ClashRoyaleBuildABot">https://github.com/Pbatch/ClashRoyaleBuildABot</a>'
    )
    server_details.setOpenExternalLinks(True)
    server_details.setStyleSheet("color: #57A6FF;")
    left_layout.addWidget(server_details)

    main_window.server_id_label = QLabel("Status")
    main_window.server_id_label.setStyleSheet("color: #999;")
    left_layout.addWidget(main_window.server_id_label)

    port_link = QLabel(
        '<a href="http://localhost:5555" style="color: #57A6FF;">127.0.0.1:5555</a>'
    )
    port_link.setOpenExternalLinks(True)
    left_layout.addWidget(port_link)

    top_bar_layout.addLayout(left_layout)

    right_layout = QVBoxLayout()
    right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

    button_layout = QHBoxLayout()
    button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)


    main_window.play_pause_button = QPushButton("⏸️")
    main_window.play_pause_button.setFont(QFont("Arial", 18))
    main_window.play_pause_button.setStyleSheet(
        """
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
    """
    )
    main_window.play_pause_button.clicked.connect(
        main_window.toggle_pause_resume_and_display
    )

    button_layout.addWidget(main_window.play_pause_button)
    main_window.play_pause_button.hide()

    main_window.start_stop_button = QPushButton("▶")
    main_window.start_stop_button.setFont(QFont("Arial", 18))
    main_window.start_stop_button.setStyleSheet(
        """
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
    """
    )
    main_window.start_stop_button.clicked.connect(
        main_window.toggle_start_stop
    )

    button_layout.addWidget(main_window.start_stop_button)

    top_bar_layout.addStretch()
    top_bar_layout.addLayout(right_layout)
    top_bar_layout.addLayout(button_layout)

    return top_bar


def setup_tabs(main_window):
    tab_widget = QTabWidget()
    tab_widget.setStyleSheet(
        """
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
    """
    )

    logs_tab = QWidget()
    logs_layout = QVBoxLayout(logs_tab)
    main_window.log_display = QTextEdit()
    main_window.log_display.setReadOnly(True)
    main_window.log_display.setStyleSheet(
        "background-color: #1e1e1e; color: lightgrey; font-family: monospace;"
    )
    logs_layout.addWidget(main_window.log_display)
    tab_widget.addTab(logs_tab, "Logs")

    main_window.visualize_tab = ImageStreamWindow()
    tab_widget.addTab(main_window.visualize_tab, "Visualize")


    settings_tab = QWidget()
    settings_layout = QGridLayout(settings_tab)

    bot_group = QGroupBox("Bot ")
    bot_layout = QFormLayout()
    main_window.log_level_dropdown = QComboBox()
    main_window.log_level_dropdown.addItems(
        ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
    )
    main_window.log_level_dropdown.setCurrentText(main_window.config["bot"]["log_level"])
    bot_layout.addRow("Log Level:", main_window.log_level_dropdown)

    main_window.adb_ip_input = QLineEdit()
    main_window.adb_ip_input.setText(main_window.config["adb"]["ip"])
    main_window.device_serial_input = QLineEdit()
    main_window.device_serial_input.setText(main_window.config["adb"]["device_serial"])
    bot_layout.addRow("ADB IP Address:", main_window.adb_ip_input)
    bot_layout.addRow("Device Serial:", main_window.device_serial_input)

    bot_group.setLayout(bot_layout)

    visuals_group = QGroupBox("Visuals Settings")
    visuals_layout = QFormLayout()
    main_window.save_labels_checkbox = QCheckBox("Save labels")
    main_window.save_labels_checkbox.setChecked(main_window.config["visuals"]["save_labels"])
    main_window.save_images_checkbox = QCheckBox("Save images")
    main_window.save_images_checkbox.setChecked(main_window.config["visuals"]["save_images"])
    main_window.show_images_checkbox = QCheckBox("Show images")
    main_window.show_images_checkbox.setChecked(main_window.config["visuals"]["show_images"])
    visuals_layout.addRow(main_window.save_labels_checkbox)
    visuals_layout.addRow(main_window.save_images_checkbox)
    visuals_layout.addRow(main_window.show_images_checkbox)
    visuals_group.setLayout(visuals_layout)

    ingame_group = QGroupBox("Ingame Settings")
    ingame_layout = QFormLayout()

    main_window.play_action_delay_input = QDoubleSpinBox()
    main_window.play_action_delay_input.setRange(0.1, 5.0)
    main_window.play_action_delay_input.setSingleStep(0.1)
    main_window.play_action_delay_input.setValue(main_window.config["ingame"]["play_action"])
    ingame_layout.addRow(
        "Action Delay (sec):", main_window.play_action_delay_input
    )

    main_window.load_deck_checkbox = QCheckBox(
        "Create deck code on game start"
    )
    main_window.load_deck_checkbox.setChecked(main_window.config["bot"]["load_deck"])
    ingame_layout.addRow(main_window.load_deck_checkbox)

    main_window.auto_start_game_checkbox = QCheckBox("Auto start game")
    main_window.auto_start_game_checkbox.setChecked(main_window.config["bot"]["auto_start_game"])
    ingame_layout.addRow(main_window.auto_start_game_checkbox)

    ingame_group.setLayout(ingame_layout)

    settings_layout.addWidget(bot_group, 0, 0)
    settings_layout.addWidget(visuals_group, 1, 0)
    settings_layout.addWidget(ingame_group, 0, 1, 2, 1)

    tab_widget.addTab(settings_tab, "Settings")

    return tab_widget
