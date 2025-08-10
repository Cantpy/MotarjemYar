# -*- coding: utf-8 -*-
"""
Data Models and Domain Objects
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re


def _is_valid_iranian_national_id(national_id: str) -> bool:
    """Validate Iranian national ID format."""
    if not national_id or len(national_id) != 10 or not national_id.isdigit():
        return False
    # Check for invalid repeating patterns
    if national_id in [str(i) * 10 for i in range(10)]:
        return False
    # # Calculate checksum
    # check_sum = sum(int(national_id[i]) * (10 - i) for i in range(9))
    # remainder = check_sum % 11
    # check_digit = int(national_id[9])
    # return check_digit == remainder if remainder < 2 else check_digit == 11 - remainder


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
                _is_valid_iranian_national_id(self.national_id.strip()) and  # Use shared function
                self._is_valid_phone(self.phone.strip())
        )

    def get_validation_errors(self) -> List[str]:
        """Get validation errors for customer data."""
        errors = []

        if not self.national_id.strip():
            errors.append("کد ملی الزامی است")
        elif not _is_valid_iranian_national_id(self.national_id.strip()):
            errors.append("کد ملی معتبر نمی‌باشد")

        if not self.name.strip():
            errors.append("نام و نام خانوادگی الزامی است")

        if not self.phone.strip():
            errors.append("شماره تماس الزامی است")
        elif not self._is_valid_phone(self.phone.strip()):
            errors.append("شماره تماس معتبر نمی‌باشد")

        return errors

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
            'ui_number': self.ui_number,  # Include ui_number in dict
            '_ui_number': self.ui_number  # For backward compatibility
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
                    _is_valid_iranian_national_id(self.national_id.strip())  # Use shared function
            )
        return True  # Empty companions are valid

    def get_validation_errors(self, companion_index: int = 0) -> List[str]:
        errors = []
        if self.name or self.national_id:
            if not self.name.strip():
                errors.append(f"نام همراه {companion_index + 1} الزامی است")
            if not self.national_id.strip():
                errors.append(f"کد ملی همراه {companion_index + 1} الزامی است")
            elif not _is_valid_iranian_national_id(self.national_id.strip()):  # Use shared function
                errors.append(f"کد ملی همراه {companion_index + 1} معتبر نمی‌باشد")
        return errors


@dataclass
class CustomerInfoData:
    """Complete customer information including companions."""
    customer: CustomerData = field(default_factory=CustomerData)
    has_companions: bool = False
    companions: List[CompanionData] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerInfoData':
        """Create CustomerInfoData from dictionary."""
        customer_data = CustomerData.from_dict(data)
        has_companions = data.get('has_companions', False)
        companions = [
            CompanionData.from_dict(comp_data)
            for comp_data in data.get('companions', [])
        ]

        return cls(
            customer=customer_data,
            has_companions=has_companions,
            companions=companions
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.customer.to_dict()
        result.update({
            'has_companions': self.has_companions,
            'companions': [comp.to_dict() for comp in self.companions]
        })
        return result

    def is_valid(self) -> bool:
        """Check if all data is valid."""
        if not self.customer.is_valid():
            return False

        if self.has_companions:
            for companion in self.companions:
                if not companion.is_valid():
                    return False

        return True

    def get_validation_errors(self) -> List[str]:
        """Get all validation errors."""
        errors = self.customer.get_validation_errors()

        if self.has_companions:
            for i, companion in enumerate(self.companions):
                errors.extend(companion.get_validation_errors(i))

        return errors

    def get_total_people(self) -> int:
        """Get total number of people (customer + companions)."""
        return 1 + (len(self.companions) if self.has_companions else 0)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the customer information."""
        return {
            'customer_name': self.customer.name,
            'total_people': self.get_total_people(),
            'has_companions': self.has_companions,
            'companions_count': len(self.companions) if self.has_companions else 0
        }

    def export_for_invoice(self) -> Dict[str, Any]:
        """Export data in format suitable for invoice processing."""
        return {
            'customer': self.customer.to_dict(),
            'companions': self.companions if self.has_companions else [],
            'total_people': self.get_total_people()
        }

    def prepare_for_save(self):
        """Prepare companions for database save by setting customer_national_id."""
        for companion in self.companions:
            companion.customer_national_id = self.customer.national_id


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    field_errors: Dict[str, str] = field(default_factory=dict)

    def add_error(self, error: str, field: str = None):
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
        if field:
            self.field_errors[field] = error

    def clear(self):
        """Clear all errors."""
        self.is_valid = True
        self.errors.clear()
        self.field_errors.clear()


@dataclass
class CustomerSearchCriteria:
    """Search criteria for customers."""
    national_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    def has_criteria(self) -> bool:
        """Check if any search criteria is provided."""
        return any([
            self.national_id,
            self.name,
            self.phone,
            self.email
        ])

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values."""
        return {
            k: v for k, v in {
                'national_id': self.national_id,
                'name': self.name,
                'phone': self.phone,
                'email': self.email
            }.items() if v is not None
        }
