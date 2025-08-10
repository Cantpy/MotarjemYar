"""
Main entry point for the Invoice Details application.
Demonstrates the MVC pattern implementation.
"""
import sys
import logging
from datetime import datetime

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your existing view
from invoice_details_view import InvoiceDetailsView

# Import the MVC components
from features.InvoicePage.invoice_details.invoice_details_models import CustomerInfo, TranslationOfficeInfo
from features.InvoicePage.invoice_page.invoice_page_controller import InvoiceDetailsController
from shared import return_resource

invoices_database = return_resource('databases', 'invoices.db')
users_database = return_resource('databases', 'users.db')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for the application."""

    def __init__(self,
                 invoices_database_url: str = f"sqlite:///{invoices_database}",
                 users_database_url: str = f"sqlite:///{users_database}"):
        """Initialize database connection."""
        self.invoices_engine = create_engine(invoices_database_url, echo=False)
        self.invoices_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.invoices_engine)

        self.users_engine = create_engine(users_database_url, echo=False)
        self.users_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.users_engine)

    def get_session(self):
        """Get database session."""
        return self.invoices_SessionLocal(), self.users_SessionLocal()

    def close(self):
        """Close database connection."""
        self.invoices_engine.dispose()
        self.users_engine.dispose()


class InvoiceDetailsMainWindow(QMainWindow):
    """Main window for Invoice Details application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("سیستم مدیریت فاکتور - جزئیات فاکتور")
        self.setGeometry(100, 100, 1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Initialize database
        self.db_manager = DatabaseManager()
        self.invoices_db_session, self.users_session = self.db_manager.get_session()

        # Current user (in real app, this would come from authentication)
        self.current_user = "admin"

        # Initialize UI
        self.init_ui()

        # Initialize controller and connect to view
        self.init_controller()

        # Load initial data
        self.load_initial_data()

    def init_ui(self):
        """Initialize the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Create the invoice details view
        self.invoice_view = InvoiceDetailsView()
        main_layout.addWidget(self.invoice_view)

        # Add control buttons
        self.add_control_buttons(main_layout)

        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)

    def add_control_buttons(self, layout):
        """Add control buttons to the layout."""
        button_layout = QVBoxLayout()

        # Initialize button
        self.init_button = QPushButton("مقداردهی اولیه")
        self.init_button.clicked.connect(self.initialize_invoice)

        # Validate button
        self.validate_button = QPushButton("اعتبارسنجی")
        self.validate_button.clicked.connect(self.validate_data)

        # Clear button
        self.clear_button = QPushButton("پاک‌سازی")
        self.clear_button.clicked.connect(self.clear_data)

        # Load sample data button (for testing)
        self.sample_button = QPushButton("بارگذاری نمونه")
        self.sample_button.clicked.connect(self.load_sample_data)

        button_layout.addWidget(self.init_button)
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.sample_button)

        layout.addLayout(button_layout)

    def init_controller(self):
        """Initialize the controller and connect signals."""
        # Create controller
        self.controller = InvoiceDetailsController(
            invoices_db_session=self.invoices_db_session,
            users_db_session=self.users_session,
            current_user=self.current_user,
            parent=self
        )

        # Set view reference in controller
        self.controller.set_view(self.invoice_view)

        # Connect controller signals
        self.controller.data_loaded.connect(self.on_data_loaded)
        self.controller.error_occurred.connect(self.on_error_occurred)
        self.controller.validation_failed.connect(self.on_validation_failed)
        self.controller.office_info_updated.connect(self.on_office_info_updated)

    def load_initial_data(self):
        """Load initial data when application starts."""
        try:
            # Initialize invoice with some sample data
            sample_customer = CustomerInfo(
                name="احمد محمدی",
                phone="09123456789",
                national_id="1234567890",
                email="ahmad@example.com",
                address="تهران، خیابان ولیعصر",
                total_companions=2
            )

            self.controller.initialize_invoice(
                document_count=5,
                customer_info=sample_customer
            )

        except Exception as e:
            logger.error(f"Error loading initial data: {str(e)}")
            self.show_error_message(f"خطا در بارگذاری اطلاعات اولیه: {str(e)}")

    def initialize_invoice(self):
        """Initialize a new invoice."""
        try:
            self.controller.initialize_invoice()

        except Exception as e:
            logger.error(f"Error initializing invoice: {str(e)}")
            self.show_error_message(f"خطا در مقداردهی فاکتور: {str(e)}")

    def validate_data(self):
        """Validate current invoice data."""
        try:
            is_valid = self.controller.validate_current_data()

            if is_valid:
                self.show_success_message("اطلاعات فاکتور معتبر است")

        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            self.show_error_message(f"خطا در اعتبارسنجی: {str(e)}")

    def clear_data(self):
        """Clear all invoice data."""
        try:
            self.controller.clear_invoice_data()
            self.show_info_message("اطلاعات فاکتور پاک شد")

        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            self.show_error_message(f"خطا در پاک‌سازی: {str(e)}")

    def load_sample_data(self):
        """Load sample data for testing."""
        try:
            # Create sample customer
            sample_customer = CustomerInfo(
                name="سارا احمدی",
                phone="09123456789",
                national_id="0987654321",
                email="sara@example.com",
                address="اصفهان، خیابان چهارباغ",
                total_companions=1
            )

            # Set customer info
            self.controller.set_customer_info(sample_customer)

            # Update costs
            self.controller.update_costs(
                translation_cost=500000,
                confirmation_cost=100000,
                office_affairs_cost=50000,
                copy_cert_cost=25000
            )

            self.show_info_message("اطلاعات نمونه بارگذاری شد")

        except Exception as e:
            logger.error(f"Error loading sample data: {str(e)}")
            self.show_error_message(f"خطا در بارگذاری نمونه: {str(e)}")

    def on_data_loaded(self, data: dict):
        """Handle data loaded signal from controller."""
        logger.info("Invoice data loaded successfully")

        # You can add additional UI updates here
        invoice_data = data.get('invoice_data')
        if invoice_data:
            self.setWindowTitle(f"سیستم مدیریت فاکتور - شماره رسید: {invoice_data.receipt_number}")

    def on_error_occurred(self, error_message: str):
        """Handle error signal from controller."""
        logger.error(f"Controller error: {error_message}")
        self.show_error_message(error_message)

    def on_validation_failed(self, errors: list):
        """Handle validation failed signal from controller."""
        logger.warning(f"Validation failed: {errors}")
        error_text = "\n".join([f"• {error}" for error in errors])
        self.show_error_message(f"خطاهای اعتبارسنجی:\n{error_text}")

    def on_office_info_updated(self, data: dict):
        """Handle office info updated signal from controller."""
        message = data.get('message', 'اطلاعات دارالترجمه به‌روزرسانی شد')
        self.show_success_message(message)

    def show_error_message(self, message: str):
        """Show error message to user."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("خطا")
        msg_box.setText(message)
        msg_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg_box.exec()

    def show_success_message(self, message: str):
        """Show success message to user."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("موفقیت")
        msg_box.setText(message)
        msg_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg_box.exec()

    def show_info_message(self, message: str):
        """Show info message to user."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("اطلاعات")
        msg_box.setText(message)
        msg_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg_box.exec()

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Close database session
            if hasattr(self, 'db_session'):
                self.db_session.close()

            # Close database manager
            if hasattr(self, 'db_manager'):
                self.db_manager.close()

            logger.info("Application closed successfully")
            event.accept()

        except Exception as e:
            logger.error(f"Error closing application: {str(e)}")
            event.accept()  # Still accept the close event


def main():
    """Main entry point."""
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Set application properties
        app.setApplicationName("Invoice Details System")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Translation Office")

        # Create main window
        window = InvoiceDetailsMainWindow()
        window.show()

        # Run application
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        if 'app' in locals():
            # Show error message if app was created
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("خطای سیستم")
            msg_box.setText(f"خطا در راه‌اندازی برنامه:\n{str(e)}")
            msg_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            msg_box.exec()

        sys.exit(1)


if __name__ == "__main__":
    main()
