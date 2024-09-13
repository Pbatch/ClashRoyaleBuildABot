from PyQt6.QtCore import QEasingCurve
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


def start_play_button_animation(self):
    self.glow_effect = QGraphicsDropShadowEffect(self)
    self.glow_effect.setBlurRadius(
        10
    )  # Initial blur radius for the glow effect
    self.glow_effect.setColor(Qt.GlobalColor.cyan)
    self.glow_effect.setOffset(
        0, 0
    )  # Center the shadow to create the glow effect
    self.start_stop_button.setGraphicsEffect(self.glow_effect)

    _start_glow_animation(self)


def _start_glow_animation(self):
    """Create a glow effect animation."""
    self.glow_animation = QPropertyAnimation(self.glow_effect, b"blurRadius")
    self.glow_animation.setStartValue(0)
    self.glow_animation.setEndValue(25)
    self.glow_animation.setDuration(2000)
    self.glow_animation.setEasingCurve(QEasingCurve.Type.SineCurve)
    self.glow_animation.setLoopCount(-1)
    self.glow_animation.start()
