# -*- coding: utf-8 -*-
"""
Controller Layer - PySide6 Controller for UI coordination and business logic integration
"""
from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, Optional

from features.InvoicePage.customer_info.customer_info_models import (CustomerData, CompanionData, CustomerInfoData,
                                                                     CustomerSearchCriteria)
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic, CustomerManagementLogic
from features.InvoicePage.customer_info.customer_info_repo import ICustomerRepository


class CustomerInfoController(QObject):
    """Controller class for customer information UI and business logic coordination."""

    # Signals for UI updates
    data_changed = Signal(dict)
    validation_changed = Signal(bool)
    companions_visibility_changed = Signal(bool)
    companions_count_changed = Signal(int)
    field_validation_changed = Signal(str, bool)  # field_name, is_valid
    error_occurred = Signal(str)  # error_message
    customer_loaded = Signal(dict)  # customer_data
    customer_saved = Signal()
    customer_deleted = Signal()

    def __init__(self, customer_repository: ICustomerRepository, parent=None):
        """Initialize controller with repository and optional parent."""
        super().__init__(parent)
        self.customer_repository = customer_repository
        self.logic = CustomerInfoLogic(customer_repository)
        self.management_logic = CustomerManagementLogic(customer_repository)
        self._last_validation_state = True

    def initialize(self):
        """Initialize controller with default state."""
        self._emit_current_state()

    # Customer field update methods (called by UI signals)
    def on_national_id_changed(self, value: str):
        """Handle national ID field change."""
        self.update_customer_field('national_id', value)

    def on_full_name_changed(self, value: str):
        """Handle full name field change."""
        self.update_customer_field('name', value)

    def on_phone_changed(self, value: str):
        """Handle phone field change."""
        self.update_customer_field('phone', value)

    def on_address_changed(self, value: str):
        """Handle address field change."""
        self.update_customer_field('address', value)

    def on_email_changed(self, value: str):
        """Handle email field change."""
        self.update_customer_field('email', value)

    def on_has_companions_changed(self, has_companions: bool):
        """Handle companions checkbox change."""
        self.update_companions_status(has_companions)

    def on_companions_count_changed(self, count: int):
        """Handle companions count spinbox change."""
        self.set_companions_count(count)

    def on_add_companion_clicked(self):
        """Handle add companion button click."""
        self.add_companion()

    def on_delete_companion_clicked(self, companion_num: int):
        """Handle delete companion button click."""
        index = self.logic.get_companion_index_by_ui_number(companion_num)
        if index is not None:
            self.remove_companion(index)

    def on_companion_field_changed(self, companion_num: int, field_name: str, value: str):
        """Handle companion field change."""
        result = self.logic.update_companion_by_ui_number(companion_num, field_name, value)

        if not result.is_valid:
            self.error_occurred.emit("; ".join(result.errors))

        self._emit_current_state()
        self._emit_companion_validation(companion_num)

    # Action button handlers
    def on_add_customer_clicked(self):
        """Handle add customer button click."""
        # This could open a customer selection dialog
        # For now, we'll emit a signal that the view can handle
        self.customer_loaded.emit({})

    def on_delete_customer_clicked(self):
        """Handle delete customer button click."""
        self.clear_all_data()

    def on_customer_affairs_clicked(self):
        """Handle customer affairs button click."""
        # This could open a customer management dialog
        # Emit signal for view to handle
        pass

    # Business logic methods
    def update_customer_field(self, field_name: str, value: str):
        """Update a customer field."""
        result = self.logic.update_customer_field(field_name, value)

        if not result.is_valid:
            # Set field-specific errors
            for field, error in result.field_errors.items():
                self._emit_field_validation_error(field, error)

        self._emit_current_state()
        self._emit_field_validation(field_name)

    def update_companions_status(self, has_companions: bool):
        """Update companions status."""
        self.logic.set_companions_status(has_companions)
        self.companions_visibility_changed.emit(has_companions)
        self._emit_current_state()

        # If enabling companions and no companions exist, add one
        if has_companions and len(self.logic.get_current_data().companions) == 0:
            self.add_companion()

    def add_companion(self) -> int:
        """Add a new companion."""
        index, result = self.logic.add_companion()

        if not result.is_valid:
            self.error_occurred.emit("; ".join(result.errors))

        current_data = self.logic.get_current_data()
        self.companions_count_changed.emit(len(current_data.companions))
        self._emit_current_state()

        # Get the UI number of the newly added companion
        if current_data.companions:
            ui_number = current_data.companions[-1].ui_number

            # Emit signal to UI to add companion row
            if hasattr(self.parent(), 'add_companion_row'):
                self.parent().add_companion_row(ui_number)

            return ui_number

        return 0

    def remove_companion(self, index: int):
        """Remove a companion by index."""
        current_data = self.logic.get_current_data()

        if 0 <= index < len(current_data.companions):
            companion = current_data.companions[index]
            ui_number = companion.ui_number

            success = self.logic.remove_companion(index)
            if success:
                self.companions_count_changed.emit(len(self.logic.get_current_data().companions))
                self._emit_current_state()

                # Emit signal to UI to remove companion row
                if hasattr(self.parent(), 'remove_companion_row'):
                    self.parent().remove_companion_row(ui_number)

    def update_companion(self, index: int, name: str, national_id: str, phone: str = ""):
        """Update companion data."""
        result = self.logic.update_companion(index, name, national_id, phone)

        if not result.is_valid:
            self.error_occurred.emit("; ".join(result.errors))

        self._emit_current_state()
        self._emit_companion_validation_by_index(index)

    def set_companions_count(self, count: int):
        """Set the number of companions."""
        result = self.logic.set_companions_count(count)

        if not result.is_valid:
            self.error_occurred.emit("; ".join(result.errors))
            return

        current_data = self.logic.get_current_data()

        # Update UI based on actual count
        self.companions_count_changed.emit(len(current_data.companions))
        self._emit_current_state()

        # Notify UI about companion changes
        if hasattr(self.parent(), 'sync_companions_with_data'):
            self.parent().sync_companions_with_data(current_data.companions)

    def clear_all_data(self):
        """Clear all data."""
        self.logic.clear_all_data()
        self.companions_visibility_changed.emit(False)
        self.companions_count_changed.emit(0)
        self._emit_current_state()

        # Clear UI companions
        if hasattr(self.parent(), 'clear_companions'):
            self.parent().clear_companions()
        if hasattr(self.parent(), 'show_companions_group'):
            self.parent().show_companions_group(False)

    def load_customer_by_national_id(self, national_id: str):
        """Load existing customer by national ID."""
        result = self.logic.load_customer_by_national_id(national_id)

        if result.is_valid:
            current_data = self.logic.get_current_data()
            self.customer_loaded.emit(current_data.to_dict())
            self.companions_visibility_changed.emit(current_data.has_companions)
            self.companions_count_changed.emit(len(current_data.companions))
            self._emit_current_state()
        else:
            self.error_occurred.emit("; ".join(result.errors))

    def search_customers(self, search_term: str):
        """Search for customers."""
        customers = self.management_logic.search_customers(search_term)
        return [customer.to_dict() for customer in customers]

    def save_customer(self) -> bool:
        """Save current customer data."""
        result = self.logic.save_customer()

        if result.is_valid:
            self.customer_saved.emit()
            return True
        else:
            self.error_occurred.emit("; ".join(result.errors))
            return False

    def delete_customer(self) -> bool:
        """Delete current customer."""
        current_data = self.logic.get_current_data()
        if not current_data.customer.national_id:
            self.error_occurred.emit("هیچ مشتری برای حذف انتخاب نشده است")
            return False

        result = self.logic.delete_current_customer()

        if result.is_valid:
            self.customer_deleted.emit()
            self.companions_visibility_changed.emit(False)
            self.companions_count_changed.emit(0)
            self._emit_current_state()
            return True
        else:
            self.error_occurred.emit("; ".join(result.errors))
            return False

    # Data access methods
    def set_data(self, data: Dict[str, Any]):
        """Set customer data from dictionary."""
        result = self.logic.import_data(data)

        if result.is_valid:
            current_data = self.logic.get_current_data()
            self.companions_visibility_changed.emit(current_data.has_companions)
            self.companions_count_changed.emit(len(current_data.companions))
            self._emit_current_state()
        else:
            self.error_occurred.emit("; ".join(result.errors))

    def get_data(self) -> Dict[str, Any]:
        """Get customer data as dictionary."""
        return self.logic.get_current_data().to_dict()

    def is_valid(self) -> bool:
        """Check if current data is valid."""
        result = self.logic.validate_all_data()
        return result.is_valid

    def get_validation_errors(self) -> list:
        """Get validation errors."""
        result = self.logic.validate_all_data()
        return result.errors

    def export_data(self) -> Dict[str, Any]:
        """Export customer data for external use."""
        return self.logic.get_export_data()

    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import customer data from external source."""
        result = self.logic.import_data(data)

        if result.is_valid:
            current_data = self.logic.get_current_data()
            self.companions_visibility_changed.emit(current_data.has_companions)
            self.companions_count_changed.emit(len(current_data.companions))
            self._emit_current_state()
            return True
        else:
            self.error_occurred.emit("; ".join(result.errors))
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get data summary."""
        return self.logic.get_summary()

    def can_proceed_to_next_step(self) -> tuple:
        """Check if can proceed to next step."""
        return self.logic.can_proceed_to_next_step()

    def is_data_modified(self) -> bool:
        """Check if data has been modified."""
        return self.logic.is_data_modified()

    # Validation helper methods
    def get_field_validation_state(self, field_name: str) -> bool:
        """Get validation state for a specific field."""
        current_data = self.logic.get_current_data()
        customer = current_data.customer

        if field_name == 'national_id':
            value = customer.national_id.strip()
            return bool(value) and customer._is_valid_national_id(value)
        elif field_name == 'name':
            return bool(customer.name.strip())
        elif field_name == 'phone':
            value = customer.phone.strip()
            return bool(value) and customer._is_valid_phone(value)
        elif field_name in ['address', 'email']:
            return True  # Optional fields
        else:
            return True

    def get_companion_validation_state(self, ui_number: int, field_name: str) -> bool:
        """Get validation state for a companion field."""
        companion = self.logic.get_companion_by_ui_number(ui_number)
        if not companion:
            return True

        name = companion.name.strip()
        national_id = companion.national_id.strip()

        # If any field is filled, both should be filled and valid
        if name or national_id:
            if field_name == 'name':
                return bool(name)
            elif field_name == 'national_id':
                return bool(national_id) and companion._is_valid_national_id(national_id)

        return True  # Empty companions are valid

    # Private helper methods
    def _emit_current_state(self):
        """Emit current data and validation state."""
        data = self.logic.get_current_data().to_dict()
        is_valid = self.logic.validate_all_data().is_valid

        self.data_changed.emit(data)

        # Only emit validation changed if state actually changed
        if is_valid != self._last_validation_state:
            self.validation_changed.emit(is_valid)
            self._last_validation_state = is_valid

    def _emit_field_validation(self, field_name: str):
        """Emit field-specific validation."""
        is_valid = self.get_field_validation_state(field_name)
        self.field_validation_changed.emit(field_name, is_valid)

        # Update UI field validation if parent has the method
        if hasattr(self.parent(), 'set_field_validation'):
            self.parent().set_field_validation(field_name, is_valid)

    def _emit_field_validation_error(self, field_name: str, error_message: str):
        """Emit field validation error."""
        self.field_validation_changed.emit(field_name, False)

        # Update UI field validation if parent has the method
        if hasattr(self.parent(), 'set_field_validation'):
            self.parent().set_field_validation(field_name, False)

        # Show error message
        if hasattr(self.parent(), 'show_field_error'):
            self.parent().show_field_error(field_name, error_message)

    def _emit_companion_validation(self, ui_number: int):
        """Emit companion-specific validation."""
        companion = self.logic.get_companion_by_ui_number(ui_number)
        if not companion:
            return

        name = companion.name.strip()
        national_id = companion.national_id.strip()

        # If any field is filled, both should be filled and valid
        if name or national_id:
            name_valid = bool(name)
            national_id_valid = bool(national_id) and companion._is_valid_national_id(national_id)

            self.field_validation_changed.emit(f'companion_{ui_number}_name', name_valid)
            self.field_validation_changed.emit(f'companion_{ui_number}_national_id', national_id_valid)
        else:
            # Both fields are empty, which is valid
            self.field_validation_changed.emit(f'companion_{ui_number}_name', True)
            self.field_validation_changed.emit(f'companion_{ui_number}_national_id', True)

    def _emit_companion_validation_by_index(self, index: int):
        """Emit companion validation by index."""
        current_data = self.logic.get_current_data()
        if index < len(current_data.companions):
            companion = current_data.companions[index]
            self._emit_companion_validation(companion.ui_number)


