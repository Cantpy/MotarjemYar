from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer

from typing import List


class Toast(QWidget):
    def __init__(self, parent, message: str, duration=3000, on_close=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.on_close = on_close

        self.label = QLabel(message)
        self.label.setStyleSheet("""
            background-color: #333;
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.mousePressEvent = self.dismiss_on_click

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.adjustSize()

        self.setWindowOpacity(0.0)
        self.show()

        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()

        QTimer.singleShot(duration, self.close_with_fade)

    def dismiss_on_click(self, event):
        self.close_with_fade()

    def close_with_fade(self):
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self._final_close)
        self.fade_out.start()

    def _final_close(self):
        self.close()
        if self.on_close:
            self.on_close(self)


class ToastManager:
    def __init__(self, parent):
        self.parent = parent
        self.active_toasts: List[Toast] = []

    def show(self, message: str, duration: int = 3000):
        toast = Toast(self.parent, message, duration, on_close=self._remove_toast)
        self.active_toasts.append(toast)
        self._reposition_toasts()

    def _remove_toast(self, toast):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            self._reposition_toasts()

    def _reposition_toasts(self):
        margin = 10
        spacing = 10
        bottom_offset = 40

        for index, toast in enumerate(reversed(self.active_toasts)):
            toast.adjustSize()
            parent_rect = self.parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - toast.width()) // 2
            y = (parent_rect.y() + parent_rect.height() - toast.height() -
                 bottom_offset - index * (toast.height() + spacing))
            toast.move(x, y)


_toast_manager = None


def show_toast(parent, message: str, duration=3000):
    global _toast_manager
    if _toast_manager is None or _toast_manager.parent != parent:
        _toast_manager = ToastManager(parent)
    _toast_manager.show(message, duration)
