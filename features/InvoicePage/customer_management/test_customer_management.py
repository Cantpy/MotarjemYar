"""
Pytest test suite for Customer Management System.

This module contains comprehensive tests for the customer management system,
covering models, repository, logic, and integration scenarios.

Run tests with:
    pytest test_customer_management.py -v
    pytest test_customer_management.py::TestCustomerData::test_validation -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

# Import the modules to test
from features.InvoicePage.customer_management.customer_managemnet_models import (CustomerData, CompanionData,
                                                                                 CustomerDisplayData)
from features.InvoicePage.customer_management.customer_management_logic import CustomerLogic
from features.InvoicePage.customer_management.customer_management_repo import CustomerRepository


class TestCustomerData:
    """Test cases for CustomerData model."""

    def test_customer_data_creation(self):
        """Test creating customer data object."""
        customer = CustomerData(
            national_id="1234567890",
            name="علی احمدی",
            phone="09123456789",
            email="ali@example.com",
            address="تهران، خیابان ولیعصر",
            telegram_id="@ali_ahmadi"
        )

        assert customer.national_id == "1234567890"
        assert customer.name == "علی احمدی"
        assert customer.phone == "09123456789"
        assert customer.email == "ali@example.com"

    def test_customer_data_from_dict(self):
        """Test creating customer data from dictionary."""
        data = {
            'national_id': '1234567890',
            'name': 'علی احمدی',
            'phone': '09123456789',
            'email': 'ali@example.com',
            'address': 'تهران',
            'telegram_id': '@ali',
            'passport_image': 'path/to/image.jpg'
        }

        customer = CustomerData.from_dict(data)
        assert customer.national_id == '1234567890'
        assert customer.name == 'علی احمدی'
        assert customer.phone == '09123456789'

    def test_customer_data_to_dict(self):
        """Test converting customer data to dictionary."""
        customer = CustomerData(
            national_id="1234567890",
            name="علی احمدی",
            phone="09123456789"
        )

        result = customer.to_dict()
        assert result['national_id'] == "1234567890"
        assert result['name'] == "علی احمدی"
        assert result['phone'] == "09123456789"

    def test_national_id_validation(self):
        """Test Iranian national ID validation."""
        customer = CustomerData()

        # Valid national IDs
        assert customer._is_valid_national_id("0013542419")
        assert customer._is_valid_national_id("0074559648")

        # Invalid national IDs
        assert not customer._is_valid_national_id("")
        assert not customer._is_valid_national_id("123")
        assert not customer._is_valid_national_id("1234567890a")
        assert not customer._is_valid_national_id("0000000000")
        assert not customer._is_valid_national_id("1111111111")
        assert not customer._is_valid_national_id("1234567891")  # Wrong checksum

    def test_phone_validation(self):
        """Test phone number validation."""
        customer = CustomerData()

        # Valid phone numbers
        assert customer._is_valid_phone("09123456789")
        assert customer._is_valid_phone("9123456789")
        assert customer._is_valid_phone("02112345678")
        assert customer._is_valid_phone("021-1234-5678")
        assert customer._is_valid_phone("(021) 1234-5678")

        # Invalid phone numbers
        assert not customer._is_valid_phone("")
        assert not customer._is_valid_phone("123")
        assert not customer._is_valid_phone("09abc123456")
        assert not customer._is_valid_phone("0812345")

    def test_customer_validation(self):
        """Test customer data validation."""
        # Valid customer
        customer = CustomerData(
            national_id="0013542419",
            name="علی احمدی",
            phone="09123456789"
        )
        assert customer.is_valid()
        assert len(customer.get_validation_errors()) == 0

        # Invalid customer - missing required fields
        customer = CustomerData()
        assert not customer.is_valid()
        errors = customer.get_validation_errors()
        assert "کد ملی الزامی است" in errors
        assert "نام و نام خانوادگی الزامی است" in errors
        assert "شماره تماس الزامی است" in errors

        # Invalid customer - bad national ID
        customer = CustomerData(
            national_id="1234567890",  # Invalid checksum
            name="علی احمدی",
            phone="09123456789"
        )
        assert not customer.is_valid()
        errors = customer.get_validation_errors()
        assert "کد ملی معتبر نمی‌باشد" in errors


class TestCompanionData:
    """Test cases for CompanionData model."""

    def test_companion_data_creation(self):
        """Test creating companion data object."""
        companion = CompanionData(
            id=1,
            name="مریم احمدی",
            national_id="0074559648",
            customer_national_id="0013542419",
            ui_number=1
        )

        assert companion.id == 1
        assert companion.name == "مریم احمدی"
        assert companion.national_id == "0074559648"
        assert companion.customer_national_id == "0013542419"
        assert companion.ui_number == 1

    def test_companion_validation(self):
        """Test companion data validation."""
        # Empty companion (valid)
        companion = CompanionData()
        assert companion.is_valid()

        # Valid companion with data
        companion = CompanionData(
            name="مریم احمدی",
            national_id="0074559648"
        )
        assert companion.is_valid()

        # Invalid - name without national_id
        companion = CompanionData(name="مریم احمدی")
        assert not companion.is_valid()

        # Invalid - bad national_id
        companion = CompanionData(
            name="مریم احمدی",
            national_id="1234567890"  # Invalid checksum
        )
        assert not companion.is_valid()

    def test_companion_validation_errors(self):
        """Test companion validation error messages."""
        companion = CompanionData(name="مریم")  # Missing national_id
        errors = companion.get_validation_errors(0)
        assert "کد ملی همراه 1 الزامی است" in errors

        companion = CompanionData(
            name="مریم",
            national_id="invalid"
        )
        errors = companion.get_validation_errors(1)  # Second companion
        assert "کد ملی همراه 2 معتبر نمی‌باشد" in errors


class TestCustomerDisplayData:
    """Test cases for CustomerDisplayData model."""

    def test_customer_display_data_creation(self):
        """Test creating customer display data."""
        companions = [
            CompanionData(name="مریم", national_id="0074559648"),
            CompanionData(name="احمد", national_id="0013542419")
        ]

        display_data = CustomerDisplayData(
            national_id="1234567890",
            name="علی احمدی",
            phone="09123456789",
            email="ali@example.com",
            address="تهران",
            telegram_id="@ali",
            invoice_count=5,
            companions=companions
        )

        assert display_data.national_id == "1234567890"
        assert display_data.invoice_count == 5
        assert len(display_data.companions) == 2
        assert display_data.companions[0].name == "مریم"


class TestCustomerLogic:
    """Test cases for CustomerLogic business logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        return Mock(spec=CustomerRepository)

    @pytest.fixture
    def customer_logic(self, mock_repository):
        """Create CustomerLogic instance with mock repository."""
        return CustomerLogic(mock_repository)

    def test_create_customer_success(self, customer_logic, mock_repository):
        """Test successful customer creation."""
        # Setup
        customer_data = CustomerData(
            national_id="0013542419",
            name="علی احمدی",
            phone="09123456789"
        )
        mock_repository.get_customer_by_national_id.return_value = None
        mock_repository.create_customer.return_value = True

        # Execute
        success, errors = customer_logic.create_customer(customer_data)

        # Assert
        assert success
        assert len(errors) == 0
        mock_repository.create_customer.assert_called_once_with(customer_data)

    def test_create_customer_validation_failure(self, customer_logic, mock_repository):
        """Test customer creation with validation errors."""
        # Setup - invalid customer data
        customer_data = CustomerData()  # Empty data

        # Execute
        success, errors = customer_logic.create_customer(customer_data)

        # Assert
        assert not success
        assert len(errors) > 0
        assert "کد ملی الزامی است" in errors
        mock_repository.create_customer.assert_not_called()

    def test_create_customer_duplicate_national_id(self, customer_logic, mock_repository):
        """Test customer creation with duplicate national ID."""
        # Setup
        customer_data = CustomerData(
            national_id="0013542419",
            name="علی احمدی",
            phone="09123456789"
        )
        existing_customer = CustomerData(national_id="0013542419", name="Existing")
        mock_repository.get_customer_by_national_id.return_value = existing_customer

        # Execute
        success, errors = customer_logic.create_customer(customer_data)

        # Assert
        assert not success
        assert "مشتری با این کد ملی قبلاً ثبت شده است" in errors
        mock_repository.create_customer.assert_not_called()

    def test_delete_customer_with_active_invoices(self, customer_logic, mock_repository):
        """Test customer deletion when they have active invoices."""
        # Setup
        national_id = "0013542419"
        customer = CustomerData(national_id=national_id, name="علی احمدی")
        mock_repository.get_customer_by_national_id.return_value = customer
        mock_repository.check_customer_has_active_invoices.return_value = (True, 3)

        # Execute
        success, errors, has_active_invoices, active_count = customer_logic.delete_customer(national_id)

        # Assert
        assert not success
        assert has_active_invoices
        assert active_count == 3
        assert len(errors) == 0  # No errors, just warning about active invoices
        mock_repository.delete_customer.assert_not_called()

    def test_delete_customer_success(self, customer_logic, mock_repository):
        """Test successful customer deletion."""
        # Setup
        national_id = "0013542419"
        customer = CustomerData(national_id=national_id, name="علی احمدی")
        mock_repository.get_customer_by_national_id.return_value = customer
        mock_repository.check_customer_has_active_invoices.return_value = (False, 0)
        mock_repository.delete_customer.return_value = True

        # Execute
        success, errors, has_active_invoices, active_count = customer_logic.delete_customer(national_id)

        # Assert
        assert success
        assert not has_active_invoices
        assert active_count == 0
        assert len(errors) == 0
        mock_repository.delete_customer.assert_called_once_with(national_id)

    def test_force_delete_customer(self, customer_logic, mock_repository):
        """Test force deletion of customer."""
        # Setup
        national_id = "0013542419"
        customer = CustomerData(national_id=national_id, name="علی احمدی")
        mock_repository.get_customer_by_national_id.return_value = customer
        mock_repository.delete_customer.return_value = True

        # Execute
        success, errors = customer_logic.force_delete_customer(national_id)

        # Assert
        assert success
        assert len(errors) == 0
        mock_repository.delete_customer.assert_called_once_with(national_id)

    def test_search_customers_and_companions(self, customer_logic, mock_repository):
        """Test searching customers and companions."""
        # Setup
        search_term = "علی"
        expected_results = [
            CustomerDisplayData(
                national_id="0013542419",
                name="علی احمدی",
                phone="09123456789",
                email="",
                address="",
                telegram_id="",
                invoice_count=2,
                companions=[]
            )
        ]
        mock_repository.search_customers_and_companions.return_value = expected_results

        # Execute
        results = customer_logic.search_customers_and_companions(search_term)

        # Assert
        assert len(results) == 1
        assert results[0].name == "علی احمدی"
        mock_repository.search_customers_and_companions.assert_called_once_with(search_term)

    def test_get_customer_summary(self, customer_logic):
        """Test customer summary formatting."""
        # Setup
        companions = [
            CompanionData(name="مریم احمدی", national_id="0074559648"),
            CompanionData(name="احمد احمدی", national_id="0013542419")
        ]
        customer = CustomerDisplayData(
            national_id="1234567890",
            name="علی احمدی",
            phone="09123456789",
            email="ali@example.com",
            address="تهران",
            telegram_id="@ali",
            invoice_count=5,
            companions=companions
        )

        # Execute
        summary = customer_logic.get_customer_summary(customer)

        # Assert
        assert "نام: علی احمدی" in summary
        assert "کد ملی: 1234567890" in summary
        assert "تعداد فاکتورها: 5" in summary
        assert "همراهان (2):" in summary
        assert "1. مریم احمدی (0074559648)" in summary
        assert "2. احمد احمدی (0013542419)" in summary


