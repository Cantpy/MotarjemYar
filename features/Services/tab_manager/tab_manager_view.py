# features/Services/tab_manager/tab_manager_view.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QPushButton


class ServicesManagementView(QWidget):
    """
    A 'dumb' container widget that holds the tabbed interface for service management.
    """
    refresh_all_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
        self._style_tabs()

    def _setup_ui(self):
        """Initialize the tabbed interface shell."""
        self.setWindowTitle("مدیریت خدمات")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)

        # --- Shared UI Controls ---
        # Example: A toolbar with a global refresh button
        toolbar_layout = QHBoxLayout()
        self.refresh_all_btn = QPushButton("🔄 به‌روزرسانی همه")
        toolbar_layout.addWidget(self.refresh_all_btn)
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

    def _connect_signals(self):
        """Connect this _view's widgets to its public signals."""
        self.refresh_all_btn.clicked.connect(self.refresh_all_requested)

    def add_tab(self, widget: QWidget, name: str):
        """A public method to allow the factory/controller to add fully-built tabs."""
        self.tab_widget.addTab(widget, name)

    def _style_tabs(self):
        """Apply custom styling."""
        # self.tab_widget.setStyleSheet("""...""")
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)