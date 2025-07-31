# -*- coding: utf-8 -*-
"""
Customer Information Backend - Data handling and validation
"""


class CustomerInfoBackend:
    """Backend class for customer information handling."""

    def __init__(self):
        self.data = {
            'national_id': '',
            'full_name': '',
            'phone': '',
            'address': '',
            'has_companions': False,
            'companions': []
        }
        self.validation_errors = []

    def get_data(self):
        """Get customer data."""
        return self.data.copy()

    def set_data(self, data):
        """Set customer data."""
        self.data.update(data)
        self.validate_data()

    def update_field(self, field_name, value):
        """Update a specific field."""
        if field_name in self.data:
            self.data[field_name] = value
            self.validate_data()

    def add_companion(self, name='', national_id=''):
        """Add a companion."""
        companion = {
            'name': name,
            'national_id': national_id
        }
        self.data['companions'].append(companion)
        self.validate_data()

    def remove_companion(self, index):
        """Remove a companion by index."""
        if 0 <= index < len(self.data['companions']):
            self.data['companions'].pop(index)
            self.validate_data()

    def update_companion(self, index, name, national_id):
        """Update companion data."""
        if 0 <= index < len(self.data['companions']):
            self.data['companions'][index] = {
                'name': name,
                'national_id': national_id
            }
            self.validate_data()

    def set_companions_status(self, has_companions):
        """Set companions status."""
        self.data['has_companions'] = has_companions
        if not has_companions:
            self.data['companions'] = []
        self.validate_data()

    def clear_all_data(self):
        """Clear all data."""
        self.data = {
            'national_id': '',
            'full_name': '',
            'phone': '',
            'address': '',
            'has_companions': False,
            'companions': []
        }
        self.validation_errors = []

    def validate_data(self):
        """Validate all data and update errors list."""
        self.validation_errors = []

        # Check required fields
        if not self.data['national_id'].strip():
            self.validation_errors.append("کد ملی الزامی است")
        elif not self._is_valid_national_id(self.data['national_id'].strip()):
            self.validation_errors.append("کد ملی معتبر نمی‌باشد")

        if not self.data['full_name'].strip():
            self.validation_errors.append("نام و نام خانوادگی الزامی است")

        if not self.data['phone'].strip():
            self.validation_errors.append("شماره تماس الزامی است")
        elif not self._is_valid_phone(self.data['phone'].strip()):
            self.validation_errors.append("شماره تماس معتبر نمی‌باشد")

        # Check companions
        if self.data['has_companions']:
            for i, companion in enumerate(self.data['companions']):
                name = companion.get('name', '').strip()
                national_id = companion.get('national_id', '').strip()

                if name or national_id:
                    if not name:
                        self.validation_errors.append(f"نام همراه {i + 1} الزامی است")
                    if not national_id:
                        self.validation_errors.append(f"کد ملی همراه {i + 1} الزامی است")
                    elif not self._is_valid_national_id(national_id):
                        self.validation_errors.append(f"کد ملی همراه {i + 1} معتبر نمی‌باشد")

        return len(self.validation_errors) == 0

    def is_valid(self):
        """Check if current data is valid."""
        return len(self.validation_errors) == 0

    def get_validation_errors(self):
        """Get list of validation errors."""
        return self.validation_errors.copy()

    def _is_valid_national_id(self, national_id):
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

    def _is_valid_phone(self, phone):
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

    def export_data(self):
        """Export customer data for external use."""
        return {
            'customer': {
                'national_id': self.data['national_id'],
                'full_name': self.data['full_name'],
                'phone': self.data['phone'],
                'address': self.data['address']
            },
            'companions': self.data['companions'] if self.data['has_companions'] else [],
            'total_people': 1 + len(self.data['companions']) if self.data['has_companions'] else 1
        }

    def import_data(self, data):
        """Import customer data from external source."""
        try:
            customer_data = {
                'national_id': data.get('customer', {}).get('national_id', ''),
                'full_name': data.get('customer', {}).get('full_name', ''),
                'phone': data.get('customer', {}).get('phone', ''),
                'address': data.get('customer', {}).get('address', ''),
                'has_companions': bool(data.get('companions', [])),
                'companions': data.get('companions', [])
            }
            self.set_data(customer_data)
            return True
        except Exception as e:
            print(f"Error importing data: {e}")
            return False

    def get_summary(self):
        """Get a summary of the customer information."""
        return {
            'customer_name': self.data['full_name'],
            'total_people': 1 + len(self.data['companions']) if self.data['has_companions'] else 1,
            'has_companions': self.data['has_companions'],
            'companions_count': len(self.data['companions']) if self.data['has_companions'] else 0
        }
