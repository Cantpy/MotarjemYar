"""
Validation utilities for form inputs and data validation.
"""
import re


def validate_email(email):
    """
    Validate email format using regex.

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    return pattern.match(email) is not None


def validate_phone_number(phone):
    """
    Validate Iranian phone number format.

    Args:
        phone (str): Phone number to validate

    Returns:
        bool: True if phone format is valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False

    # Remove spaces and common separators
    clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Iranian mobile number patterns
    patterns = [
        r'^09\d{9}$',  # 09xxxxxxxxx
        r'^\+989\d{9}$',  # +989xxxxxxxxx
        r'^989\d{9}$',  # 989xxxxxxxxx
        r'^0\d{10}$',  # Landline: 0xxxxxxxxxx
    ]

    return any(re.match(pattern, clean_phone) for pattern in patterns)


def validate_national_id(national_id):
    """
    Validate Iranian national ID (Melli Code).

    Args:
        national_id (str): National ID to validate

    Returns:
        bool: True if national ID is valid, False otherwise
    """
    if not national_id or not isinstance(national_id, str):
        return False

    # Remove spaces and convert to string
    clean_id = national_id.replace(" ", "").strip()

    # Must be exactly 10 digits
    if not clean_id.isdigit() or len(clean_id) != 10:
        return False

    # Invalid patterns
    invalid_patterns = [
        '0000000000', '1111111111', '2222222222', '3333333333', '4444444444',
        '5555555555', '6666666666', '7777777777', '8888888888', '9999999999'
    ]

    if clean_id in invalid_patterns:
        return False

    # Checksum validation
    check_sum = 0
    for i in range(9):
        check_sum += int(clean_id[i]) * (10 - i)

    remainder = check_sum % 11
    check_digit = int(clean_id[9])

    if remainder < 2:
        return check_digit == remainder
    else:
        return check_digit == 11 - remainder


def validate_required_field(value, field_name="Field"):
    """
    Validate that a required field is not empty.

    Args:
        value (str): Value to validate
        field_name (str): Name of the field for error message

    Returns:
        tuple: (is_valid, error_message)
    """
    if not value or not str(value).strip():
        return False, f"{field_name} is required"
    return True, ""


def validate_numeric_field(value, field_name="Field", min_value=None, max_value=None):
    """
    Validate that a field contains a valid number within optional range.

    Args:
        value (str|int|float): Value to validate
        field_name (str): Name of the field for error message
        min_value (float, optional): Minimum allowed value
        max_value (float, optional): Maximum allowed value

    Returns:
        tuple: (is_valid, error_message, numeric_value)
    """
    try:
        if isinstance(value, str):
            # Remove common separators and convert Persian numerals
            from .number_utils import clean_number_string
            clean_value = clean_number_string(value)
            numeric_value = float(clean_value) if '.' in clean_value else int(clean_value)
        else:
            numeric_value = float(value)

        if min_value is not None and numeric_value < min_value:
            return False, f"{field_name} must be at least {min_value}", None

        if max_value is not None and numeric_value > max_value:
            return False, f"{field_name} must be at most {max_value}", None

        return True, "", numeric_value

    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number", None


def validate_text_length(value, field_name="Field", min_length=None, max_length=None):
    """
    Validate text length within specified range.

    Args:
        value (str): Text to validate
        field_name (str): Name of the field for error message
        min_length (int, optional): Minimum required length
        max_length (int, optional): Maximum allowed length

    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(value, str):
        value = str(value)

    length = len(value.strip())

    if min_length is not None and length < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"

    if max_length is not None and length > max_length:
        return False, f"{field_name} must be at most {max_length} characters long"

    return True, ""