class TestCustomerRepository:
    """Test cases for CustomerRepository data access."""

    @pytest.fixture
    def mock_session_factory(self):
        """Create a mock session factory."""
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        return mock_session_factory, mock_session

    @pytest.fixture
    def customer_repository(self, mock_session_factory):
        """Create CustomerRepository with mock session factory."""
        session_factory, _ = mock_session_factory
        return CustomerRepository(session_factory)

    def test_check_customer_has_active_invoices(self, customer_repository, mock_session_factory):
        """Test checking for active invoices."""
        # Setup
        _, mock_session = mock_session_factory
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3  # 3 active invoices

        # Execute
        has_active, count = customer_repository.check_customer_has_active_invoices("1234567890")

        # Assert
        assert has_active
        assert count == 3

    def test_search_empty_term(self, customer_repository):
        """Test search with empty term returns all customers."""
        with patch.object(customer_repository, 'get_all_customers_with_details') as mock_get_all:
            mock_get_all.return_value = []

            # Execute
            results = customer_repository.search_customers_and_companions("")

            # Assert
            mock_get_all.assert_called_once()


class TestIntegration:
    """Integration tests for the customer management system."""

    def test_customer_lifecycle(self):
        """Test complete customer lifecycle: create, update, delete."""
        # This would be an integration test that tests the full workflow
        # In a real scenario, this would use a test database
        pass

    def test_search_functionality(self):
        """Test search functionality across customers and companions."""
        # This would test the search functionality end-to-end
        pass


