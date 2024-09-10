from PyQt6.QtGui import QImage
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget


class ImageStreamWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel(self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_frame(self, annotated_image):
        height, width, channel = annotated_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(
            annotated_image.data.tobytes(),
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )

        pixmap = QPixmap.fromImage(q_image)
        self.label.setPixmap(pixmap)
