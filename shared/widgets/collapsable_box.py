# shared/widgets/collapsible_box.py

from PySide6.QtWidgets import QWidget, QToolButton, QVBoxLayout, QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont


class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)

        self.toggle_button = QToolButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")  # Button is now just a trigger
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonIconOnly)  # No text on the button itself
        self.toggle_button.setArrowType(Qt.RightArrow)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("IranSANS", 10, QFont.Bold))
        self.title_label.setStyleSheet("color: #3182ce;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(5)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()  # This pushes the arrow to the far side
        header_layout.addWidget(self.toggle_button)

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setLayout(QVBoxLayout())  # It needs a layout from the start

        # Add a separator line for better visual distinction
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(header_layout)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.content_area)

        # --- The animation _logic is correct from the previous answer ---
        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.toggle_button.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

        start_height = self.content_area.height()
        end_height = self.content_area.layout().sizeHint().height() if checked else 0

        self.animation.setStartValue(start_height)
        self.animation.setEndValue(end_height)
        self.animation.start()

    def setContentLayout(self, layout):
        # This is correct
        old_layout = self.content_area.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)
        self.content_area.setLayout(layout)
