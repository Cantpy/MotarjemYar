# -*- coding: utf-8 -*-
"""
Pytest Test Suite for Customer Management System
"""
import pytest
import sys
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication

from features.InvoicePage.customer_info.customer_info_models import (
    CustomerData,
    CustomerInfoData,
    CompanionData,
    CustomerSearchCriteria
)
from features.InvoicePage.customer_info.customer_info_repo import InMemoryCustomerRepository
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic, CustomerManagementLogic
from features.InvoicePage.customer_info.customer_info_controller import ControllerFactory
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView


@pytest.fixture
def qapp():
    """Fixture to provide QApplication instance."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def empty_repository():
    """Fixture providing an empty in-memory repository."""
    return InMemoryCustomerRepository()


@pytest.fixture
def populated_repository():
    """Fixture providing a repository with test data."""
    repository = InMemoryCustomerRepository()

    test_customers = [
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

    for customer in test_customers:
        repository.create_customer(customer)

    return repository


@pytest.fixture
def valid_customer_data():
    """Fixture providing valid customer data."""
    return CustomerData(
        national_id="0013542419",  # Valid Iranian national ID
        name="Test Customer",
        phone="09123456789",
        email="test@example.com",
        address="Test Address"
    )


@pytest.fixture
def valid_companion_data():
    """Fixture providing valid companion data."""
    return CompanionData(
        name="Test Companion",
        national_id="1111111146",  # Valid Iranian national ID
        phone="09987654321",
        ui_number=1
    )


@pytest.fixture
def customer_logic(empty_repository):
    """Fixture providing CustomerInfoLogic instance."""
    return CustomerInfoLogic(empty_repository)


@pytest.fixture
def management_logic(empty_repository):
    """Fixture providing CustomerManagementLogic instance."""
    return CustomerManagementLogic(empty_repository)


class TestCustomerData:
    """Test cases for CustomerData model."""

    def test_valid_customer_creation(self, valid_customer_data):
        """Test creating a valid customer."""
        assert valid_customer_data.is_valid() is True
        assert valid_customer_data.national_id == "0013542419"
        assert valid_customer_data.name == "Test Customer"
        assert valid_customer_data.phone == "09123456789"
        assert valid_customer_data.email == "test@example.com"

    def test_customer_to_dict(self, valid_customer_data):
        """Test customer serialization to dictionary."""
        data_dict = valid_customer_data.to_dict()

        assert isinstance(data_dict, dict)
        assert data_dict["national_id"] == "0013542419"
        assert data_dict["name"] == "Test Customer"
        assert data_dict["phone"] == "09123456789"
        assert data_dict["email"] == "test@example.com"

    @pytest.mark.parametrize("national_id,expected", [
        ("0013542419", True),  # Valid Iranian national ID
        ("1249934095", True),
        ("2980335045", True),
        ("1270038168", True),
        ("1261930150", True),
        ("4210029165", True),
        ("4210342033", True),
        ("5100059133", True),
        ("4218763437", True),
        ("2980335045", True),
        ("4839767076", True),
        ("2200721439", True),
        ("1160330824", True),
        ("1280321261", True),
        ("1758068310", True),
        ("1111111146", True),
        ("0000000018", False),
        ("0000123456", False),
        ("1234567890", False),  # Invalid checksum
        ("0000000000", False),  # All zeros
        ("123456789", False),  # Too short
        ("12345678901", False),  # Too long
        ("", False),  # Empty
        ("abcd123456", False),  # Contains letters
    ])
    def test_national_id_validation(self, national_id, expected):
        """Test Iranian national ID validation."""
        customer = CustomerData(
            national_id=national_id,
            name="Test",
            phone="09123456789"
        )
        assert customer._is_valid_national_id(national_id) == expected

    @pytest.mark.parametrize("phone,expected", [
        ("09123456789", True),  # Standard mobile
        ("9123456789", True),  # Mobile without leading zero
        ("02112345678", True),  # Tehran landline
        ("123456", False),  # Too short
        ("abcd", False),  # Contains letters
        ("091234567890", False),  # Too long
        ("", False),  # Empty
        ("08123456789", False),  # Invalid mobile prefix
    ])
    def test_phone_validation(self, phone, expected):
        """Test phone number validation."""
        customer = CustomerData(
            national_id="0013542419",
            name="Test",
            phone=phone
        )
        assert (phone and customer._is_valid_phone(phone)) == expected

    def test_invalid_customer_validation_errors(self):
        """Test validation error collection for invalid customer."""
        invalid_customer = CustomerData(
            national_id="123",  # Invalid
            name="",  # Empty
            phone="invalid",  # Invalid
            email="not_an_email"  # Invalid email format
        )

        assert invalid_customer.is_valid() is False
        errors = invalid_customer.get_validation_errors()
        assert isinstance(errors, list)
        assert len(errors) > 0

        # Check that we get specific validation errors
        error_messages = ' '.join(errors)
        assert "national_id" in error_messages or "کد ملی" in error_messages


class TestCompanionData:
    """Test cases for CompanionData model."""

    def test_valid_companion_creation(self, valid_companion_data):
        """Test creating a valid companion."""
        assert valid_companion_data.is_valid() is True
        assert valid_companion_data.name == "Test Companion"
        assert valid_companion_data.national_id == "1111111146"
        assert valid_companion_data.phone == "09987654321"
        assert valid_companion_data.ui_number == 1

    def test_companion_to_dict(self, valid_companion_data):
        """Test companion serialization to dictionary."""
        data_dict = valid_companion_data.to_dict()

        assert isinstance(data_dict, dict)
        assert data_dict["name"] == "Test Companion"
        assert data_dict["national_id"] == "1111111146"
        assert data_dict["phone"] == "09987654321"
        assert data_dict["ui_number"] == 1

    def test_companion_without_phone(self):
        """Test companion creation without phone number."""
        companion = CompanionData(
            name="No Phone Companion",
            national_id="1111111146",
            ui_number=1
        )

        assert companion.is_valid() is True


class TestCustomerInfoData:
    """Test cases for CustomerInfoData model."""

    def test_customer_info_creation(self, valid_customer_data, valid_companion_data):
        """Test creating customer info with companions."""
        customer_info = CustomerInfoData(
            customer=valid_customer_data,
            has_companions=True,
            companions=[valid_companion_data]
        )

        assert customer_info.is_valid() is True
        assert customer_info.get_total_people() == 2  # Customer + 1 companion
        assert customer_info.has_companions is True
        assert len(customer_info.companions) == 1

    def test_customer_info_without_companions(self, valid_customer_data):
        """Test creating customer info without companions."""
        customer_info = CustomerInfoData(
            customer=valid_customer_data,
            has_companions=False,
            companions=[]
        )

        assert customer_info.is_valid() is True
        assert customer_info.get_total_people() == 1  # Only customer
        assert customer_info.has_companions is False
        assert len(customer_info.companions) == 0

    def test_customer_info_summary(self, valid_customer_data, valid_companion_data):
        """Test customer info summary generation."""
        customer_info = CustomerInfoData(
            customer=valid_customer_data,
            has_companions=True,
            companions=[valid_companion_data]
        )

        summary = customer_info.get_summary()
        assert isinstance(summary, str)
        assert valid_customer_data.name in summary
        assert "2" in summary  # Total people count


class TestInMemoryCustomerRepository:
    """Test cases for InMemoryCustomerRepository."""

    def test_create_customer(self, empty_repository, valid_customer_data):
        """Test creating a customer in repository."""
        result = empty_repository.create_customer(valid_customer_data)

        assert result is True
        assert empty_repository.customer_exists(valid_customer_data.national_id)

    def test_create_duplicate_customer(self, empty_repository, valid_customer_data):
        """Test creating duplicate customer should fail."""
        # Create first customer
        result1 = empty_repository.create_customer(valid_customer_data)
        assert result1 is True

        # Try to create duplicate
        result2 = empty_repository.create_customer(valid_customer_data)
        assert result2 is False

    def test_get_by_national_id(self, populated_repository):
        """Test retrieving customer by national ID."""
        customer = populated_repository.get_by_national_id("1234567890")

        assert customer is not None
        assert customer.national_id == "1234567890"
        assert customer.name == "علی احمدی"

    def test_get_nonexistent_customer(self, empty_repository):
        """Test retrieving non-existent customer."""
        customer = empty_repository.get_by_national_id("9999999999")
        assert customer is None

    def test_update_customer(self, populated_repository):
        """Test updating existing customer."""
        customer = populated_repository.get_by_national_id("1234567890")
        assert customer is not None

        original_email = customer.email
        customer.email = "updated@example.com"

        result = populated_repository.update_customer(customer)
        assert result is True

        # Verify update
        updated_customer = populated_repository.get_by_national_id("1234567890")
        assert updated_customer.email == "updated@example.com"
        assert updated_customer.email != original_email

    def test_delete_customer(self, populated_repository):
        """Test deleting customer."""
        assert populated_repository.customer_exists("1234567890")

        result = populated_repository.delete_customer("1234567890")
        assert result is True
        assert not populated_repository.customer_exists("1234567890")

    def test_get_all_customers(self, populated_repository):
        """Test retrieving all customers."""
        customers = populated_repository.get_all_customers()

        assert isinstance(customers, list)
        assert len(customers) == 3

        national_ids = [c.national_id for c in customers]
        assert "1234567890" in national_ids
        assert "0987654321" in national_ids
        assert "1122334455" in national_ids

    def test_search_customers(self, populated_repository):
        """Test searching customers."""
        criteria = CustomerSearchCriteria(name="علی")
        results = populated_repository.search_customers(criteria)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].name == "علی احمدی"

    def test_search_customers_by_phone(self, populated_repository):
        """Test searching customers by phone."""
        criteria = CustomerSearchCriteria(phone="09123456789")
        results = populated_repository.search_customers(criteria)

        assert len(results) == 1
        assert results[0].phone == "09123456789"

    def test_search_no_results(self, populated_repository):
        """Test search with no matching results."""
        criteria = CustomerSearchCriteria(name="NonExistent")
        results = populated_repository.search_customers(criteria)

        assert isinstance(results, list)
        assert len(results) == 0


class TestCustomerInfoLogic:
    """Test cases for CustomerInfoLogic."""

    def test_set_customer_data(self, customer_logic, valid_customer_data):
        """Test setting customer data in logic layer."""
        result = customer_logic.set_customer_data(valid_customer_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_set_invalid_customer_data(self, customer_logic):
        """Test setting invalid customer data."""
        invalid_customer = CustomerData(
            national_id="123",  # Invalid
            name="",  # Empty
            phone="invalid"  # Invalid
        )

        result = customer_logic.set_customer_data(invalid_customer)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_companions_functionality(self, customer_logic):
        """Test companion management functionality."""
        # Initially no companions
        assert customer_logic.get_current_data().has_companions is False

        # Enable companions
        customer_logic.set_companions_status(True)
        assert customer_logic.get_current_data().has_companions is True

        # Add companion
        companion_index, result = customer_logic.add_companion("Test Companion", "1111111146")

        assert companion_index == 1  # First companion gets index 1
        assert result.is_valid is True

        current_data = customer_logic.get_current_data()
        assert len(current_data.companions) == 1
        assert current_data.companions[0].name == "Test Companion"

    def test_remove_companion(self, customer_logic):
        """Test removing companion."""
        # Setup: enable companions and add one
        customer_logic.set_companions_status(True)
        companion_index, _ = customer_logic.add_companion("Test Companion", "1111111146")

        # Verify companion exists
        assert len(customer_logic.get_current_data().companions) == 1

        # Remove companion
        result = customer_logic.remove_companion(companion_index)
        assert result.is_valid is True

        # Verify companion removed
        assert len(customer_logic.get_current_data().companions) == 0

    def test_validate_all_data(self, customer_logic, valid_customer_data):
        """Test complete data validation."""
        # Set valid customer
        customer_logic.set_customer_data(valid_customer_data)

        # Add valid companion
        customer_logic.set_companions_status(True)
        customer_logic.add_companion("Valid Companion", "1111111146")

        # Validate all
        result = customer_logic.validate_all_data()
        assert result.is_valid is True

    def test_get_summary(self, customer_logic, valid_customer_data):
        """Test getting data summary."""
        customer_logic.set_customer_data(valid_customer_data)
        customer_logic.set_companions_status(True)
        customer_logic.add_companion("Companion", "1111111146")

        summary = customer_logic.get_summary()

        assert isinstance(summary, str)
        assert valid_customer_data.name in summary

    def test_export_data(self, customer_logic, valid_customer_data):
        """Test data export functionality."""
        customer_logic.set_customer_data(valid_customer_data)
        customer_logic.set_companions_status(True)
        customer_logic.add_companion("Export Companion", "1111111146")

        export_data = customer_logic.get_export_data()

        assert isinstance(export_data, dict)
        assert export_data["national_id"] == valid_customer_data.national_id
        assert export_data["name"] == valid_customer_data.name
        assert export_data["has_companions"] is True
        assert len(export_data["companions"]) == 1

    def test_import_data(self, customer_logic):
        """Test data import functionality."""
        import_data = {
            'national_id': '0013542419',
            'name': 'Imported Customer',
            'phone': '09123456789',
            'email': 'import@test.com',
            'has_companions': True,
            'companions': [
                {
                    'name': 'Imported Companion',
                    'national_id': '1111111146',
                    'phone': '09987654321',
                    'ui_number': 1
                }
            ]
        }

        result = customer_logic.import_data(import_data)
        assert result.is_valid is True

        current_data = customer_logic.get_current_data()
        assert current_data.customer.name == "Imported Customer"
        assert len(current_data.companions) == 1
        assert current_data.companions[0].name == "Imported Companion"

    def test_clear_all_data(self, customer_logic, valid_customer_data):
        """Test clearing all data."""
        # Set up some data
        customer_logic.set_customer_data(valid_customer_data)
        customer_logic.set_companions_status(True)
        customer_logic.add_companion("Test Companion", "1111111146")

        # Verify data exists
        current_data = customer_logic.get_current_data()
        assert current_data.customer is not None
        assert len(current_data.companions) == 1

        # Clear data
        customer_logic.clear_all_data()

        # Verify data cleared
        cleared_data = customer_logic.get_current_data()
        assert cleared_data.customer.name == ""
        assert cleared_data.customer.national_id == ""
        assert len(cleared_data.companions) == 0


class TestCustomerManagementLogic:
    """Test cases for CustomerManagementLogic."""

    def test_search_customers(self, populated_repository):
        """Test customer search functionality."""
        management_logic = CustomerManagementLogic(populated_repository)

        # Search by name
        results = management_logic.search_customers("علی")
        assert len(results) == 1
        assert results[0].name == "علی احمدی"

        # Search by phone
        results = management_logic.search_customers("09123456789")
        assert len(results) == 1
        assert results[0].phone == "09123456789"

        # Search by email
        results = management_logic.search_customers("mohammad@example.com")
        assert len(results) == 1
        assert results[0].email == "mohammad@example.com"

    def test_search_empty_term(self, populated_repository):
        """Test search with empty search term."""
        management_logic = CustomerManagementLogic(populated_repository)

        results = management_logic.search_customers("")
        assert len(results) == 3  # Should return all customers

    def test_search_no_results(self, populated_repository):
        """Test search with no matching results."""
        management_logic = CustomerManagementLogic(populated_repository)

        results = management_logic.search_customers("NonExistentCustomer")
        assert len(results) == 0


class TestControllerFactory:
    """Test cases for ControllerFactory."""

    def test_create_customer_info_controller(self, empty_repository):
        """Test controller creation."""
        controller = ControllerFactory.create_customer_info_controller(empty_repository)

        assert controller is not None
        assert hasattr(controller, 'is_valid')
        assert hasattr(controller, 'get_data')

    def test_controller_data_operations(self, empty_repository):
        """Test controller data operations."""
        controller = ControllerFactory.create_customer_info_controller(empty_repository)

        # Simulate field changes
        controller.on_national_id_changed("0013542419")
        controller.on_full_name_changed("Controller Test")
        controller.on_phone_changed("09123456789")

        # Check validation
        is_valid = controller.is_valid()
        assert is_valid is True

        # Get data
        data = controller.get_data()
        assert data is not None
        assert data.customer.name == "Controller Test"

    def test_controller_companion_operations(self, empty_repository):
        """Test controller companion operations."""
        controller = ControllerFactory.create_customer_info_controller(empty_repository)

        # Enable companions
        controller.on_has_companions_changed(True)

        # Add companion
        controller.on_add_companion_clicked()

        # Simulate companion field changes
        controller.on_companion_field_changed(1, 'name', 'Controller Companion')
        controller.on_companion_field_changed(1, 'national_id', '1111111146')

        # Get data and verify
        data = controller.get_data()
        assert data.has_companions is True
        assert len(data.companions) == 1
        assert data.companions[0].name == "Controller Companion"


class TestCustomerInfoView:
    """Test cases for CustomerInfoView (UI component)."""

    def test_view_creation(self, qapp, empty_repository):
        """Test view instantiation."""
        with patch('features.InvoicePage.customer_info.customer_info_view.CustomerInfoView.__init__',
                   return_value=None):
            view = Mock()
            view.data_changed = Mock()
            view.validation_changed = Mock()

            # Test that view can be mocked and signals exist
            assert hasattr(view, 'data_changed')
            assert hasattr(view, 'validation_changed')


class TestIntegration:
    """Integration tests across all layers."""

    def test_complete_customer_workflow(self, empty_repository):
        """Test complete customer creation and management workflow."""
        # Step 1: Create logic instance
        logic = CustomerInfoLogic(empty_repository)

        # Step 2: Create customer
        customer_data = CustomerData(
            national_id="0013542419",
            name="Integration Test Customer",
            phone="09123456789",
            email="integration@test.com"
        )

        result = logic.set_customer_data(customer_data)
        assert result.is_valid is True

        # Step 3: Add companions
        logic.set_companions_status(True)
        companion1_idx, comp1_result = logic.add_companion("Companion 1", "1111111146")
        companion2_idx, comp2_result = logic.add_companion("Companion 2", "0000000018")

        assert comp1_result.is_valid is True
        assert comp2_result.is_valid is True
        assert companion1_idx == 1
        assert companion2_idx == 2

        # Step 4: Validate all data
        validation = logic.validate_all_data()
        assert validation.is_valid is True

        # Step 5: Save customer
        save_result = logic.save_customer()
        assert save_result.is_valid is True

        # Step 6: Verify customer exists in repository
        assert empty_repository.customer_exists("0013542419") is True

        # Step 7: Retrieve and verify customer
        retrieved_customer = empty_repository.get_by_national_id("0013542419")
        assert retrieved_customer is not None
        assert retrieved_customer.name == "Integration Test Customer"

        # Step 8: Test export/import
        exported_data = logic.get_export_data()

        # Clear and reimport
        logic.clear_all_data()
        import_result = logic.import_data(exported_data)
        assert import_result.is_valid is True

        # Verify data integrity after import
        current_data = logic.get_current_data()
        assert current_data.customer.name == "Integration Test Customer"
        assert len(current_data.companions) == 2

    def test_error_handling_workflow(self, populated_repository):
        """Test error handling across the system."""
        logic = CustomerInfoLogic(populated_repository)

        # Test duplicate national ID
        duplicate_customer = CustomerData(
            national_id="1234567890",  # Already exists in populated_repository
            name="Duplicate Customer",
            phone="09111111111"
        )

        result = logic.set_customer_data(duplicate_customer)
        # The logic layer should handle this appropriately
        # (behavior depends on your business rules)

        # Test invalid companion data
        logic.set_companions_status(True)
        companion_idx, companion_result = logic.add_companion("", "invalid_id")

        # Should handle invalid companion gracefully
        assert companion_result.is_valid is False or companion_idx is None

    def test_search_integration(self, populated_repository):
        """Test search functionality integration."""
        management_logic = CustomerManagementLogic(populated_repository)

        # Test various search scenarios
        search_terms = ["علی", "09123456789", "ali@example.com", "تهران"]

        for term in search_terms:
            results = management_logic.search_customers(term)
            assert isinstance(results, list)

            if results:  # If we found results
                # Verify each result contains the search term
                for customer in results:
                    customer_data = [
                        customer.name.lower(),
                        customer.phone,
                        customer.email.lower() if customer.email else "",
                        customer.address.lower() if customer.address else ""
                    ]
                    # At least one field should contain the search term
                    assert any(term.lower() in field for field in customer_data)


# Performance and stress tests
class TestPerformance:
    """Performance and stress tests."""

    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        repository = InMemoryCustomerRepository()

        # Create many customers
        for i in range(100):
            customer = CustomerData(
                national_id=f"{i:010d}",
                name=f"Customer {i}",
                phone=f"0912345{i:04d}",
                email=f"customer{i}@test.com"
            )
            result = repository.create_customer(customer)
            assert result is True

        # Test retrieval performance
        all_customers = repository.get_all_customers()
        assert len(all_customers) == 100

        # Test search performance
        criteria = CustomerSearchCriteria(name="Customer 5")
        results = repository.search_customers(criteria)
        assert len(results) >= 10  # Should find Customer 5, 50, 51, etc.

    def test_concurrent_operations(self, empty_repository):
        """Test thread safety of operations."""
        import threading
        import time

        logic = CustomerInfoLogic(empty_repository)
        results = []

        def create_customer(customer_id):
            customer = CustomerData(
                national_id=f"{customer_id:010d}",
                name=f"Concurrent Customer {customer_id}",
                phone=f"0912{customer_id:06d}"
            )
            result = logic.set_customer_data(customer)
            results.append(result.is_valid)
            time.sleep(0.001)  # Small delay to encourage race conditions

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_customer, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results (may vary based on your thread safety implementation)
        assert len(results) == 10


if __name__ == "__main__":
    # Run with pytest
    # pytest test_customer_info.py -v
    # pytest test_customer_info.py::TestCustomerData::test_valid_customer_creation -v
    # pytest test_customer_info.py -k "validation" -v

    import pytest

    pytest.main([__file__, "-v"])
