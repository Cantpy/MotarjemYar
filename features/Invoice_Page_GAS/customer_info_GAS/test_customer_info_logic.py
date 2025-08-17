# test_logic.py
import pytest
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import CustomerLogic, CustomerExistsError
from shared.utils.validation_utils import (validate_legal_national_id, validate_national_id, validate_email,
                                           validate_phone_number)
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from unittest.mock import MagicMock


# --- Tests for Validators ---
@pytest.mark.parametrize("nid, expected", [
    ("0082374147", True),
    ("4610192446", True),
    ("4622532891", True),
    ("4210342033", True),
    ("4610322749", True),
    ("4218763437", True),
    ("5100059133", True),
    ("4610348977", True),
    ("4610192446", True),
    ("1818572117", True),
    ("4610329794", True),
    ("1160103070", True),
    ("4610121891", True),
    ("4610348977", True),
    ("1271813130", True),
    ("1288915985", True),
    ("1289125139", True),
    ("3255814235", True),
    ("1270480480", True),
    ("1270846272", True),
    ("1130044602", True),
    ("1160054320", True),
    ("1160114757", True),
    ("1160153809", True),
    ("1160326614", True),
    ("1284993442", True),
    ("1285511921", True),
    ("1292227001", True),
    ("1284993442", True),
    ("1285511921", True),
    ("1292227001", True),
    ("0079124121", False),  # The one that failed your test (Correctly invalid)
    ("0018215441", False),  # Invalid checksum
    ("1111111111", False),  # Invalid (repeating digits)
    ("12345", False),  # Invalid (wrong length)
    ("abcdefghij", False),  # Invalid (not a digit)
])
def test_iranian_national_id_validator(nid, expected):
    """Tests the 10-digit real person National ID validator."""
    assert validate_national_id(nid) == expected


# --- NEW: Test for the 11-digit Legal Entity ID ---
@pytest.mark.parametrize("nid, expected", [
    ("14008425983", True),
    ("10100111117", True),
    ("14005531030", True),
    ("14012772033", True),
    ("14006237431", True),
    ("14012042322", True),
    ("14010520356", True),
    ("10260607934", True),
    ("14008425984", False),
    ("1234567890", False),
    ("123456789012", False),
    ("abcdefghijk", False),
])
def test_iranian_legal_national_id_validator(nid, expected):
    """Tests the 11-digit legal entity National ID validator."""
    assert validate_legal_national_id(nid) == expected


@pytest.mark.parametrize("phone, expected", [
    ("09123456789", True),
    ("+989351234567", True),
    ("09901112233", True),
    ("9123456789", True),  # Missing leading zero
    ("0912345678", False),  # Too short
    ("1234567890", False),  # Invalid prefix
])
def test_iranian_phone_validator(phone, expected):
    """Tests the phone number validator."""
    assert validate_phone_number(phone) == expected


# ----------------------------------------------------------------------
# Tests for CustomerInfoLogic Class
# ----------------------------------------------------------------------

@pytest.fixture
def logic():
    """Creates a CustomerInfoLogic instance with a mocked repository for each test."""
    logic_instance = CustomerLogic()
    # Mock the repository to isolate the logic for testing
    logic_instance._repo = MagicMock()
    return logic_instance


def test_save_customer_with_valid_real_nid_succeeds(logic):
    """Tests that a new customer with a valid 10-digit NID is saved correctly."""
    raw_data = {"name": "تست حقیقی", "national_id": "0018215441", "phone": "09123456789"}

    # Configure the mock to say the customer does not exist
    logic._repo.get_customer.return_value = None

    logic.save_customer(raw_data)

    # Check that the repository's add_customer method was called once
    logic._repo.add_customer.assert_called_once()


def test_save_customer_with_valid_legal_nid_succeeds(logic):
    """Tests that a new customer with a valid 11-digit NID is saved correctly."""
    raw_data = {"name": "شرکت تست حقوقی", "national_id": "14008425983", "phone": "09123456789"}

    # Configure the mock to say the customer does not exist
    logic._repo.get_customer.return_value = None

    logic.save_customer(raw_data)

    # Check that the repository's add_customer method was called once
    logic._repo.add_customer.assert_called_once()


def test_save_customer_with_invalid_nid_fails(logic):
    """Tests that logic raises a ValueError for a structurally invalid National ID."""
    # Using a string now, as per the current architecture
    raw_data = {"name": "تست نامعتبر", "national_id": "12345", "phone": "09123456789"}

    with pytest.raises(ValueError):
        logic.save_customer(raw_data)


def test_save_existing_customer_raises_custom_error(logic):
    """Tests that saving a customer with an existing NID raises CustomerExistsError."""
    raw_data = {"name": "مشتری تکراری", "national_id": "0018215441", "phone": "09123456789"}

    # Configure the mock to return an existing customer, simulating that it was found
    logic._repo.get_customer.return_value = Customer(**raw_data)

    with pytest.raises(CustomerExistsError):
        logic.save_customer(raw_data)


def test_update_customer_calls_repo(logic):
    """Tests that the update_customer method calls the repository's add method."""
    customer_to_update = Customer(name="مشتری آپدیت شده", national_id="0018215441", phone="09111111111")

    logic.update_customer(customer_to_update)

    # The add_customer method in the repo uses merge(), so it handles updates.
    logic._repo.add_customer.assert_called_once_with(customer_to_update)
