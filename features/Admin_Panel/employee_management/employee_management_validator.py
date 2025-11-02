# features/Admin_Panel/employee_management/employee_management_validator.py

import re
from datetime import date
from dateutil.relativedelta import relativedelta

"""
Validation utilities for employee data.
"""


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format using regex."""
    if not email:
        return True, ""  # Email is optional

    if not isinstance(email, str):
        return False, "فرمت ایمیل نامعتبر است"

    pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if pattern.match(email):
        return True, ""
    return False, "فرمت ایمیل نامعتبر است"


def validate_phone_number(phone: str) -> tuple[bool, str]:
    """Validate Iranian phone number format."""
    if not phone or not isinstance(phone, str):
        return False, "شماره تلفن الزامی است"

    # Remove spaces and common separators
    clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Standardized patterns for landline or mobile
    patterns = [
        r'^09\d{9}$',  # Mobile: 09xxxxxxxxx
        r'^0\d{10}$',  # Landline: 0xxxxxxxxxx
    ]

    if any(re.match(pattern, clean_phone) for pattern in patterns):
        return True, ""
    return False, "فرمت شماره تلفن نامعتبر است (مثال: 09123456789)"


def validate_national_id(national_id: str) -> tuple[bool, str]:
    """Validate Iranian national ID (Melli Code)."""
    if not national_id or not isinstance(national_id, str):
        return False, "کد ملی الزامی است"

    # 1. Prerequisite check: Must be 10 digits and numeric.
    if not national_id.isdigit() or len(national_id) != 10:
        return False, "کد ملی باید 10 رقم باشد"

    # 2. Check for invalid repeating characters.
    if len(set(national_id)) == 1:
        return False, "کد ملی نامعتبر است"

    # 3. Calculate the checksum.
    check_digit = int(national_id[9])
    weighted_sum = sum(int(national_id[i]) * (10 - i) for i in range(9))
    remainder = weighted_sum % 11

    # 4. Compare with the check digit based on the official rules.
    if (remainder < 2 and check_digit == remainder) or \
       (remainder >= 2 and check_digit == 11 - remainder):
        return True, ""
    return False, "کد ملی نامعتبر است (خطا در رقم کنترل)"


def validate_required_field(value: str, field_name: str) -> tuple[bool, str]:
    """Validate that a required field is not empty."""
    if not value or not str(value).strip():
        return False, f"{field_name} الزامی است"
    return True, ""


def validate_text_length(value: str, field_name: str, min_length: int) -> tuple[bool, str]:
    """Validate minimum text length."""
    if not isinstance(value, str):
        value = str(value)

    if len(value.strip()) < min_length:
        return False, f"{field_name} باید حداقل {min_length} کاراکتر باشد"
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format and length."""
    is_valid, error = validate_required_field(username, "نام کاربری")
    if not is_valid:
        return False, error

    is_valid, error = validate_text_length(username, "نام کاربری", 3)
    if not is_valid:
        return False, error

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "نام کاربری فقط می‌تواند شامل حروف انگلیسی، اعداد و _ باشد"
    return True, ""


def validate_password(password: str, is_edit: bool = False) -> tuple[bool, str]:
    """Validate password complexity."""
    # In edit mode, an empty password means no change is requested.
    if is_edit and not password:
        return True, ""

    is_valid, error = validate_required_field(password, "رمز عبور")
    if not is_valid:
        return False, error

    if len(password) < 6:
        return False, "رمز عبور باید حداقل 6 کاراکتر باشد"
    if not re.search(r'[0-9]', password):
        return False, "رمز عبور باید حداقل یک عدد داشته باشد"
    if not re.search(r'[a-zA-Z]', password):
        return False, "رمز عبور باید حداقل یک حرف داشته باشد"
    return True, ""


def validate_hire_date(hire_date: date) -> tuple[bool, str]:
    """
    MODIFIED: Validate hire date is not more than one month in the future.
    """
    if not hire_date:
        return False, "تاریخ استخدام نامعتبر است"

    # Calculate the limit date (today + 1 month)
    limit_date = date.today() + relativedelta(months=1)

    if hire_date > limit_date:
        return False, "تاریخ استخدام نمی‌تواند بیش از یک ماه در آینده باشد"
    return True, ""


def validate_birth_date(birth_date: date) -> tuple[bool, str]:
    """Validate birth date and employee age."""
    if not birth_date:
        return True, ""  # Date of birth is optional

    if birth_date > date.today():
        return False, "تاریخ تولد نمی‌تواند در آینده باشد"

    age = date.today().year - birth_date.year
    if age < 18:
        return False, "سن کارمند باید حداقل 18 سال باشد"
    if age > 80:
        return False, "تاریخ تولد نامعتبر است"
    return True, ""
