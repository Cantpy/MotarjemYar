"""documents_widget.py"""

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget)
from ui.fixed_costs_ui import FixedCostsWidget
from other_services_widget import OtherServicesWidget
from service_management_widget import ServicesManagerWidget


class TabbedServicesManager(QWidget):
    """Main widget containing tabbed interface for different service management sections."""

    def __init__(self, parent=None):
        super().__init__()
        self.parent_invoice_page = parent  # MainWinodw

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("مدیریت خدمات")
        self.setGeometry(100, 100, 1000, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _setup_ui(self):
        """Initialize the tabbed interface."""
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setTabShape(QTabWidget.TabShape.Rounded)

        # Create tabs
        self._create_documents_tab()
        self._create_fixed_costs_tab()
        self._create_other_services_tab()

        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)

        # Style the tabs to be equally spaced
        self._style_tabs()

    def _create_documents_tab(self):
        """Create the documents management tab with ServicesManagerWidget."""
        # Create the ServicesManagerWidget instance
        self.services_widget = ServicesManagerWidget(self.parent_invoice_page)

        # Add as first tab
        self.tab_widget.addTab(self.services_widget, "مدارک")

    def _create_fixed_costs_tab(self):
        """Create the fixed costs tab with FixedCostsWidget."""
        # Create the FixedCostsWidget instance
        self.fixed_costs_widget = FixedCostsWidget()

        # Add as second tab
        self.tab_widget.addTab(self.fixed_costs_widget, "هزینه‌های ثابت")

    def _create_other_services_tab(self):
        """Create the fixed costs tab with FixedCostsWidget."""
        # Create the FixedCostsWidget instance
        self.other_services_widget = OtherServicesWidget()

        # Add as second tab
        self.tab_widget.addTab(self.other_services_widget, "خدمات دیگر")

    def _style_tabs(self):
        """Apply custom styling to make tabs equally spaced."""
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: white;
            }

            QTabWidget::tab-bar {
                alignment: center;
            }

            QTabBar::tab {
                background-color: #F0F0F0;
                border: 1px solid #C0C0C0;
                padding: 10px 20px;
                margin-right: 2px;
                min-width: 150px;
                text-align: center;
            }

            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #E0E0E0;
            }

            QTabBar::tab:first {
                margin-left: 0px;
            }

            QTabBar::tab:last {
                margin-right: 0px;
            }
        """)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = TabbedServicesManager(parent=None)
    widget.show()
    sys.exit(app.exec())
