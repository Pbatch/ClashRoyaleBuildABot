from PyQt6.QtGui import QImage
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget


class ImageStreamWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.image = QLabel(self)
        self.inactiveIndicator = QLabel(self)
        self.inactiveIndicator.setText(
            "The visualizer is disabled. Enable it in the Settings tab."
        )
        self.inactiveIndicator.setStyleSheet(
            " ".join(
                [
                    "background-color: #FFA500;",
                    "color: white;",
                    "padding: 5px;",
                    "height: fit-content;",
                    "width: fit-content;",
                ]
            )
        )
        self.inactiveIndicator.setMaximumHeight(30)
        layout = QVBoxLayout()
        layout.addWidget(self.inactiveIndicator)
        layout.addWidget(self.image)
        self.setLayout(layout)

    def update_frame(self, annotated_image):
        height, width, _ = annotated_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(
            annotated_image.data.tobytes(),
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(q_image)
        self.image.setPixmap(pixmap)

    def update_active_state(self, active):
        if not active:
            self.inactiveIndicator.show()
        else:
            self.inactiveIndicator.hide()
        self.image.clear()
