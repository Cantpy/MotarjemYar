from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class CustomerData:
    """CustomerModel data model."""
    national_id: str = ""
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    telegram_id: str = ""
    passport_image: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerData':
        """Create CustomerData from dictionary."""
        return cls(
            national_id=data.get('national_id', ''),
            name=data.get('name', '') or data.get('full_name', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', ''),
            telegram_id=data.get('telegram_id', ''),
            passport_image=data.get('passport_image', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'national_id': self.national_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'telegram_id': self.telegram_id,
            'passport_image': self.passport_image
        }

    def is_valid(self) -> bool:
        """Check if customer data is valid."""
        return (
                bool(self.national_id.strip()) and
                bool(self.name.strip()) and
                bool(self.phone.strip()) and
                self._is_valid_national_id(self.national_id.strip()) and
                self._is_valid_phone(self.phone.strip())
        )

    def get_validation_errors(self) -> List[str]:
        """Get validation errors for customer data."""
        errors = []

        if not self.national_id.strip():
            errors.append("کد ملی الزامی است")
        elif not self._is_valid_national_id(self.national_id.strip()):
            errors.append("کد ملی معتبر نمی‌باشد")

        if not self.name.strip():
            errors.append("نام و نام خانوادگی الزامی است")

        if not self.phone.strip():
            errors.append("شماره تماس الزامی است")
        elif not self._is_valid_phone(self.phone.strip()):
            errors.append("شماره تماس معتبر نمی‌باشد")

        return errors

    def _is_valid_national_id(self, national_id: str) -> bool:
        """Validate Iranian national ID format."""
        if not national_id or len(national_id) != 10:
            return False

        if not national_id.isdigit():
            return False

        # Check for invalid patterns
        if national_id in ['0000000000', '1111111111', '2222222222', '3333333333',
                           '4444444444', '5555555555', '6666666666', '7777777777',
                           '8888888888', '9999999999']:
            return False

        # Calculate checksum
        check_sum = 0
        for i in range(9):
            check_sum += int(national_id[i]) * (10 - i)

        remainder = check_sum % 11
        check_digit = int(national_id[9])

        if remainder < 2:
            return check_digit == remainder
        else:
            return check_digit == 11 - remainder

    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False

        # Remove spaces, dashes, and parentheses
        cleaned_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Check if it's all digits
        if not cleaned_phone.isdigit():
            return False

        # Check length (Iranian phone numbers)
        if len(cleaned_phone) == 11 and cleaned_phone.startswith('09'):
            return True
        elif len(cleaned_phone) == 10 and cleaned_phone.startswith('9'):
            return True
        elif len(cleaned_phone) in [8, 11]:  # Landline numbers
            return True

        return False


@dataclass
class CompanionData:
    """CompanionModel data model - now represents a separate entity in database."""
    id: Optional[int] = None
    name: str = ""
    national_id: str = ""
    customer_national_id: str = ""
    ui_number: int = 0  # For UI ordering/display purposes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'name': self.name,
            'national_id': self.national_id,
            'customer_national_id': self.customer_national_id,
            'ui_number': self.ui_number,
            '_ui_number': self.ui_number
        }
        if self.id is not None:
            result['id'] = self.id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanionData':
        """Create CompanionData from dictionary."""
        ui_number = data.get('ui_number', 0) or data.get('_ui_number', 0)
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            national_id=data.get('national_id', ''),
            customer_national_id=data.get('customer_national_id', ''),
            ui_number=ui_number
        )

    def is_valid(self) -> bool:
        """Check if companion data is valid."""
        if self.name or self.national_id:
            return (
                    bool(self.name.strip()) and
                    bool(self.national_id.strip()) and
                    self._is_valid_national_id(self.national_id.strip())
            )
        return True

    def get_validation_errors(self, companion_index: int = 0) -> List[str]:
        """Get validation errors for companion data."""
        errors = []

        if self.name or self.national_id:
            if not self.name.strip():
                errors.append(f"نام همراه {companion_index + 1} الزامی است")
            if not self.national_id.strip():
                errors.append(f"کد ملی همراه {companion_index + 1} الزامی است")
            elif not self._is_valid_national_id(self.national_id.strip()):
                errors.append(f"کد ملی همراه {companion_index + 1} معتبر نمی‌باشد")

        return errors

    def _is_valid_national_id(self, national_id: str) -> bool:
        """Validate Iranian national ID format."""
        if not national_id or len(national_id) != 10:
            return False

        if not national_id.isdigit():
            return False

        # Check for invalid patterns
        if national_id in ['0000000000', '1111111111', '2222222222', '3333333333',
                           '4444444444', '5555555555', '6666666666', '7777777777',
                           '8888888888', '9999999999']:
            return False

        # Calculate checksum
        check_sum = 0
        for i in range(9):
            check_sum += int(national_id[i]) * (10 - i)

        remainder = check_sum % 11
        check_digit = int(national_id[9])

        if remainder < 2:
            return check_digit == remainder
        else:
            return check_digit == 11 - remainder


@dataclass
class CustomerDisplayData:
    """Data model for displaying customer information in the table."""
    national_id: str
    name: str
    phone: str
    email: str
    address: str
    telegram_id: str
    invoice_count: int = 0
    companions: List[CompanionData] = None

    def __post_init__(self):
        if self.companions is None:
            self.companions = []