# Test fixtures and utilities
@pytest.fixture
def sample_customer_data():
    """Provide sample customer data for tests."""
    return CustomerData(
        national_id="0013542419",
        name="علی احمدی",
        phone="09123456789",
        email="ali@example.com",
        address="تهران، خیابان ولیعصر",
        telegram_id="@ali_ahmadi",
        passport_image="path/to/passport.jpg"
    )


@pytest.fixture
def sample_companion_data():
    """Provide sample companion data for tests."""
    return CompanionData(
        id=1,
        name="مریم احمدی",
        national_id="0074559648",
        customer_national_id="0013542419",
        ui_number=1
    )


@pytest.fixture
def sample_display_data():
    """Provide sample customer display data for tests."""
    return CustomerDisplayData(
        national_id="0013542419",
        name="علی احمدی",
        phone="09123456789",
        email="ali@example.com",
        address="تهران",
        telegram_id="@ali_ahmadi",
        invoice_count=5,
        companions=[
            CompanionData(name="مریم احمدی", national_id="0074559648"),
            CompanionData(name="احمد احمدی", national_id="0013542419")
        ]
    )


# Performance and edge case tests
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_long_customer_name(self):
        """Test handling of very long customer names."""
        long_name = "نام بسیار طولانی " * 50  # Very long name
        customer = CustomerData(
            national_id="0013542419",
            name=long_name,
            phone="09123456789"
        )
        assert customer.is_valid()  # Should still be valid

    def test_special_characters_in_phone(self):
        """Test phone validation with various special characters."""
        customer = CustomerData()

        # Test various formats
        assert customer._is_valid_phone("021-1234-5678")
        assert customer._is_valid_phone("(021) 1234 5678")
        assert customer._is_valid_phone("021.1234.5678")
        assert not customer._is_valid_phone("021#1234#5678")

    def test_unicode_handling(self):
        """Test proper Unicode handling for Persian text."""
        customer = CustomerData(
            national_id="0013542419",
            name="علی احمدی پور",  # Persian with complex characters
            phone="09123456789"
        )

        dict_data = customer.to_dict()
        restored_customer = CustomerData.from_dict(dict_data)

        assert restored_customer.name == customer.name
        assert restored_customer.is_valid()


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
