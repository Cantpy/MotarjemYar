from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QMouseEvent


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # This will handle all constructor patterns
        self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)
