import logging

from PyQt6.QtCore import Q_ARG
from PyQt6.QtCore import QMetaObject
from PyQt6.QtCore import Qt


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
            Q_ARG(str, log_entry),
        )
