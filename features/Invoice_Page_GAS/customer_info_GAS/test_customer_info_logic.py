# test_logic.py
import pytest
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import (CustomerLogic,
                                                                             is_valid_iranian_national_id,
                                                                             is_valid_iranian_phone)
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from unittest.mock import MagicMock

# --- Tests for Validators ---


@pytest.mark.parametrize("nid, expected", [
    ("0018215441", True),   # Valid NID
    ("1272659350", True),   # Valid NID
    ("0018215440", False),  # Invalid checksum
    ("1111111111", False),  # Invalid (repeating digits)
    ("12345", False),       # Invalid (wrong length)
    ("abcdefghij", False),  # Invalid (not a digit)
])
def test_iranian_national_id_validator(nid, expected):
    assert is_valid_iranian_national_id(nid) == expected


@pytest.mark.parametrize("phone, expected", [
    ("09123456789", True),
    ("+989351234567", True),
    ("09901112233", True),
    ("9123456789", True),    # Missing leading zero
    ("0912345678", False),   # Too short
    ("1234567890", False),   # Invalid prefix
])
def test_iranian_phone_validator(phone, expected):
    assert is_valid_iranian_phone(phone) == expected


# --- Tests for Logic Class ---

@pytest.fixture
def logic():
    logic_instance = CustomerLogic()
    logic_instance.repository = MagicMock()
    return logic_instance


def test_save_customer_with_invalid_nid_fails(logic):
    """Tests that logic raises a ValueError for an invalid National ID."""
    customer = Customer(name="Test", national_id=12345, phone="09123456789")
    with pytest.raises(ValueError, match="not valid"):
        logic.save_customer(customer)
