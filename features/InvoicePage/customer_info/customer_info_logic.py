# -*- coding: utf-8 -*-
"""
Business Logic Layer - Core business rules and operations
"""
from typing import List, Optional, Dict, Any, Tuple
from features.InvoicePage.customer_info.customer_info_models import (
    CustomerData, CompanionData, CustomerInfoData,
    ValidationResult, CustomerSearchCriteria
)
from features.InvoicePage.customer_info.customer_info_repo import ICustomerRepository


class CustomerInfoLogic:
    """Business logic for customer information management."""

    def __init__(self, customer_repository: ICustomerRepository):
        """Initialize with customer repository."""
        self.customer_repository = customer_repository
        self._current_data = CustomerInfoData()

    def get_current_data(self) -> CustomerInfoData:
        """Get current customer information data."""
        return self._current_data

    def set_customer_data(self, customer_data: CustomerData) -> ValidationResult:
        """Set customer data with validation."""
        result = ValidationResult(is_valid=True)

        # Validate customer data
        if not customer_data.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=customer_data.get_validation_errors()
            )
            return result

        # Check for duplicate national ID (if creating new customer)
        if self.customer_repository.customer_exists(customer_data.national_id):
            # If customer exists, load their complete data including companions
            existing_customer_info = self.customer_repository.get_customer_with_companions(customer_data.national_id)
            if existing_customer_info:
                self._current_data = existing_customer_info
                return result

        # Check for duplicate phone number
        if self.customer_repository.phone_exists(customer_data.phone, customer_data.national_id):
            result.add_error("شماره تماس قبلاً ثبت شده است", "phone")
            return result

        self._current_data.customer = customer_data
        return result

    def update_customer_field(self, field_name: str, value: str) -> ValidationResult:
        """Update a specific customer field."""
        result = ValidationResult(is_valid=True)

        # Update the field
        if hasattr(self._current_data.customer, field_name):
            setattr(self._current_data.customer, field_name, value)
        else:
            result.add_error(f"فیلد نامعتبر: {field_name}")
            return result

        # Validate the updated data
        if not self._current_data.customer.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=self._current_data.customer.get_validation_errors()
            )

        # Additional business rules
        if field_name == "phone" and value.strip():
            if self.customer_repository.phone_exists(value.strip(), self._current_data.customer.national_id):
                result.add_error("شماره تماس قبلاً ثبت شده است", "phone")

        return result

    def set_companions_status(self, has_companions: bool) -> None:
        """Set companions status."""
        self._current_data.has_companions = has_companions
        if not has_companions:
            self._current_data.companions.clear()

    def add_companion(self, name: str = "", national_id: str = "") -> Tuple[int, ValidationResult]:
        """Add a new companion and return its index and validation result."""
        result = ValidationResult(is_valid=True)

        # UI number will be set by the controller to maintain sequential numbering
        companion = CompanionData(
            name=name,
            national_id=national_id,
            customer_national_id=self._current_data.customer.national_id,
            ui_number=0  # Will be set by controller
        )

        # Validate companion data
        if not companion.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=companion.get_validation_errors(len(self._current_data.companions))
            )

        # Check for duplicate national ID if provided
        if companion.national_id.strip():
            # Check if national ID is already used by a customer
            if self.customer_repository.customer_exists(companion.national_id.strip()):
                result.add_error("کد ملی همراه قبلاً به عنوان مشتری ثبت شده است")

            # Check if national ID is already used by another companion
            if self.customer_repository.companion_national_id_exists(companion.national_id.strip()):
                result.add_error("کد ملی همراه قبلاً ثبت شده است")

            # Check against other companions in current session
            for existing_companion in self._current_data.companions:
                if existing_companion.national_id == companion.national_id.strip():
                    result.add_error("کد ملی همراه تکراری است")
                    break

        self._current_data.companions.append(companion)
        return len(self._current_data.companions) - 1, result

    def remove_companion(self, index: int) -> bool:
        """Remove companion by index."""
        if 0 <= index < len(self._current_data.companions):
            self._current_data.companions.pop(index)
            return True
        return False

    def update_companion(self, index: int, name: str, national_id: str, phone: str = "") -> ValidationResult:
        """Update companion data."""
        result = ValidationResult(is_valid=True)

        if not (0 <= index < len(self._current_data.companions)):
            result.add_error("همراه مورد نظر یافت نشد")
            return result

        companion = self._current_data.companions[index]
        old_national_id = companion.national_id

        companion.name = name
        companion.national_id = national_id
        companion.customer_national_id = self._current_data.customer.national_id

        # Validate companion data
        if not companion.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=companion.get_validation_errors(index)
            )

        # Check for duplicate national ID if changed
        if companion.national_id.strip() and companion.national_id != old_national_id:
            # Check if national ID is already used by a customer
            if self.customer_repository.customer_exists(companion.national_id.strip()):
                result.add_error(f"کد ملی همراه {index + 1} قبلاً به عنوان مشتری ثبت شده است")

            # Check if national ID is already used by another companion (excluding current one)
            exclude_id = companion.id if companion.id else None
            if self.customer_repository.companion_national_id_exists(companion.national_id.strip(), exclude_id):
                result.add_error(f"کد ملی همراه {index + 1} قبلاً ثبت شده است")

            # Check against other companions in current session
            for i, existing_companion in enumerate(self._current_data.companions):
                if i != index and existing_companion.national_id == companion.national_id.strip():
                    result.add_error(f"کد ملی همراه {index + 1} تکراری است")
                    break

        return result

    def validate_all_data(self) -> ValidationResult:
        """Validate all customer information data."""
        result = ValidationResult(is_valid=True)

        # Validate customer data
        if not self._current_data.customer.is_valid():
            result.errors.extend(self._current_data.customer.get_validation_errors())
            result.is_valid = False

        # Validate companions if any
        if self._current_data.has_companions:
            for i, companion in enumerate(self._current_data.companions):
                if not companion.is_valid():
                    result.errors.extend(companion.get_validation_errors(i))
                    result.is_valid = False

        return result

    def clear_all_data(self) -> None:
        """Clear all customer information data."""
        self._current_data = CustomerInfoData()

    def load_customer_by_national_id(self, national_id: str) -> ValidationResult:
        """Load existing customer with companions by national ID."""
        result = ValidationResult(is_valid=True)

        customer_info = self.customer_repository.get_customer_with_companions(national_id)
        if not customer_info:
            result.add_error("مشتری با این کد ملی یافت نشد")
            return result

        self._current_data = customer_info

        # Assign UI numbers for companions (will be renumbered by controller)
        for i, companion in enumerate(self._current_data.companions):
            if companion.ui_number <= 0:
                companion.ui_number = i + 1

        return result

    def search_customers(self, criteria: CustomerSearchCriteria) -> List[CustomerData]:
        """Search for customers based on criteria."""
        if not criteria.has_criteria():
            return []

        return self.customer_repository.search_customers(criteria)

    def save_customer(self) -> ValidationResult:
        """Save customer with companions to repository."""
        result = self.validate_all_data()
        if not result.is_valid:
            return result

        # Use the new method that handles both customer and companions
        if not self.customer_repository.save_customer_with_companions(self._current_data):
            result.add_error("خطا در ثبت اطلاعات مشتری و همراهان")

        return result

    def delete_current_customer(self) -> ValidationResult:
        """Delete current customer from repository (companions will be deleted automatically)."""
        result = ValidationResult(is_valid=True)

        if not self._current_data.customer.national_id:
            result.add_error("هیچ مشتری برای حذف انتخاب نشده است")
            return result

        if not self.customer_repository.delete_customer(self._current_data.customer.national_id):
            result.add_error("خطا در حذف مشتری")
            return result

        # Clear data after successful deletion
        self.clear_all_data()
        return result

    def get_export_data(self) -> Dict[str, Any]:
        """Get data formatted for export (e.g., to invoice)."""
        return self._current_data.export_for_invoice()

    def import_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Import customer data from external source."""
        result = ValidationResult(is_valid=True)

        try:
            imported_data = CustomerInfoData.from_dict(data)

            # Validate imported data
            if not imported_data.is_valid():
                result = ValidationResult(
                    is_valid=False,
                    errors=imported_data.get_validation_errors()
                )
                return result

            # Ensure companions have the correct customer_national_id
            for companion in imported_data.companions:
                companion.customer_national_id = imported_data.customer.national_id

            self._current_data = imported_data

        except Exception as e:
            result.add_error(f"خطا در وارد کردن داده‌ها: {str(e)}")

        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current customer information."""
        return self._current_data.get_summary()

    def get_companion_by_ui_number(self, ui_number: int) -> Optional[CompanionData]:
        """Get companion by UI number."""
        for companion in self._current_data.companions:
            if companion.ui_number == ui_number:
                return companion
        return None

    def get_companion_index_by_ui_number(self, ui_number: int) -> Optional[int]:
        """Get companion index by UI number."""
        for i, companion in enumerate(self._current_data.companions):
            if companion.ui_number == ui_number:
                return i
        return None

    def update_companion_by_ui_number(self, ui_number: int, field_name: str, value: str) -> ValidationResult:
        """Update companion field by UI number."""
        result = ValidationResult(is_valid=True)

        companion = self.get_companion_by_ui_number(ui_number)
        if not companion:
            result.add_error("همراه مورد نظر یافت نشد")
            return result

        old_value = getattr(companion, field_name, "")

        # Update the field
        if hasattr(companion, field_name):
            setattr(companion, field_name, value)
            # Ensure customer_national_id is always set
            companion.customer_national_id = self._current_data.customer.national_id
        else:
            result.add_error(f"فیلد نامعتبر: {field_name}")
            return result

        # Get index for validation
        index = self.get_companion_index_by_ui_number(ui_number)
        if index is not None:
            # Validate companion data
            if not companion.is_valid():
                result = ValidationResult(
                    is_valid=False,
                    errors=companion.get_validation_errors(index)
                )

            # Check for duplicate national ID if updated
            if field_name == "national_id" and companion.national_id.strip() and companion.national_id != old_value:
                # Check if national ID is already used by a customer
                if self.customer_repository.customer_exists(companion.national_id.strip()):
                    result.add_error("کد ملی همراه قبلاً به عنوان مشتری ثبت شده است")

                # Check if national ID is already used by another companion
                exclude_id = companion.id if companion.id else None
                if self.customer_repository.companion_national_id_exists(companion.national_id.strip(), exclude_id):
                    result.add_error("کد ملی همراه قبلاً ثبت شده است")

                # Check against other companions in current session
                for other_companion in self._current_data.companions:
                    if (other_companion.ui_number != ui_number and
                            other_companion.national_id == companion.national_id.strip()):
                        result.add_error("کد ملی همراه تکراری است")
                        break

        return result

    def is_data_modified(self) -> bool:
        """Check if current data has been modified."""
        return (
                bool(self._current_data.customer.national_id) or
                bool(self._current_data.customer.name) or
                bool(self._current_data.customer.phone) or
                bool(self._current_data.companions)
        )

    def can_proceed_to_next_step(self) -> Tuple[bool, List[str]]:
        """Check if data is valid enough to proceed to next step."""
        validation_result = self.validate_all_data()
        return validation_result.is_valid, validation_result.errors

    def refresh_companions_from_database(self) -> ValidationResult:
        """Refresh companions data from database for current customer."""
        result = ValidationResult(is_valid=True)

        if not self._current_data.customer.national_id:
            result.add_error("هیچ مشتری بارگذاری نشده است")
            return result

        customer_info = self.customer_repository.get_customer_with_companions(
            self._current_data.customer.national_id
        )

        if customer_info:
            self._current_data.companions = customer_info.companions
            self._current_data.has_companions = customer_info.has_companions

            # Assign UI numbers for companions (will be renumbered by controller)
            for i, companion in enumerate(self._current_data.companions):
                if companion.ui_number <= 0:
                    companion.ui_number = i + 1
        else:
            result.add_error("خطا در بارگذاری اطلاعات همراهان")

        return result


