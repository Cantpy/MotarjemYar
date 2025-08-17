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
    # 1. Prerequisite check: Must be 10 digits and numeric.
    if not national_id.isdigit() or len(national_id) != 10:
        return False

    # 2. Check for invalid repeating characters.
    if len(set(national_id)) == 1:
        return False

    # 3. Calculate the checksum.
    check_digit = int(national_id[9])
    weighted_sum = sum(int(national_id[i]) * (10 - i) for i in range(9))
    remainder = weighted_sum % 11

    # 4. Compare with the check digit based on the official rules.
    if remainder < 2:
        return check_digit == remainder
    else:
        return check_digit == (11 - remainder)


def validate_legal_national_id(nid: str) -> bool:
    """
    Validates an 11-digit Iranian Legal Entity National ID (شناسه ملی).

    Args:
        nid: The 11-digit national ID as a string.

    Returns:
        True if the ID is valid, False otherwise.
    """
    # 1. Prerequisite check: Must be 11 digits and numeric.
    if not nid.isdigit() or len(nid) != 11:
        return False

    # 2. Get the check digit (the last digit).
    check_digit = int(nid[10])

    # 3. Define the constant weights for the checksum calculation.
    weights = [29, 27, 23, 19, 17, 13, 11, 7, 5, 3]

    # 4. The digit before the check digit (at index 9) is a special coefficient.
    coefficient = int(nid[9]) + 2

    # 5. Calculate the weighted sum.
    weighted_sum = 0
    # Iterate through the first 10 digits and their corresponding weights.
    for i in range(10):
        term = (int(nid[i]) + coefficient) % 10
        weighted_sum += term * weights[i]

    # 6. Calculate the remainder.
    remainder = weighted_sum % 11

    # 7. Determine the expected check digit and compare.
    if remainder == 0:
        return check_digit == 0
    else:
        expected_check_digit = 11 - remainder
        return check_digit == expected_check_digit


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
