# -*- coding: utf-8 -*-
"""
Controller Layer - PySide6 Controller for UI coordination and business logic integration
"""
from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, Optional

from features.InvoicePage.customer_info.customer_info_models import CustomerData, CompanionData
from features.InvoicePage.customer_info.customer_info_logic import CustomerInfoLogic
from features.InvoicePage.customer_info.customer_info_repo import ICustomerRepository
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView


class CustomerInfoController(QObject):
    """Controller class for customer information UI and business logic coordination."""

    # Signals for UI updates
    data_changed = Signal(dict)
    validation_changed = Signal(bool)
    companions_visibility_changed = Signal(bool)
    field_validation_changed = Signal(str, bool)
    error_occurred = Signal(str)
    customer_loaded = Signal(dict)
    customer_saved = Signal()
    customer_deleted = Signal()
    companions_refreshed = Signal(list)

    def __init__(self, customer_repository: ICustomerRepository, view: 'CustomerInfoView'):
        super().__init__(view)
        self.view = view
        self.logic = CustomerInfoLogic(customer_repository)
        self._last_validation_state = True

    def initialize(self):
        """Initialize controller and load necessary data for the view."""
        self._load_and_set_autocompletion()
        self._emit_current_state()

    def _load_and_set_autocompletion(self):
        """Fetches data from the logic/repo and passes simple lists to the view."""
        try:
            # The controller is responsible for this data retrieval
            customers = self.logic.customer_repository.get_all_customers()

            # Prepare simple lists for the view
            customer_names = [c.name for c in customers]
            customer_phones = [c.phone for c in customers]
            customer_ids = [c.national_id for c in customers]

            # Pass the data to the view to set up completers
            self.view.setup_autocompleters({
                'names': customer_names,
                'phones': customer_phones,
                'national_ids': customer_ids
            })
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری اطلاعات تکمیلی: {str(e)}")

    def find_and_load_customer(self, identifier: str, field: str):
        """Finds a customer based on an identifier and loads their data."""
        try:
            if field == 'national_id':
                customer = self.logic.customer_repository.get_by_national_id(identifier)
            elif field == 'phone':
                customer = self.logic.customer_repository.get_by_phone(identifier)
            elif field == 'name':
                customers = self.logic.customer_repository.search_customers_by_partial_match('name', identifier,
                                                                                             limit=1)
                customer = customers[0] if customers else None
            else:
                customer = None

            if customer:
                self.load_customer_by_national_id(customer.national_id)

        except Exception as e:
            self.error_occurred.emit(f"خطا در یافتن مشتری: {str(e)}")

    # CustomerModel field update methods (called by UI signals)
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

    def on_telegram_id_changed(self, value: str):
        """Handle telegram ID field change."""
        self.update_customer_field('telegram_id', value)

    def on_has_companions_changed(self, has_companions: bool):
        """Handle companions checkbox change - no automatic companion creation."""
        self.update_companions_status(has_companions)

    def on_add_companion_clicked(self):
        """Handle add companion button click."""
        self.add_companion()

    def on_delete_companion_clicked(self, companion_num: int):
        """Handle delete companion button click with proper renumbering."""
        self.remove_companion_by_ui_number(companion_num)

    def on_companion_field_changed(self, companion_num: int, field_name: str, value: str):
        """Handle companion field change."""
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

    def on_refresh_companions_clicked(self):
        """Handle refresh companions button click."""
        self.refresh_companions_from_database()

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
        """Update companions status without automatically creating companions."""
        self.logic.set_companions_status(has_companions)
        self.companions_visibility_changed.emit(has_companions)
        self._emit_current_state()

        # Don't automatically add a companion - let user click the add button

    def add_companion(self) -> int:
        """Add a new companion with proper UI number management."""
        # Get current companions to determine next UI number
        current_data = self.logic.get_current_data()
        next_ui_number = len(current_data.companions) + 1

        index, result = self.logic.add_companion()

        if not result.is_valid:
            self.error_occurred.emit("; ".join(result.errors))
            return 0

        # Update the companion's UI number to be sequential
        updated_data = self.logic.get_current_data()
        if updated_data.companions:
            companion = updated_data.companions[-1]  # Get the newly added companion
            companion.ui_number = next_ui_number

        self._emit_current_state()

        # Safely emit signal to UI to add companion row
        try:
            if hasattr(self.parent(), 'add_companion_row'):
                self.parent().add_companion_row(next_ui_number)
        except (AttributeError, RuntimeError):
            # Parent doesn't have this method or is deleted
            pass

        return next_ui_number

    def remove_companion_by_ui_number(self, ui_number: int):
        """Remove a companion by UI number and renumber remaining companions."""
        current_data = self.logic.get_current_data()

        # Find the companion to remove
        companion_to_remove = None
        for comp in current_data.companions:
            if comp.ui_number == ui_number:
                companion_to_remove = comp
                break

        if not companion_to_remove:
            return

        # Remove the companion from logic
        index = current_data.companions.index(companion_to_remove)
        success = self.logic.remove_companion(index)

        if success:
            # Renumber remaining companions to fill gaps
            self._renumber_companions()

            # Get updated data for UI synchronization
            updated_data = self.logic.get_current_data()

            self._emit_current_state()

            # Update UI with renumbered companions
            try:
                if hasattr(self.parent(), 'renumber_companion_widgets'):
                    companion_dicts = [comp.to_dict() for comp in updated_data.companions]
                    self.parent().renumber_companion_widgets(companion_dicts)
            except (AttributeError, RuntimeError):
                pass

    def _renumber_companions(self):
        """Renumber companions to maintain sequential UI numbers."""
        current_data = self.logic.get_current_data()

        # Renumber companions sequentially
        for i, companion in enumerate(current_data.companions, 1):
            companion.ui_number = i

    def remove_companion(self, index: int):
        """Remove a companion by index - deprecated, use remove_companion_by_ui_number instead."""
        current_data = self.logic.get_current_data()

        if 0 <= index < len(current_data.companions):
            companion = current_data.companions[index]
            ui_number = companion.ui_number
            self.remove_companion_by_ui_number(ui_number)

    def update_companion(self, index: int, name: str, national_id: str, phone: str = ""):
        """Update companion data."""
        result = self.logic.update_companion(index, name, national_id, phone)

        if not result.is_valid:
            self.error_occurred.emit("; ".join(result.errors))

        self._emit_current_state()
        self._emit_companion_validation_by_index(index)

    def clear_all_data(self):
        """Clear all data."""
        self.logic.clear_all_data()
        self.companions_visibility_changed.emit(False)
        self._emit_current_state()

        # Clear UI companions
        if hasattr(self.parent(), 'clear_companions'):
            self.parent().clear_companions()
        if hasattr(self.parent(), 'show_companions_group'):
            self.parent().show_companions_group(False)

    def load_customer_by_national_id(self, national_id: str):
        """Load existing customer with companions by national ID."""
        result = self.logic.load_customer_by_national_id(national_id)

        if result.is_valid:
            current_data = self.logic.get_current_data()

            # Renumber companions for proper UI display
            self._renumber_companions()

            self.customer_loaded.emit(current_data.to_dict())
            self.companions_visibility_changed.emit(current_data.has_companions)
            self._emit_current_state()

            # Emit companions data for UI synchronization
            companion_dicts = [comp.to_dict() for comp in current_data.companions]
            self.companions_refreshed.emit(companion_dicts)
        else:
            self.error_occurred.emit("; ".join(result.errors))

    def refresh_companions_from_database(self):
        """Refresh companions data from database."""
        result = self.logic.refresh_companions_from_database()

        if result.is_valid:
            current_data = self.logic.get_current_data()

            # Renumber companions for proper UI display
            self._renumber_companions()

            self.companions_visibility_changed.emit(current_data.has_companions)
            self._emit_current_state()

            # Emit companions data for UI synchronization
            companion_dicts = [comp.to_dict() for comp in current_data.companions]
            self.companions_refreshed.emit(companion_dicts)
        else:
            self.error_occurred.emit("; ".join(result.errors))

    def search_customers(self, search_term: str):
        """Search for customers."""
        customers = self.management_logic.search_customers(search_term)
        return [customer.to_dict() for customer in customers]

    def save_customer(self) -> bool:
        """Save current customer data with companions."""
        try:
            result = self.logic.save_customer()

            if result.is_valid:
                self.customer_saved.emit()
                return True
            else:
                self.error_occurred.emit("; ".join(result.errors))
                return False
        except Exception as e:
            error_msg = f"خطای غیرمنتظره در ذخیره اطلاعات: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False

    def delete_customer(self) -> bool:
        """Delete current customer and all companions."""
        current_data = self.logic.get_current_data()
        if not current_data.customer.national_id:
            self.error_occurred.emit("هیچ مشتری برای حذف انتخاب نشده است")
            return False

        result = self.logic.delete_current_customer()

        if result.is_valid:
            self.customer_deleted.emit()
            self.companions_visibility_changed.emit(False)
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

            # Renumber companions for proper UI display
            self._renumber_companions()

            self.companions_visibility_changed.emit(current_data.has_companions)
            self._emit_current_state()

            # Emit companions data for UI synchronization
            companion_dicts = [comp.to_dict() for comp in current_data.companions]
            self.companions_refreshed.emit(companion_dicts)
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

            # Renumber companions for proper UI display
            self._renumber_companions()

            self.companions_visibility_changed.emit(current_data.has_companions)
            self._emit_current_state()

            # Emit companions data for UI synchronization
            companion_dicts = [comp.to_dict() for comp in current_data.companions]
            self.companions_refreshed.emit(companion_dicts)
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
            return bool(value) and customer.is_valid()
        elif field_name == 'name':
            return bool(customer.name.strip())
        elif field_name == 'phone':
            value = customer.phone.strip()
            return bool(value) and customer.is_valid()
        elif field_name in ['address', 'email', 'telegram_id']:
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
                return bool(national_id) and companion.is_valid()

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
            national_id_valid = bool(national_id) and companion.is_valid()

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
