# -*- coding: utf-8 -*-
"""
Testing Version - Uses InMemoryCustomerRepository for testing and development
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from features.InvoicePage.customer_info.customer_info_models import (CustomerData, CustomerInfoData, CompanionData)
from features.InvoicePage.customer_info.customer_info_repo import InMemoryCustomerRepository
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic, CustomerManagementLogic
from features.InvoicePage.customer_info.customer_info_controller import ControllerFactory
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView


class TestMainWindow(QMainWindow):
    """Test main application window using in-memory repository."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Management System - Test Mode")
        self.setGeometry(100, 100, 1200, 800)

        # Setup in-memory repository
        self.setup_repository()

        # Setup UI
        self.setup_ui()

    def setup_repository(self):
        """Setup in-memory repository with test data."""
        self.customer_repository = InMemoryCustomerRepository()

        # Add some demo data for testing
        self._add_demo_data()

    def _add_demo_data(self):
        """Add demo customers for testing."""
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
            CustomerData(
                national_id="1122334455",
                name="محمد کریمی",
                phone="09112233445",
                email="mohammad@example.com",
                address="شیراز، خیابان زند"
            ),
        ]

        for customer in demo_customers:
            self.customer_repository.create_customer(customer)

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


class CustomerInfoTestApp:
    """Test application class using in-memory repository."""

    def __init__(self):
        """Initialize test application."""
        self.app = QApplication(sys.argv)

        # Setup in-memory repository for testing
        self.repository = InMemoryCustomerRepository()

        # Create main window
        self.main_window = TestMainWindow()

    def run(self):
        """Run the application."""
        self.main_window.show()
        return self.app.exec()


def demonstrate_logic_layer():
    """Demonstrate the business logic layer independently."""
    print("=== Logic Layer Demo ===")

    # Create repository
    repository = InMemoryCustomerRepository()

    # Create logic instance
    logic = CustomerInfoLogic(repository)

    # Test customer creation
    customer_data = CustomerData(
        national_id="1234567890",
        name="Test Customer",
        phone="09123456789",
        email="test@example.com"
    )

    result = logic.set_customer_data(customer_data)
    print(f"Customer validation: {result.is_valid}")
    if not result.is_valid:
        print(f"Errors: {result.errors}")

    # Test companion addition
    logic.set_companions_status(True)
    companion_index, companion_result = logic.add_companion("Companion Name", "0987654321")
    print(f"Companion added at index {companion_index}, valid: {companion_result.is_valid}")

    # Get summary
    summary = logic.get_summary()
    print(f"Summary: {summary}")

    # Export data
    export_data = logic.get_export_data()
    print(f"Export data: {export_data}")


def demonstrate_repository_layer():
    """Demonstrate the repository layer independently."""
    print("=== Repository Layer Demo ===")

    # Create repository
    repository = InMemoryCustomerRepository()

    # Create test customer
    customer = CustomerData(
        national_id="1111111111",
        name="Repository Test",
        phone="09111111111",
        email="repo@test.com"
    )

    # Test CRUD operations
    print(f"Creating customer: {repository.create_customer(customer)}")
    print(f"Customer exists: {repository.customer_exists('1111111111')}")

    # Retrieve customer
    retrieved = repository.get_by_national_id("1111111111")
    print(f"Retrieved customer: {retrieved.name if retrieved else 'Not found'}")

    # Update customer
    if retrieved:
        retrieved.email = "updated@test.com"
        print(f"Updating customer: {repository.update_customer(retrieved)}")

    # Search customers
    from features.InvoicePage.customer_info.customer_info_models import CustomerSearchCriteria
    criteria = CustomerSearchCriteria(name="Repository")
    results = repository.search_customers(criteria)
    print(f"Search results: {len(results)} customers found")


def demonstrate_models():
    """Demonstrate the models layer."""
    print("=== Models Layer Demo ===")

    # Test CustomerData
    customer = CustomerData(
        national_id="1234567890",
        name="Test Customer",
        phone="09123456789"
    )

    print(f"Customer valid: {customer.is_valid()}")
    print(f"Customer dict: {customer.to_dict()}")

    # Test validation errors
    invalid_customer = CustomerData(
        national_id="123",  # Invalid
        name="",  # Empty
        phone="invalid"  # Invalid
    )

    print(f"Invalid customer errors: {invalid_customer.get_validation_errors()}")

    # Test CompanionData
    companion = CompanionData(
        name="Companion Name",
        national_id="0987654321",
        ui_number=1
    )

    print(f"Companion valid: {companion.is_valid()}")

    # Test CustomerInfoData
    customer_info = CustomerInfoData(
        customer=customer,
        has_companions=True,
        companions=[companion]
    )

    print(f"Customer info valid: {customer_info.is_valid()}")
    print(f"Total people: {customer_info.get_total_people()}")
    print(f"Summary: {customer_info.get_summary()}")


def example_validation_scenarios():
    """Example of various validation scenarios."""
    print("=== Validation Scenarios ===")

    # Test valid Iranian national ID
    valid_ids = ["0013542419", "1111111146", "0000000018"]
    invalid_ids = ["1234567890", "0000000000", "123456789"]

    print("Testing National ID validation:")
    for nid in valid_ids + invalid_ids:
        customer = CustomerData(national_id=nid, name="Test", phone="09123456789")
        is_valid = customer._is_valid_national_id(nid)
        print(f"  {nid}: {'✓' if is_valid else '✗'}")

    # Test phone validation
    valid_phones = ["09123456789", "9123456789", "02112345678"]
    invalid_phones = ["123456", "abcd", "091234567890"]

    print("\nTesting Phone validation:")
    for phone in valid_phones + invalid_phones:
        customer = CustomerData(national_id="0013542419", name="Test", phone=phone)
        is_valid = customer._is_valid_phone(phone)
        print(f"  {phone}: {'✓' if is_valid else '✗'}")


def run_all_tests():
    """Run all test demonstrations."""
    print("Starting Customer Management System Tests\n")

    demonstrate_models()
    print("\n" + "=" * 50 + "\n")

    demonstrate_repository_layer()
    print("\n" + "=" * 50 + "\n")

    demonstrate_logic_layer()
    print("\n" + "=" * 50 + "\n")

    example_validation_scenarios()
    print("\n" + "=" * 50 + "\n")

    print("All tests completed successfully!")


if __name__ == "__main__":
    # Run demonstrations
    run_all_tests()
    print("\n" + "=" * 50 + "\n")

    # Run the GUI application
    print("Starting Test GUI Application...")
    app = CustomerInfoTestApp()
    sys.exit(app.run())
