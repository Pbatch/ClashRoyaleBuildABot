def set_styles(window):
    window.setStyleSheet(
        """
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
        QGroupBox {
            color: white;
        }
        QCheckBox {
            color: white;
        }
        QPushButton {
            color: white;
        }
    """
    )
