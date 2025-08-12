import sys
import sqlite3
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Import our modules
from features.InvoicePage.document_selection.document_selection_repo import DatabaseRepository
from features.InvoicePage.document_selection.document_selection_logic import DocumentLogic, PriceCalculationLogic
from features.InvoicePage.document_selection.document_selection_controller import DocumentSelectionController

from features.InvoicePage.document_selection.document_selection_assets import SERVICES_DB_URL


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.controller = None
        self.setup_ui()
        self.setup_logic()

    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("سیستم مدیریت اسناد و قیمت‌گذاری")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('فایل')

        # New invoice action
        new_action = QAction('فاکتور جدید', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_invoice)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('خروج', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('نمایش')

        # Show summary action
        summary_action = QAction('خلاصه فاکتور', self)
        summary_action.setShortcut('Ctrl+S')
        summary_action.triggered.connect(self.show_summary)
        view_menu.addAction(summary_action)

        # Refresh action
        refresh_action = QAction('بروزرسانی', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)

    def setup_logic(self):
        """Setup business logic and controllers"""
        try:

            # Initialize repository
            repository = DatabaseRepository(f"sqlite:///{SERVICES_DB_URL}")

            # Initialize logic components
            document_logic = DocumentLogic(repository)
            price_logic = PriceCalculationLogic(document_logic)

            # Initialize controller
            self.controller = DocumentSelectionController(document_logic, price_logic, self)

            # Create and set main view
            main_view = self.controller.create_view(self)
            layout = QVBoxLayout(self.centralWidget())
            layout.addWidget(main_view)

            print("Application initialized successfully!")

        except Exception as e:
            print(f"Error initializing application: {e}")
            sys.exit(1)

    def new_invoice(self):
        """Create new invoice (clear current)"""
        if self.controller:
            self.controller._on_clear_requested()

    def show_summary(self):
        """Show invoice summary"""
        if self.controller:
            self.controller.show_invoice_summary()

    def refresh_data(self):
        """Refresh application data"""
        if self.controller:
            self.controller.refresh_autocomplete()
            print("Data refreshed!")

    def closeEvent(self, event):
        """Handle application close event"""
        if self.controller:
            self.controller.cleanup()
        event.accept()


def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("سیستم مدیریت اسناد")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Document Management System")

    # Set right-to-left layout for Persian UI
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Print startup message
    print("=== سیستم مدیریت اسناد و قیمت‌گذاری ===")
    print("Application started successfully!")
    print(f"Database: {SERVICES_DB_URL}")
    print("UI Language: Persian (RTL)")
    print("=========================================")

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
