"""services_management_view.py - Main tabbed interface for services management using PySide6"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from services_documents_view import ServicesDocumentsView
from services_fixed_prices_view import ServicesFixedPricesView
from services_other_view import ServicesOtherView
from services_management_controller import ServicesController, FixedPricesController, OtherServicesController


class ServicesManagementView(QWidget):
    """Main widget containing tabbed interface for different service management sections."""

    def __init__(self, db_path: str, excel_path: str = None, parent=None):
        super().__init__()
        self.parent_window = parent
        self.db_path = db_path
        self.excel_path = excel_path

        # Initialize controllers
        self.services_controller = ServicesController(db_path, excel_path)
        self.fixed_prices_controller = FixedPricesController(db_path)
        self.other_services_controller = OtherServicesController(db_path)

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

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

        # Style the tabs
        self._style_tabs()

    def _create_documents_tab(self):
        """Create the documents management tab."""
        self.documents_view = ServicesDocumentsView(
            controller=self.services_controller,
            parent=self
        )
        self.tab_widget.addTab(self.documents_view, "مدارک")

    def _create_fixed_costs_tab(self):
        """Create the fixed costs tab."""
        self.fixed_prices_view = ServicesFixedPricesView(
            controller=self.fixed_prices_controller,
            parent=self
        )
        self.tab_widget.addTab(self.fixed_prices_view, "هزینه‌های ثابت")

    def _create_other_services_tab(self):
        """Create the other services tab."""
        self.other_services_view = ServicesOtherView(
            controller=self.other_services_controller,
            parent=self
        )
        self.tab_widget.addTab(self.other_services_view, "خدمات دیگر")

    def _connect_signals(self):
        """Connect controller signals to UI handlers."""
        # Connect error/success signals from all controllers
        for controller in [self.services_controller, self.fixed_prices_controller, self.other_services_controller]:
            controller.error_occurred.connect(self._show_error_message)
            controller.success_occurred.connect(self._show_success_message)
            controller.warning_occurred.connect(self._show_warning_message)

    def _show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        # This should be connected to your message box utility
        try:
            from modules.helper_functions import show_error_message_box
            show_error_message_box(self, title, message)
        except ImportError:
            print(f"Error - {title}: {message}")

    def _show_success_message(self, title: str, message: str):
        """Show success message dialog."""
        try:
            from modules.helper_functions import show_information_message_box
            show_information_message_box(self, title, message)
        except ImportError:
            print(f"Success - {title}: {message}")

    def _show_warning_message(self, title: str, message: str):
        """Show warning message dialog."""
        try:
            from modules.helper_functions import show_warning_message_box
            show_warning_message_box(self, title, message)
        except ImportError:
            print(f"Warning - {title}: {message}")

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

    def load_all_data(self):
        """Load data for all tabs."""
        self.services_controller.load_services()
        self.fixed_prices_controller.load_fixed_prices()
        self.other_services_controller.load_other_services()

    def refresh_current_tab(self):
        """Refresh data for the currently active tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:  # Documents tab
            self.services_controller.load_services()
        elif current_index == 1:  # Fixed prices tab
            self.fixed_prices_controller.load_fixed_prices()
        elif current_index == 2:  # Other services tab
            self.other_services_controller.load_other_services()

    def get_current_tab_name(self) -> str:
        """Get the name of the currently active tab."""
        current_index = self.tab_widget.currentIndex()
        return self.tab_widget.tabText(current_index)

    def switch_to_tab(self, tab_name: str):
        """Switch to a specific tab by name."""
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                self.tab_widget.setCurrentIndex(i)
                break