class CustomerManagementLogic:
    """Business logic for customer management operations."""

    def __init__(self, customer_repository: ICustomerRepository):
        """Initialize with customer repository."""
        self.customer_repository = customer_repository

    def get_all_customers(self, limit: int = 100) -> List[CustomerData]:
        """Get all customers with limit."""
        return self.customer_repository.get_all_customers(limit)

    def search_customers(self, search_term: str) -> List[CustomerData]:
        """Search customers by term (searches in name, national_id, phone)."""
        # Custom search logic - search in multiple fields
        all_results = []

        # Search by name
        name_criteria = CustomerSearchCriteria(name=search_term)
        all_results.extend(self.customer_repository.search_customers(name_criteria))

        # Search by national ID
        if search_term.isdigit():
            id_criteria = CustomerSearchCriteria(national_id=search_term)
            all_results.extend(self.customer_repository.search_customers(id_criteria))

        # Search by phone
        phone_criteria = CustomerSearchCriteria(phone=search_term)
        all_results.extend(self.customer_repository.search_customers(phone_criteria))

        # Remove duplicates based on national_id
        unique_results = {}
        for customer in all_results:
            unique_results[customer.national_id] = customer

        return list(unique_results.values())

    def create_customer_with_companions(self, customer_info: CustomerInfoData) -> ValidationResult:
        """Create a new customer with companions."""
        result = ValidationResult(is_valid=True)

        # Validate customer data
        if not customer_info.customer.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=customer_info.customer.get_validation_errors()
            )
            return result

        # Validate companions if any
        if customer_info.has_companions:
            for i, companion in enumerate(customer_info.companions):
                if not companion.is_valid():
                    result.errors.extend(companion.get_validation_errors(i))
                    result.is_valid = False

        if not result.is_valid:
            return result

        # Check for duplicate customer national ID
        if self.customer_repository.customer_exists(customer_info.customer.national_id):
            result.add_error("مشتری با این کد ملی قبلاً ثبت شده است")
            return result

        # Check for duplicate customer phone
        if self.customer_repository.phone_exists(customer_info.customer.phone):
            result.add_error("شماره تماس قبلاً ثبت شده است")
            return result

        # Check for duplicate companion national IDs
        if customer_info.has_companions:
            for companion in customer_info.companions:
                if companion.national_id.strip():
                    if self.customer_repository.customer_exists(companion.national_id):
                        result.add_error(f"کد ملی همراه '{companion.name}' قبلاً به عنوان مشتری ثبت شده است")
                    if self.customer_repository.companion_national_id_exists(companion.national_id):
                        result.add_error(f"کد ملی همراه '{companion.name}' قبلاً ثبت شده است")

        if not result.is_valid:
            return result

        # Save customer with companions
        if not self.customer_repository.save_customer_with_companions(customer_info):
            result.add_error("خطا در ثبت مشتری و همراهان")

        return result

    def create_customer(self, customer_data: CustomerData) -> ValidationResult:
        """Create a new customer with business rules validation."""
        result = ValidationResult(is_valid=True)

        # Validate customer data
        if not customer_data.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=customer_data.get_validation_errors()
            )
            return result

        # Check for duplicate national ID
        if self.customer_repository.customer_exists(customer_data.national_id):
            result.add_error("مشتری با این کد ملی قبلاً ثبت شده است")
            return result

        # Check for duplicate phone
        if self.customer_repository.phone_exists(customer_data.phone):
            result.add_error("شماره تماس قبلاً ثبت شده است")
            return result

        # Create customer
        if not self.customer_repository.create_customer(customer_data):
            result.add_error("خطا در ثبت مشتری")

        return result

    def update_customer_with_companions(self, customer_info: CustomerInfoData) -> ValidationResult:
        """Update existing customer with companions."""
        result = ValidationResult(is_valid=True)

        # Validate customer data
        if not customer_info.customer.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=customer_info.customer.get_validation_errors()
            )
            return result

        # Validate companions if any
        if customer_info.has_companions:
            for i, companion in enumerate(customer_info.companions):
                if not companion.is_valid():
                    result.errors.extend(companion.get_validation_errors(i))
                    result.is_valid = False

        if not result.is_valid:
            return result

        # Check if customer exists
        if not self.customer_repository.customer_exists(customer_info.customer.national_id):
            result.add_error("مشتری یافت نشد")
            return result

        # Check for duplicate phone (excluding current customer)
        if self.customer_repository.phone_exists(customer_info.customer.phone, customer_info.customer.national_id):
            result.add_error("شماره تماس قبلاً ثبت شده است")
            return result

        # Check for duplicate companion national IDs
        if customer_info.has_companions:
            for companion in customer_info.companions:
                if companion.national_id.strip():
                    # Check against customers (excluding current customer)
                    if (companion.national_id != customer_info.customer.national_id and
                            self.customer_repository.customer_exists(companion.national_id)):
                        result.add_error(f"کد ملی همراه '{companion.name}' قبلاً به عنوان مشتری ثبت شده است")

                    # Check against other companions (excluding current companion if it has an ID)
                    exclude_id = companion.id if companion.id else None
                    if self.customer_repository.companion_national_id_exists(companion.national_id, exclude_id):
                        result.add_error(f"کد ملی همراه '{companion.name}' قبلاً ثبت شده است")

        if not result.is_valid:
            return result

        # Update customer with companions
        if not self.customer_repository.save_customer_with_companions(customer_info):
            result.add_error("خطا در به‌روزرسانی مشتری و همراهان")

        return result

    def update_customer(self, customer_data: CustomerData) -> ValidationResult:
        """Update existing customer."""
        result = ValidationResult(is_valid=True)

        # Validate customer data
        if not customer_data.is_valid():
            result = ValidationResult(
                is_valid=False,
                errors=customer_data.get_validation_errors()
            )
            return result

        # Check if customer exists
        if not self.customer_repository.customer_exists(customer_data.national_id):
            result.add_error("مشتری یافت نشد")
            return result

        # Check for duplicate phone (excluding current customer)
        if self.customer_repository.phone_exists(customer_data.phone, customer_data.national_id):
            result.add_error("شماره تماس قبلاً ثبت شده است")
            return result

        # Update customer
        if not self.customer_repository.update_customer(customer_data):
            result.add_error("خطا در به‌روزرسانی مشتری")

        return result

    def delete_customer(self, national_id: str) -> ValidationResult:
        """Delete customer with business rules validation (companions will be deleted automatically)."""
        result = ValidationResult(is_valid=True)

        if not national_id.strip():
            result.add_error("کد ملی الزامی است")
            return result

        # Check if customer exists
        if not self.customer_repository.customer_exists(national_id):
            result.add_error("مشتری یافت نشد")
            return result

        # TODO: Check if customer has active invoices before deletion
        # This would require additional repository methods

        # Delete customer (companions will be deleted automatically via CASCADE)
        if not self.customer_repository.delete_customer(national_id):
            result.add_error("خطا در حذف مشتری")

        return result

    def get_customer_statistics(self) -> Dict[str, Any]:
        """Get customer statistics."""
        total_customers = self.customer_repository.get_customer_count()

        return {
            'total_customers': total_customers,
            'customers_with_email': 0,  # Would need additional repository methods
            'customers_with_address': 0,  # Would need additional repository methods
        }

    def get_customer_with_companions(self, national_id: str) -> Optional[CustomerInfoData]:
        """Get customer with all their companions."""
        return self.customer_repository.get_customer_with_companions(national_id)
