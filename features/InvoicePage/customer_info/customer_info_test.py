# -*- coding: utf-8 -*-
"""
Usage Example - How to integrate all layers
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your refactored modules
from features.InvoicePage.customer_info.customer_info_models import (CustomerData, CustomerInfoData, CompanionData)
from features.InvoicePage.customer_info.customer_info_repo import CustomerRepository, InMemoryCustomerRepository
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic, CustomerManagementLogic
from features.InvoicePage.customer_info.customer_info_controller import CustomerInfoController, ControllerFactory
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView


# Your existing database model (example)
# from your_database_models import Customer, Base


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer Management System")
        self.setGeometry(100, 100, 1200, 800)

        # Setup database (example with in-memory for demo)
        self.setup_database()

        # Setup UI
        self.setup_ui()

    def setup_database(self):
        """Setup database connection and repository."""
        # Option 1: Use SQLAlchemy with real database
        # engine = create_engine('sqlite:///customers.db')
        # Base.metadata.create_all(engine)
        # Session = sessionmaker(bind=engine)
        # db_session = Session()
        # self.customer_repository = CustomerRepository(db_session)

        # Option 2: Use in-memory repository for demo
        self.customer_repository = InMemoryCustomerRepository()

        # Add some demo data
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


class CustomerInfoApp:
    """Application class that demonstrates the complete integration."""

    def __init__(self):
        """Initialize application."""
        self.app = QApplication(sys.argv)

        # Setup database repository
        self.setup_repository()

        # Create main window
        self.main_window = MainWindow()

    def setup_repository(self):
        """Setup repository based on configuration."""
        # You can switch between different repository implementations
        use_database = False  # Set to True to use SQLAlchemy

        if use_database:
            # Real database setup
            engine = create_engine('sqlite:///customers.db')
            # Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            db_session = Session()
            self.repository = CustomerRepository(db_session)
        else:
            # In-memory repository for demo
            self.repository = InMemoryCustomerRepository()

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


if __name__ == "__main__":
    # Run demonstrations
    demonstrate_models()
    print("\n" + "=" * 50 + "\n")

    demonstrate_repository_layer()
    print("\n" + "=" * 50 + "\n")

    demonstrate_logic_layer()
    print("\n" + "=" * 50 + "\n")

    # Run the GUI application
    print("Starting GUI Application...")
    app = CustomerInfoApp()
    sys.exit(app.run())


# Alternative usage examples for different scenarios

def example_with_real_database():
    """Example of using the system with a real SQLAlchemy database."""
    from sqlalchemy import create_engine, Column, String
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker

    # Your existing database model
    Base = declarative_base()

    class Customer(Base):
        __tablename__ = 'customers'

        national_id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        phone = Column(String, nullable=False, unique=True)
        telegram_id = Column(String)
        email = Column(String)
        address = Column(String)
        passport_image = Column(String)

    # Setup database
    engine = create_engine('sqlite:///customers.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # Create repository with real database
    repository = CustomerRepository(db_session)

    # Use the repository with your business logic
    logic = CustomerInfoLogic(repository)

    # Example usage
    customer = CustomerData(
        national_id="1234567890",
        name="Real DB Customer",
        phone="09123456789"
    )

    result = logic.set_customer_data(customer)
    if result.is_valid:
        save_result = logic.save_customer()
        print(f"Customer saved: {save_result.is_valid}")


def example_controller_usage():
    """Example of using controllers directly."""
    # Create repository
    repository = InMemoryCustomerRepository()

    # Create controller
    controller = ControllerFactory.create_customer_info_controller(repository)

    # Simulate UI interactions
    controller.on_national_id_changed("1234567890")
    controller.on_full_name_changed("Controller Test")
    controller.on_phone_changed("09123456789")

    # Check if data is valid
    is_valid = controller.is_valid()
    print(f"Controller data valid: {is_valid}")

    # Get data
    data = controller.get_data()
    print(f"Controller data: {data}")

    # Test companion operations
    controller.on_has_companions_changed(True)
    controller.on_add_companion_clicked()

    # Simulate companion field changes
    # Note: This would normally come from UI widgets
    controller.on_companion_field_changed(1, 'name', 'Companion Name')
    controller.on_companion_field_changed(1, 'national_id', '0987654321')


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


def example_error_handling():
    """Example of error handling patterns."""
    print("=== Error Handling Examples ===")

    repository = InMemoryCustomerRepository()
    logic = CustomerInfoLogic(repository)

    # Test duplicate national ID
    customer1 = CustomerData(
        national_id="1234567890",
        name="First Customer",
        phone="09111111111"
    )

    customer2 = CustomerData(
        national_id="1234567890",  # Same national ID
        name="Second Customer",
        phone="09222222222"
    )

    # Create first customer
    repository.create_customer(customer1)

    # Try to create second customer with same national ID
    result = logic.set_customer_data(customer2)
    print(f"Duplicate national ID result: {result.is_valid}")
    if not result.is_valid:
        print(f"Errors: {result.errors}")

    # Test invalid companion data
    logic.set_companions_status(True)
    logic.add_companion("", "invalid_id")  # Invalid national ID

    validation_result = logic.validate_all_data()
    print(f"Overall validation: {validation_result.is_valid}")
    if not validation_result.is_valid:
        print(f"All errors: {validation_result.errors}")


def example_data_import_export():
    """Example of data import/export functionality."""
    print("=== Data Import/Export Examples ===")

    logic = CustomerInfoLogic(InMemoryCustomerRepository())

    # Create sample data
    sample_data = {
        'national_id': '1234567890',
        'name': 'Export Test Customer',
        'phone': '09123456789',
        'email': 'export@test.com',
        'address': 'Test Address',
        'has_companions': True,
        'companions': [
            {
                'name': 'Companion 1',
                'national_id': '0987654321',
                'phone': '09987654321',
                'ui_number': 1
            },
            {
                'name': 'Companion 2',
                'national_id': '1122334455',
                'phone': '09112233445',
                'ui_number': 2
            }
        ]
    }

    # Import data
    import_result = logic.import_data(sample_data)
    print(f"Import successful: {import_result.is_valid}")

    # Export data
    if import_result.is_valid:
        exported_data = logic.get_export_data()
        print(f"Exported data: {exported_data}")

        # Get summary
        summary = logic.get_summary()
        print(f"Data summary: {summary}")


def example_advanced_search():
    """Example of advanced search functionality."""
    print("=== Advanced Search Examples ===")

    repository = InMemoryCustomerRepository()
    management_logic = CustomerManagementLogic(repository)

    # Add test customers
    test_customers = [
        CustomerData("1111111111", "علی احمدی", "09111111111", "ali@test.com", "تهران"),
        CustomerData("2222222222", "فاطمه رضایی", "09222222222", "fateme@test.com", "اصفهان"),
        CustomerData("3333333333", "محمد کریمی", "09333333333", "mohammad@test.com", "شیراز"),
        CustomerData("4444444444", "زهرا محمدی", "09444444444", "zahra@test.com", "مشهد"),
    ]

    for customer in test_customers:
        repository.create_customer(customer)

    # Test different search scenarios
    search_terms = ["علی", "09222", "mohammad@test", "رضایی"]

    for term in search_terms:
        results = management_logic.search_customers(term)
        print(f"Search '{term}': {len(results)} results")
        for customer in results:
            print(f"  - {customer.name} ({customer.national_id})")


def example_integration_testing():
    """Example of integration testing across all layers."""
    print("=== Integration Testing ===")

    # Test complete workflow
    repository = InMemoryCustomerRepository()
    logic = CustomerInfoLogic(repository)

    # Step 1: Create customer
    print("1. Creating customer...")
    customer_data = CustomerData(
        national_id="1234567890",
        name="Integration Test",
        phone="09123456789",
        email="integration@test.com"
    )

    result = logic.set_customer_data(customer_data)
    assert result.is_valid, f"Customer creation failed: {result.errors}"
    print("   ✓ Customer created successfully")

    # Step 2: Add companions
    print("2. Adding companions...")
    logic.set_companions_status(True)

    companion1_idx, comp1_result = logic.add_companion("Companion 1", "0987654321")
    assert comp1_result.is_valid, f"Companion 1 failed: {comp1_result.errors}"

    companion2_idx, comp2_result = logic.add_companion("Companion 2", "1122334455")
    assert comp2_result.is_valid, f"Companion 2 failed: {comp2_result.errors}"
    print("   ✓ Companions added successfully")

    # Step 3: Validate all data
    print("3. Validating all data...")
    validation = logic.validate_all_data()
    assert validation.is_valid, f"Validation failed: {validation.errors}"
    print("   ✓ All data is valid")

    # Step 4: Save customer
    print("4. Saving customer...")
    save_result = logic.save_customer()
    assert save_result.is_valid, f"Save failed: {save_result.errors}"
    print("   ✓ Customer saved successfully")

    # Step 5: Verify customer exists
    print("5. Verifying customer exists...")
    exists = repository.customer_exists("1234567890")
    assert exists, "Customer not found in repository"
    print("   ✓ Customer verified in repository")

    # Step 6: Export and reimport data
    print("6. Testing export/import...")
    exported_data = logic.get_export_data()

    # Clear and reimport
    logic.clear_all_data()
    import_result = logic.import_data(exported_data)
    assert import_result.is_valid, f"Import failed: {import_result.errors}"

    # Verify data integrity
    current_data = logic.get_current_data()
    assert current_data.customer.name == "Integration Test"
    assert len(current_data.companions) == 2
    print("   ✓ Export/import successful")

    print("All integration tests passed! ✓")


# Factory pattern example for different configurations
class CustomerSystemFactory:
    """Factory for creating different system configurations."""

    @staticmethod
    def create_development_system():
        """Create system with in-memory repository for development."""
        repository = InMemoryCustomerRepository()
        return {
            'repository': repository,
            'logic': CustomerInfoLogic(repository),
            'management': CustomerManagementLogic(repository)
        }

    @staticmethod
    def create_production_system(database_url: str):
        """Create system with SQLAlchemy repository for production."""
        engine = create_engine(database_url)
        # Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db_session = Session()

        repository = CustomerRepository(db_session)
        return {
            'repository': repository,
            'logic': CustomerInfoLogic(repository),
            'management': CustomerManagementLogic(repository)
        }

    @staticmethod
    def create_testing_system():
        """Create system for testing with mock data."""
        repository = InMemoryCustomerRepository()

        # Add test data
        test_customers = [
            CustomerData("1111111111", "Test User 1", "09111111111"),
            CustomerData("2222222222", "Test User 2", "09222222222"),
        ]

        for customer in test_customers:
            repository.create_customer(customer)

        return {
            'repository': repository,
            'logic': CustomerInfoLogic(repository),
            'management': CustomerManagementLogic(repository)
        }


if __name__ == "__main__":
    # Run all examples
    example_validation_scenarios()
    print("\n" + "=" * 50 + "\n")

    example_error_handling()
    print("\n" + "=" * 50 + "\n")

    example_data_import_export()
    print("\n" + "=" * 50 + "\n")

    example_advanced_search()
    print("\n" + "=" * 50 + "\n")

    example_integration_testing()
    print("\n" + "=" * 50 + "\n")

    # Uncomment to run GUI
    app = CustomerInfoApp()
    sys.exit(app.run())
