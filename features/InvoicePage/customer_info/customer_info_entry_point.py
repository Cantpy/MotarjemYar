# -*- coding: utf-8 -*-
"""
Production Version - Uses SQLAlchemy CustomerRepository for production
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from features.InvoicePage.customer_info.customer_info_models import (CustomerData)
from features.InvoicePage.customer_info.customer_info_repo import CustomerRepository
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView

from features.InvoicePage.customer_management.customer_management_view import CustomerManagementView

from shared.models.sqlalchemy_models import CustomerModel, CompanionModel
from shared import return_resource

customers_database = return_resource('databases', 'customers.db')
print(f"Customer database: {customers_database}")


class MainWindow(QMainWindow):
    """Main application window for production."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Management System")
        self.setGeometry(100, 100, 1200, 800)

        # Setup database
        self.setup_database()

        # Setup UI
        self.setup_ui()

    def setup_database(self):
        """Setup database connection and repository."""
        try:
            # Create engine
            engine = create_engine(f'sqlite:///{customers_database}', echo=False)

            # Only create CustomerModel and CompanionModel tables
            CustomerModel.__table__.create(engine, checkfirst=True)
            CompanionModel.__table__.create(engine, checkfirst=True)

            Session = sessionmaker(bind=engine)
            db_session = Session()
            self.customer_repository = CustomerRepository(db_session)

        except Exception as e:
            print(f"Database setup error: {e}")
            raise

    def setup_ui(self):
        """Setup main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.customer_info_view = CustomerInfoView(self.customer_repository, self)
        layout.addWidget(self.customer_info_view)

        # Connect signals for navigation and actions
        self.customer_info_view.customer_affairs_requested.connect(self.open_customer_affairs_dialog)

    def open_customer_affairs_dialog(self):
        """Handles the request from the view to open the management dialog."""
        # Here you would instantiate and show the CustomerManagementDialog
        print("LOG: Opening customer affairs dialog...")
        dialog = CustomerManagementView(self)
        dialog.exec()

    def on_customer_data_changed(self, data):
        """Handle customer data changes."""
        print(f"Customer data changed: {data}")

    def on_validation_changed(self, is_valid):
        """Handle validation state changes."""
        print(f"Validation state: {'Valid' if is_valid else 'Invalid'}")

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Close database session
            if hasattr(self, 'customer_repository') and hasattr(self.customer_repository, 'session'):
                self.customer_repository.session.close()
        except Exception as e:
            print(f"Error closing database: {e}")

        event.accept()


class CustomerInfoApp:
    """Production application class using database repository."""

    def __init__(self):
        """Initialize application."""
        self.app = QApplication(sys.argv)

        # Create main window (database setup is handled in MainWindow_gaming)
        self.main_window = MainWindow()

    def run(self):
        """Run the application."""
        self.main_window.show()
        return self.app.exec()


def create_database_tables():
    """Utility function to create only the required database tables."""
    try:
        engine = create_engine(f'sqlite:///{customers_database}', echo=False)

        # Create only the specific tables we need
        CustomerModel.__table__.create(engine, checkfirst=True)
        CompanionModel.__table__.create(engine, checkfirst=True)

        print("Database tables created successfully")
        return engine
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise


def example_with_real_database():
    """Example of using the system with a real SQLAlchemy database."""
    try:
        # Create database engine and tables
        engine = create_database_tables()
        Session = sessionmaker(bind=engine)
        db_session = Session()

        # Create repository with real database
        repository = CustomerRepository(db_session)

        # Use the repository with business logic
        logic = CustomerInfoLogic(repository)

        # Example usage
        customer = CustomerData(
            national_id="1234567890",
            name="Real DB Customer",
            phone="09123456789",
            email="realdb@example.com",
            address="Real Address"
        )

        result = logic.set_customer_data(customer)
        if result.is_valid:
            save_result = logic.save_customer()
            print(f"Customer saved to database: {save_result.is_valid}")

            # Verify customer exists
            exists = repository.customer_exists("1234567890")
            print(f"Customer exists in database: {exists}")
        else:
            print(f"Customer validation failed: {result.errors}")

        # Close session
        db_session.close()

    except Exception as e:
        print(f"Database example error: {e}")


if __name__ == "__main__":

    # Run database example
    print("Testing database operations...")
    example_with_real_database()
    print("\n" + "=" * 50 + "\n")

    # Run the GUI application
    print("Starting Production GUI Application...")
    try:
        app = CustomerInfoApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)
