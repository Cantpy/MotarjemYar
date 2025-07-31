"""
Invoice Management System - Main Application
============================================

This module demonstrates how to integrate all layers of the MVC architecture
for a complete invoice management system.

Usage Examples:
1. Basic setup and initialization
2. Creating and managing customers
3. Creating and managing invoices
4. UI integration with controllers
5. Complete application example
"""

import sys
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import QTimer, Qt

# Import all layers
from models import Customer, Service, Invoice, InvoiceItem, PaymentStatus, DeliveryStatus
from repository import (
    DatabaseManager, SQLAlchemyCustomerRepository, SQLAlchemyServiceRepository,
    SQLAlchemyInvoiceRepository
)
from logic import (
    CustomerService, ServiceService, InvoiceService, PricingService,
    ReportService, BusinessRulesService, ValidationService
)
from controller import ControllerFactory, MainInvoiceController
from view import InvoiceMainWidget


class InvoiceApplication(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setup_database()
        self.setup_services()
        self.setup_controllers()
        self.setup_ui()
        self.setup_connections()

        # Initialize with sample data
        QTimer.singleShot(100, self.initialize_sample_data)

    def setup_database(self):
        """Setup database connections."""
        # Create database directory if it doesn't exist
        db_dir = Path("databases")
        db_dir.mkdir(exist_ok=True)

        # Database paths
        customers_db = str(db_dir / "customers.db")
        invoices_db = str(db_dir / "invoices.db")
        services_db = str(db_dir / "services.db")

        # Create database manager
        self.db_manager = DatabaseManager(customers_db, invoices_db, services_db)

        # Create repositories
        self.customer_repository = SQLAlchemyCustomerRepository(self.db_manager)
        self.service_repository = SQLAlchemyServiceRepository(self.db_manager)
        self.invoice_repository = SQLAlchemyInvoiceRepository(self.db_manager)

    def setup_services(self):
        """Setup business logic services."""
        self.customer_service = CustomerService(self.customer_repository)
        self.service_service = ServiceService(self.service_repository)
        self.invoice_service = InvoiceService(self.invoice_repository, self.customer_service)
        self.pricing_service = PricingService(self.service_service)
        self.report_service = ReportService(self.invoice_service, self.customer_service)
        self.business_rules_service = BusinessRulesService()

    def setup_controllers(self):
        """Setup controllers."""
        self.controller_factory = ControllerFactory(
            self.customer_service,
            self.service_service,
            self.invoice_service,
            self.pricing_service,
            self.report_service,
            self.business_rules_service
        )

        self.main_controller = self.controller_factory.create_main_controller(self)

    def setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("سیستم مدیریت فاکتور")
        self.setMinimumSize(1200, 800)

        # Create main widget
        self.main_widget = InvoiceMainWidget(self)
        self.setCentralWidget(self.main_widget)

        # Set up window properties
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def setup_connections(self):
        """Setup connections between controllers and UI."""
        # Connect main controller signals
        self.main_controller.status_changed.connect(self.show_status_message)
        self.main_controller.error_occurred.connect(self.show_error_message)
        self.main_controller.success_occurred.connect(self.show_success_message)
        self.main_controller.form_cleared.connect(self.on_form_cleared)
        self.main_controller.totals_updated.connect(self.on_totals_updated)

        # Connect UI signals to controller
        self.main_widget.invoice_saved.connect(self.on_invoice_save_requested)
        self.main_widget.invoice_preview_requested.connect(self.on_invoice_preview_requested)

        # Connect customer controller
        customer_controller = self.main_controller.customer_controller
        customer_controller.customer_found.connect(self.on_customer_found)
        customer_controller.customer_saved.connect(self.on_customer_saved)
        customer_controller.customer_deleted.connect(self.on_customer_deleted)

        # Connect customer widget signals
        customer_widget = self.main_widget.customer_widget
        customer_widget.save_customer_requested.connect(self.on_customer_save_requested)
        customer_widget.delete_customer_requested.connect(self.on_customer_delete_requested)
        customer_widget.customer_search_requested.connect(self.on_customer_search_requested)

        # Connect service controller
        service_controller = self.main_controller.service_controller
        service_controller.service_names_loaded.connect(self.on_service_names_loaded)

        # Initialize data
        self.load_initial_data()

    def load_initial_data(self):
        """Load initial data for the application."""
        # Load service names for autocomplete
        self.main_controller.service_controller.load_service_names()

        # Load customer suggestions
        suggestions = {
            'name': self.main_controller.customer_controller.get_customer_suggestions('name'),
            'phone': self.main_controller.customer_controller.get_customer_suggestions('phone'),
            'national_id': self.main_controller.customer_controller.get_customer_suggestions('national_id')
        }
        self.main_widget.customer_widget.set_completers(suggestions)

        # Generate invoice number
        self.main_controller.initialize_new_invoice()

    def initialize_sample_data(self):
        """Initialize sample data for demonstration."""
        try:
            # Add sample services if they don't exist
            services_result = self.service_service.get_all_services()
            if services_result.success and not services_result.data:
                sample_services = [
                    Service(name="ترجمه رسمی پاسپورت", base_price=150000),
                    Service(name="ترجمه شناسنامه", base_price=100000),
                    Service(name="ترجمه گواهینامه", base_price=120000),
                    Service(name="ترجمه مدرک تحصیلی", base_price=200000),
                    Service(name="ترجمه قرارداد", base_price=300000, dynamic_price_1=250000,
                            dynamic_price_name_1="قیمت ویژه"),
                ]

                for service in sample_services:
                    self.service_repository.save(service)

                # Reload service names
                self.main_controller.service_controller.load_service_names()

        except Exception as e:
            print(f"Error initializing sample data: {e}")

    # Signal handlers
    def show_status_message(self, message: str):
        """Show status message."""
        self.statusBar().showMessage(message, 3000)

    def show_error_message(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "خطا", message)

    def show_success_message(self, message: str):
        """Show success message."""
        self.statusBar().showMessage(f"✓ {message}", 5000)

    def on_form_cleared(self):
        """Handle form cleared event."""
        invoice_number = self.invoice_service.get_current_invoice_number()
        self.main_widget.set_invoice_number(invoice_number)

    def on_totals_updated(self, totals: dict):
        """Handle totals updated event."""
        # Update UI with new totals if needed
        pass

    def on_invoice_save_requested(self, invoice_data: dict):
        """Handle invoice save request."""
        success = self.main_controller.finalize_invoice(invoice_data)
        if success:
            self.show_success_message("فاکتور با موفقیت ذخیره شد!")

    def on_invoice_preview_requested(self, invoice_data: dict):
        """Handle invoice preview request."""
        # Validate data first
        errors = self.main_controller.validate_invoice_form(invoice_data)
        if errors:
            error_messages = [f"{error.field}: {error.message}" for error in errors]
            QMessageBox.warning(self, "خطای اعتبارسنجی", "\n".join(error_messages))
            return

        # Show preview (implement preview window as needed)
        QMessageBox.information(self, "پیش‌نمایش فاکتور", "پیش‌نمایش فاکتور در نسخه آینده پیاده‌سازی خواهد شد.")

    def on_customer_found(self, customer: Customer):
        """Handle customer found event."""
        self.main_widget.customer_widget.set_customer_data(customer)

    def on_customer_saved(self, customer: Customer):
        """Handle customer saved event."""
        self.show_success_message(f"مشتری {customer.name} ذخیره شد!")

    def on_customer_deleted(self, national_id: str):
        """Handle customer deleted event."""
        self.show_success_message(f"مشتری با کد ملی {national_id} حذف شد!")
        self.main_widget.customer_widget.clear_form()

    def on_customer_save_requested(self, customer_data: dict):
        """Handle customer save request."""
        self.main_controller.customer_controller.save_customer(**customer_data)

    def on_customer_delete_requested(self, national_id: str):
        """Handle customer delete request."""
        self.main_controller.customer_controller.delete_customer(national_id)

    def on_customer_search_requested(self, field_type: str, value: str):
        """Handle customer search request."""
        if len(value) >= 3:  # Only search after 3 characters
            self.main_controller.autofill_customer_data(field_type, value)

    def on_service_names_loaded(self, service_names: list):
        """Handle service names loaded event."""
        self.main_widget.service_input.set_service_completer(service_names)

    def closeEvent(self, event):
        """Handle application close event."""
        # Clean up database connections
        if hasattr(self, 'db_manager'):
            self.db_manager.customers_engine.dispose()
            self.db_manager.invoices_engine.dispose()
            self.db_manager.services_engine.dispose()

        event.accept()


def create_sample_customer() -> Customer:
    """Create a sample customer for testing."""
    return Customer(
        national_id="1234567890",
        name="احمد محمدی",
        phone="09123456789",
        address="تهران، خیابان ولیعصر، پلاک 123",
        email="ahmad@example.com"
    )


def create_sample_service() -> Service:
    """Create a sample service for testing."""
    return Service(
        name="ترجمه رسمی پاسپورت",
        base_price=150000,
        dynamic_price_1=120000,
        dynamic_price_name_1="قیمت ویژه"
    )


def create_sample_invoice(customer: Customer) -> Invoice:
    """Create a sample invoice for testing."""
    invoice = Invoice(
        invoice_number=1001,
        name=customer.name,
        national_id=customer.national_id,
        phone=customer.phone,
        issue_date=date.today(),
        delivery_date=date.today() + timedelta(days=3),
        translator="علی رضایی",
        source_language="انگلیسی",
        target_language="فارسی"
    )

    # Add sample items
    item1 = InvoiceItem(
        invoice_number=1001,
        item_name="ترجمه رسمی پاسپورت",
        item_qty=1,
        item_price=150000,
        officiality=1
    )

    item2 = InvoiceItem(
        invoice_number=1001,
        item_name="ترجمه شناسنامه",
        item_qty=2,
        item_price=100000
    )

    invoice.add_item(item1)
    invoice.add_item(item2)

    return invoice


def example_basic_usage():
    """Example of basic usage without UI."""
    print("=== Basic Usage Example ===")

    # Setup database (in-memory for testing)
    db_manager = DatabaseManager(":memory:", ":memory:", ":memory:")

    # Setup repositories
    customer_repo = SQLAlchemyCustomerRepository(db_manager)
    service_repo = SQLAlchemyServiceRepository(db_manager)
    invoice_repo = SQLAlchemyInvoiceRepository(db_manager)

    # Setup services
    customer_service = CustomerService(customer_repo)
    service_service = ServiceService(service_repo)
    invoice_service = InvoiceService(invoice_repo, customer_service)

    # Create sample data
    customer = create_sample_customer()
    service = create_sample_service()

    # Save customer
    result = customer_service.save_customer(
        customer.national_id, customer.name, customer.phone, customer.address,
        email=customer.email
    )
    print(f"Customer save result: {result.message}")

    # Save service
    saved_service = service_repo.save(service)
    print(f"Service saved: {saved_service.name}")

    # Create invoice
    invoice_result = invoice_service.create_invoice(
        invoice_number=1001,
        name=customer.name,
        national_id=customer.national_id,
        phone=customer.phone,
        issue_date=date.today(),
        delivery_date=date.today() + timedelta(days=3),
        translator="علی رضایی"
    )
    print(f"Invoice create result: {invoice_result.message}")

    if invoice_result.success:
        # Add items to invoice
        item_result = invoice_service.add_invoice_item(
            1001, "ترجمه رسمی پاسپورت", 1, 150000, officiality=1
        )
        print(f"Add item result: {item_result.message}")

        # Get invoice with items
        invoice_get_result = invoice_service.get_invoice_by_number(1001)
        if invoice_get_result.success:
            invoice = invoice_get_result.data
            print(f"Invoice total: {invoice.final_amount}")
            print(f"Items count: {len(invoice.items)}")


def example_validation():
    """Example of validation usage."""
    print("\n=== Validation Example ===")

    validator = ValidationService()

    # Test customer validation
    errors = validator.validate_customer_data("", "123", "12345", "addr")
    print("Customer validation errors:")
    for error in errors:
        print(f"  {error.field}: {error.message}")

    # Test valid customer data
    errors = validator.validate_customer_data("احمد محمدی", "09123456789", "1234567890", "تهران، خیابان ولیعصر")
    print(f"Valid customer data errors: {len(errors)}")


def example_business_rules():
    """Example of business rules usage."""
    print("\n=== Business Rules Example ===")

    # Setup minimal services
    db_manager = DatabaseManager(":memory:", ":memory:", ":memory:")
    customer_repo = SQLAlchemyCustomerRepository(db_manager)
    invoice_repo = SQLAlchemyInvoiceRepository(db_manager)
    customer_service = CustomerService(customer_repo)
    invoice_service = InvoiceService(invoice_repo, customer_service)

    business_rules = BusinessRulesService()

    # Create sample invoice
    invoice = create_sample_invoice(create_sample_customer())

    # Test modification rules
    can_modify = business_rules.can_modify_invoice(invoice)
    print(f"Can modify unpaid invoice: {can_modify.success}")

    # Mark as paid and test again
    invoice.payment_status = PaymentStatus.PAID
    can_modify = business_rules.can_modify_invoice(invoice)
    print(f"Can modify paid invoice: {can_modify.success}")
    print(f"Message: {can_modify.message}")


def run_gui_application():
    """Run the complete GUI application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Invoice Management System")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Translation Services")

    # Create and show main window
    window = InvoiceApplication()
    window.show()

    # Run application
    return app.exec()


def main():
    """Main function demonstrating all examples."""
    print("Invoice Management System - MVC Architecture Demo")
    print("=" * 50)

    # Run examples
    example_basic_usage()
    example_validation()
    example_business_rules()

    print("\n" + "=" * 50)
    print("Starting GUI Application...")
    print("Close the window to exit.")

    # Run GUI application
    sys.exit(run_gui_application())


if __name__ == "__main__":
    main()


# Additional utility functions for testing and development

def create_test_database():
    """Create a test database with sample data."""
    from pathlib import Path

    # Create test database directory
    test_db_dir = Path("test_databases")
    test_db_dir.mkdir(exist_ok=True)

    # Setup database
    db_manager = DatabaseManager(
        str(test_db_dir / "test_customers.db"),
        str(test_db_dir / "test_invoices.db"),
        str(test_db_dir / "test_services.db")
    )

    # Setup repositories
    customer_repo = SQLAlchemyCustomerRepository(db_manager)
    service_repo = SQLAlchemyServiceRepository(db_manager)
    invoice_repo = SQLAlchemyInvoiceRepository(db_manager)

    # Add sample customers
    sample_customers = [
        Customer("1234567890", "احمد محمدی", "09123456789", "تهران، ولیعصر"),
        Customer("0987654321", "فاطمه احمدی", "09187654321", "اصفهان، چهارباغ"),
        Customer("1122334455", "محمد رضایی", "09121122334", "شیراز، زند"),
    ]

    for customer in sample_customers:
        try:
            customer_repo.save(customer)
            print(f"Added customer: {customer.name}")
        except Exception as e:
            print(f"Error adding customer {customer.name}: {e}")

    # Add sample services
    sample_services = [
        Service("ترجمه رسمی پاسپورت", 150000),
        Service("ترجمه شناسنامه", 100000),
        Service("ترجمه مدرک تحصیلی", 200000),
        Service("ترجمه قرارداد", 300000),
        Service("ترجمه گواهینامه", 120000),
    ]

    for service in sample_services:
        try:
            service_repo.save(service)
            print(f"Added service: {service.name}")
        except Exception as e:
            print(f"Error adding service {service.name}: {e}")

    print("Test database created successfully!")
    return db_manager


def run_tests():
    """Run basic tests on the system."""
    print("Running system tests...")

    try:
        # Test database creation
        db_manager = create_test_database()

        # Test services
        customer_repo = SQLAlchemyCustomerRepository(db_manager)
        customer_service = CustomerService(customer_repo)

        # Test customer operations
        result = customer_service.get_all_customers()
        print(f"Found {len(result.data)} customers")

        # Test customer search
        customer = customer_service.get_customer_by_national_id("1234567890")
        if customer.success:
            print(f"Found customer: {customer.data.name}")

        print("All tests passed!")

    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            run_tests()
        elif sys.argv[1] == "--create-test-db":
            create_test_database()
        elif sys.argv[1] == "--examples":
            example_basic_usage()
            example_validation()
            example_business_rules()
        else:
            print("Available options:")
            print("  --test: Run system tests")
            print("  --create-test-db: Create test database")
            print("  --examples: Run examples without GUI")
            print("  (no args): Run full GUI application")
    else:
        main()