class CustomerManagementController(QObject):
    """Controller for customer management operations."""

    # Signals
    customers_loaded = Signal(list)  # List of customer dictionaries
    customer_created = Signal(dict)  # Customer data
    customer_updated = Signal(dict)  # Customer data
    customer_deleted = Signal(str)  # National ID
    error_occurred = Signal(str)  # Error message
    search_completed = Signal(list)  # Search results

    def __init__(self, customer_repository: ICustomerRepository, parent=None):
        """Initialize controller with repository."""
        super().__init__(parent)
        self.customer_repository = customer_repository
        self.logic = CustomerManagementLogic(customer_repository)

    def load_all_customers(self, limit: int = 100):
        """Load all customers."""
        try:
            customers = self.logic.get_all_customers(limit)
            customer_dicts = [customer.to_dict() for customer in customers]
            self.customers_loaded.emit(customer_dicts)
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری مشتریان: {str(e)}")

    def search_customers(self, search_term: str):
        """Search customers by term."""
        try:
            if not search_term.strip():
                self.search_completed.emit([])
                return

            customers = self.logic.search_customers(search_term.strip())
            customer_dicts = [customer.to_dict() for customer in customers]
            self.search_completed.emit(customer_dicts)
        except Exception as e:
            self.error_occurred.emit(f"خطا در جستجو: {str(e)}")

    def create_customer(self, customer_data: Dict[str, Any]):
        """Create new customer."""
        try:
            customer = CustomerData.from_dict(customer_data)
            result = self.logic.create_customer(customer)

            if result.is_valid:
                self.customer_created.emit(customer.to_dict())
            else:
                self.error_occurred.emit("; ".join(result.errors))
        except Exception as e:
            self.error_occurred.emit(f"خطا در ایجاد مشتری: {str(e)}")

    def update_customer(self, customer_data: Dict[str, Any]):
        """Update existing customer."""
        try:
            customer = CustomerData.from_dict(customer_data)
            result = self.logic.update_customer(customer)

            if result.is_valid:
                self.customer_updated.emit(customer.to_dict())
            else:
                self.error_occurred.emit("; ".join(result.errors))
        except Exception as e:
            self.error_occurred.emit(f"خطا در به‌روزرسانی مشتری: {str(e)}")

    def delete_customer(self, national_id: str):
        """Delete customer."""
        try:
            result = self.logic.delete_customer(national_id)

            if result.is_valid:
                self.customer_deleted.emit(national_id)
            else:
                self.error_occurred.emit("; ".join(result.errors))
        except Exception as e:
            self.error_occurred.emit(f"خطا در حذف مشتری: {str(e)}")

    def get_customer_by_national_id(self, national_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by national ID."""
        try:
            customer = self.customer_repository.get_by_national_id(national_id)
            return customer.to_dict() if customer else None
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری مشتری: {str(e)}")
            return None

    def get_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get customer by phone."""
        try:
            customer = self.customer_repository.get_by_phone(phone)
            return customer.to_dict() if customer else None
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری مشتری: {str(e)}")
            return None

    def validate_customer_data(self, customer_data: Dict[str, Any]) -> tuple:
        """Validate customer data."""
        try:
            customer = CustomerData.from_dict(customer_data)
            is_valid = customer.is_valid()
            errors = customer.get_validation_errors() if not is_valid else []
            return is_valid, errors
        except Exception as e:
            return False, [f"خطا در اعتبارسنجی داده‌ها: {str(e)}"]

    def check_duplicate_national_id(self, national_id: str) -> bool:
        """Check if national ID already exists."""
        try:
            return self.customer_repository.customer_exists(national_id)
        except Exception as e:
            self.error_occurred.emit(f"خطا در بررسی کد ملی: {str(e)}")
            return False

    def check_duplicate_phone(self, phone: str, exclude_national_id: str = None) -> bool:
        """Check if phone number already exists."""
        try:
            return self.customer_repository.phone_exists(phone, exclude_national_id)
        except Exception as e:
            self.error_occurred.emit(f"خطا در بررسی شماره تماس: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get customer statistics."""
        try:
            return self.logic.get_customer_statistics()
        except Exception as e:
            self.error_occurred.emit(f"خطا در دریافت آمار: {str(e)}")
            return {}


class CustomerDialogController(QObject):
    """Controller for customer selection/management dialogs."""

    # Signals
    customer_selected = Signal(dict)  # Selected customer data
    dialog_closed = Signal()
    search_results_changed = Signal(list)

    def __init__(self, customer_repository: ICustomerRepository, parent=None):
        """Initialize with customer repository."""
        super().__init__(parent)
        self.management_controller = CustomerManagementController(customer_repository, self)
        self.selected_customer = None

        # Connect management controller signals
        self.management_controller.search_completed.connect(self.search_results_changed)
        self.management_controller.error_occurred.connect(self._handle_error)

    def search_customers(self, search_term: str):
        """Search customers and emit results."""
        self.management_controller.search_customers(search_term)

    def select_customer(self, customer_data: Dict[str, Any]):
        """Select a customer."""
        self.selected_customer = customer_data
        self.customer_selected.emit(customer_data)

    def get_selected_customer(self) -> Optional[Dict[str, Any]]:
        """Get currently selected customer."""
        return self.selected_customer

    def clear_selection(self):
        """Clear customer selection."""
        self.selected_customer = None

    def close_dialog(self):
        """Close dialog and emit signal."""
        self.dialog_closed.emit()

    def _handle_error(self, error_message: str):
        """Handle errors from management controller."""
        # Re-emit error or handle as needed
        if hasattr(self.parent(), 'show_error'):
            self.parent().show_error(error_message)


class ValidationController(QObject):
    """Helper controller for validation operations."""

    def __init__(self):
        """Initialize validation controller."""
        super().__init__()

    @staticmethod
    def validate_national_id(national_id: str) -> tuple:
        """Validate Iranian national ID."""
        customer_data = CustomerData(national_id=national_id)
        is_valid = customer_data._is_valid_national_id(national_id)
        error = "" if is_valid else "کد ملی معتبر نمی‌باشد"
        return is_valid, error

    @staticmethod
    def validate_phone(phone: str) -> tuple:
        """Validate phone number."""
        customer_data = CustomerData(phone=phone)
        is_valid = customer_data._is_valid_phone(phone)
        error = "" if is_valid else "شماره تماس معتبر نمی‌باشد"
        return is_valid, error

    @staticmethod
    def validate_required_field(value: str, field_name: str) -> tuple:
        """Validate required field."""
        is_valid = bool(value.strip())
        error = f"{field_name} الزامی است" if not is_valid else ""
        return is_valid, error

    @staticmethod
    def validate_email(email: str) -> tuple:
        """Validate email format (basic validation)."""
        if not email.strip():
            return True, ""  # Email is optional

        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        is_valid = bool(re.match(email_pattern, email.strip()))
        error = "فرمت ایمیل معتبر نمی‌باشد" if not is_valid else ""
        return is_valid, error


class ControllerFactory:
    """Factory for creating controllers with proper dependencies."""

    @staticmethod
    def create_customer_info_controller(customer_repository: ICustomerRepository,
                                        parent=None) -> CustomerInfoController:
        """Create customer info controller."""
        return CustomerInfoController(customer_repository, parent)

    @staticmethod
    def create_customer_management_controller(customer_repository: ICustomerRepository,
                                              parent=None) -> CustomerManagementController:
        """Create customer management controller."""
        return CustomerManagementController(customer_repository, parent)

    @staticmethod
    def create_customer_dialog_controller(customer_repository: ICustomerRepository,
                                          parent=None) -> CustomerDialogController:
        """Create customer dialog controller."""
        return CustomerDialogController(customer_repository, parent)

    @staticmethod
    def create_validation_controller() -> ValidationController:
        """Create validation controller."""
        return ValidationController()