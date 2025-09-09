from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Qt
from shared.fonts.font_manager import FontManager


class AdminMainWindowView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("پنل مدیریت مترجم‌یار")
        self.setFont(FontManager.get_font(size=12))
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()
        self.tab_widget.setLayoutDirection(Qt.RightToLeft)
        self.tab_widget.setFont(FontManager.get_font(size=12))
        layout.addWidget(self.tab_widget)
