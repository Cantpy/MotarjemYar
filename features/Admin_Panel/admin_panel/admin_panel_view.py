# features/Admin_Panel/admin_panel/admin_panel_view.py

from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from PySide6.QtCore import Qt
import qtawesome as qta


class AdminPanelView(QWidget):
    """
    The main container view for the Admin Panel. It's a QTabWidget that
    holds the views of the other admin features.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdminPanelContainer")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

    def add_feature_tab(self, view: QWidget, icon_name: str, title: str):
        """
        A helper method to add a new feature's view as a tab.
        """
        icon = qta.icon(icon_name)
        self.tab_widget.addTab(view, icon, title)
