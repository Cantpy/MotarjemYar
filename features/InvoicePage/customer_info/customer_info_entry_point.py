# -*- coding: utf-8 -*-
"""
Production Version - Uses SQLAlchemy CustomerRepository for production
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from features.InvoicePage.customer_info.customer_info_models import (CustomerData, CustomerInfoData, CompanionData)
from features.InvoicePage.customer_info.customer_info_repo import CustomerRepository
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic, CustomerManagementLogic
from features.InvoicePage.customer_info.customer_info_controller import ControllerFactory
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView

# Import only the specific models we need to avoid creating unnecessary tables
from shared.entities.common_sqlalchemy_bases import CustomerModel, CompanionModel, Base
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

            # Create only the tables we need - this should prevent extra tables
            # Only create CustomerModel and CompanionModel tables
            CustomerModel.__table__.create(engine, checkfirst=True)
            CompanionModel.__table__.create(engine, checkfirst=True)

            # Alternative approach if you prefer:
            # Base.metadata.create_all(engine, tables=[CustomerModel.__table__, CompanionModel.__table__])

            Session = sessionmaker(bind=engine)
            db_session = Session()
            self.customer_repository = CustomerRepository(db_session)

            # Add some demo data if database is empty
            self._add_demo_data()

        except Exception as e:
            print(f"Database setup error: {e}")
            raise

    def _add_demo_data(self):
        """Add demo customers for testing if database is empty."""
        try:
            # Check if database has data
            if not self.customer_repository.get_all_customers():
                demo_customers = [
                    CustomerData(
                        national_id="1234567890",
                        name="علی احمدی",
                        phone="09123456789",
                        email="ali@example.com",
                        address="تهران، خیابان آزادی"
                    ),
                    CustomerData(
                        national_id="0987654321",
                        name="فاطمه محمدی",
                        phone="09987654321",
                        email="fateme@example.com",
                        address="اصفهان، خیابان چهارباغ"
                    ),
                ]

                for customer in demo_customers:
                    self.customer_repository.create_customer(customer)

                print("Demo data added to database")
        except Exception as e:
            print(f"Error adding demo data: {e}")

    def setup_ui(self):
        """Setup main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create customer info view with repository
        self.customer_info_view = CustomerInfoView(self.customer_repository, self)
        layout.addWidget(self.customer_info_view)

        # Connect signals
        self.customer_info_view.data_changed.connect(self.on_customer_data_changed)
        self.customer_info_view.validation_changed.connect(self.on_validation_changed)

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

        # Create main window (database setup is handled in MainWindow)
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


def verify_database_structure():
    """Verify that only the expected tables exist in the database."""
    try:
        from sqlalchemy import inspect

        engine = create_engine(f'sqlite:///{customers_database}')
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")

        expected_tables = ['customers', 'companions']
        unexpected_tables = [t for t in tables if t not in expected_tables]

        if unexpected_tables:
            print(f"WARNING: Unexpected tables found: {unexpected_tables}")
        else:
            print("Database structure is correct - only expected tables found")

        # Show table details
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            print(f"\nTable '{table_name}':")
            print(f"  Columns: {[col['name'] for col in columns]}")
            print(f"  Indexes: {len(indexes)} indexes")

        return tables
    except Exception as e:
        print(f"Error verifying database structure: {e}")
        return []


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
    print("Customer Management System - Production Mode")
    print("=" * 50)

    # Verify database structure first
    print("Verifying database structure...")
    verify_database_structure()
    print("\n" + "=" * 50 + "\n")

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
