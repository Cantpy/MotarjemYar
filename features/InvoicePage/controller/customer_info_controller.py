# -*- coding: utf-8 -*-
"""
Customer Information Controller - Business logic and UI coordination
"""
from PySide6.QtCore import QObject, Signal
from features.InvoicePage.backend.customer_info_backend import CustomerInfoBackend


class CustomerInfoController(QObject):
    """Controller class for customer information UI and backend coordination."""

    # Signals
    data_changed = Signal(dict)
    validation_changed = Signal(bool)
    companions_visibility_changed = Signal(bool)
    companions_count_changed = Signal(int)
    field_validation_changed = Signal(str, bool)  # field_name, is_valid

    def __init__(self, parent=None):
        super().__init__(parent)
        self.backend = CustomerInfoBackend()
        self._last_validation_state = True
        self._companion_counter = 0  # Track companion numbering

    def initialize(self):
        """Initialize controller with default state."""
        self._emit_current_state()

    # Customer field update methods (called by UI signals)
    def on_national_id_changed(self, value):
        """Handle national ID field change."""
        self.update_customer_field('national_id', value)

    def on_full_name_changed(self, value):
        """Handle full name field change."""
        self.update_customer_field('full_name', value)

    def on_phone_changed(self, value):
        """Handle phone field change."""
        self.update_customer_field('phone', value)

    def on_address_changed(self, value):
        """Handle address field change."""
        self.update_customer_field('address', value)

    def on_email_changed(self, value):
        """Handle email field change."""
        self.update_customer_field('email', value)

    def on_has_companions_changed(self, has_companions):
        """Handle companions checkbox change."""
        self.update_companions_status(has_companions)

    def on_companions_count_changed(self, count):
        """Handle companions count spinbox change."""
        self.set_companions_count(count)

    def on_add_companion_clicked(self):
        """Handle add companion button click."""
        self.add_companion()

    def on_delete_companion_clicked(self, companion_num):
        """Handle delete companion button click."""
        # Find the index of the companion with this number
        companions = self.backend.data['companions']
        for i, companion in enumerate(companions):
            if companion.get('_ui_number') == companion_num:
                self.remove_companion(i)
                break

    def on_companion_field_changed(self, companion_num, field_name, value):
        """Handle companion field change."""
        # Find the index of the companion with this number
        companions = self.backend.data['companions']
        for i, companion in enumerate(companions):
            if companion.get('_ui_number') == companion_num:
                if field_name == 'national_id':
                    self.update_companion(i, companion.get('name', ''), value)
                elif field_name == 'full_name':
                    self.update_companion(i, value, companion.get('national_id', ''))
                elif field_name == 'phone':
                    # Update phone field (if backend supports it)
                    companion['phone'] = value
                    self._emit_current_state()
                break

    # Action button handlers
    def on_add_customer_clicked(self):
        """Handle add customer button click."""
        # This could open a customer selection dialog or similar
        pass

    def on_delete_customer_clicked(self):
        """Handle delete customer button click."""
        self.clear_all_data()

    def on_customer_affairs_clicked(self):
        """Handle customer affairs button click."""
        # This could open a customer management dialog
        pass

    # Original methods (updated to work with UI)
    def update_customer_field(self, field_name, value):
        """Update a customer field."""
        self.backend.update_field(field_name, value)
        self._emit_current_state()
        self._emit_field_validation(field_name)

    def update_companions_status(self, has_companions):
        """Update companions status."""
        self.backend.set_companions_status(has_companions)
        self.companions_visibility_changed.emit(has_companions)
        self._emit_current_state()

        # If enabling companions and no companions exist, add one
        if has_companions and len(self.backend.data['companions']) == 0:
            self.add_companion()

    def add_companion(self):
        """Add a new companion."""
        self._companion_counter += 1
        companion_data = {
            'name': '',
            'national_id': '',
            'phone': '',
            '_ui_number': self._companion_counter  # Track UI number
        }

        self.backend.add_companion()
        # Update the last companion with UI number
        if self.backend.data['companions']:
            self.backend.data['companions'][-1].update(companion_data)

        self.companions_count_changed.emit(len(self.backend.data['companions']))
        self._emit_current_state()

        # Emit signal to UI to add companion row
        if hasattr(self.parent(), 'add_companion_row'):
            self.parent().add_companion_row(self._companion_counter)

        return len(self.backend.data['companions']) - 1  # Return index of new companion

    def remove_companion(self, index):
        """Remove a companion by index."""
        if 0 <= index < len(self.backend.data['companions']):
            companion = self.backend.data['companions'][index]
            ui_number = companion.get('_ui_number')

            self.backend.remove_companion(index)
            self.companions_count_changed.emit(len(self.backend.data['companions']))
            self._emit_current_state()

            # Emit signal to UI to remove companion row
            if hasattr(self.parent(), 'remove_companion_row') and ui_number:
                self.parent().remove_companion_row(ui_number)

    def update_companion(self, index, name, national_id):
        """Update companion data."""
        self.backend.update_companion(index, name, national_id)
        self._emit_current_state()
        self._emit_companion_validation(index)

    def set_companions_count(self, count):
        """Set the number of companions."""
        current_count = len(self.backend.data['companions'])

        if count > current_count:
            # Add companions
            for _ in range(count - current_count):
                self.add_companion()
        elif count < current_count:
            # Remove companions from the end
            for _ in range(current_count - count):
                self.remove_companion(len(self.backend.data['companions']) - 1)

    def clear_all_data(self):
        """Clear all data."""
        self.backend.clear_all_data()
        self._companion_counter = 0  # Reset companion counter
        self.companions_visibility_changed.emit(False)
        self.companions_count_changed.emit(0)
        self._emit_current_state()

        # Clear UI companions
        if hasattr(self.parent(), 'clear_companions'):
            self.parent().clear_companions()
        if hasattr(self.parent(), 'show_companions_group'):
            self.parent().show_companions_group(False)

    def set_data(self, data):
        """Set customer data."""
        self.backend.set_data(data)

        # Update companion counter based on existing companions
        companions = data.get('companions', [])
        for companion in companions:
            if '_ui_number' in companion:
                self._companion_counter = max(self._companion_counter, companion['_ui_number'])

        self.companions_visibility_changed.emit(data.get('has_companions', False))
        self.companions_count_changed.emit(len(companions))
        self._emit_current_state()

    def get_data(self):
        """Get customer data."""
        return self.backend.get_data()

    def is_valid(self):
        """Check if current data is valid."""
        return self.backend.is_valid()

    def get_validation_errors(self):
        """Get validation errors."""
        return self.backend.get_validation_errors()

    def export_data(self):
        """Export customer data."""
        return self.backend.export_data()

    def import_data(self, data):
        """Import customer data."""
        success = self.backend.import_data(data)
        if success:
            # Update companion counter
            companions = self.backend.data.get('companions', [])
            for companion in companions:
                if '_ui_number' in companion:
                    self._companion_counter = max(self._companion_counter, companion['_ui_number'])

            self.companions_visibility_changed.emit(self.backend.data['has_companions'])
            self.companions_count_changed.emit(len(companions))
            self._emit_current_state()
        return success

    def get_summary(self):
        """Get data summary."""
        return self.backend.get_summary()

    def _emit_current_state(self):
        """Emit current data and validation state."""
        data = self.backend.get_data()
        is_valid = self.backend.is_valid()

        self.data_changed.emit(data)

        # Only emit validation changed if state actually changed
        if is_valid != self._last_validation_state:
            self.validation_changed.emit(is_valid)
            self._last_validation_state = is_valid

    def _emit_field_validation(self, field_name):
        """Emit field-specific validation."""
        data = self.backend.get_data()
        field_value = data.get(field_name, '')

        # Basic validation for required fields
        if field_name in ['national_id', 'full_name', 'phone']:
            is_valid = bool(field_value.strip())
            if field_name == 'national_id' and is_valid:
                is_valid = self.backend._is_valid_national_id(field_value.strip())
            elif field_name == 'phone' and is_valid:
                is_valid = self.backend._is_valid_phone(field_value.strip())
        else:
            is_valid = True  # Optional fields are always valid

        self.field_validation_changed.emit(field_name, is_valid)

        # Update UI field validation if parent has the method
        if hasattr(self.parent(), 'set_field_validation'):
            self.parent().set_field_validation(field_name, is_valid)

    def _emit_companion_validation(self, index):
        """Emit companion-specific validation."""
        if index < len(self.backend.data['companions']):
            companion = self.backend.data['companions'][index]
            ui_number = companion.get('_ui_number')
            name = companion.get('name', '').strip()
            national_id = companion.get('national_id', '').strip()

            # If any field is filled, both should be filled and valid
            if name or national_id:
                name_valid = bool(name)
                national_id_valid = bool(national_id) and self.backend._is_valid_national_id(national_id)

                self.field_validation_changed.emit(f'companion_{ui_number}_name', name_valid)
                self.field_validation_changed.emit(f'companion_{ui_number}_national_id', national_id_valid)
            else:
                # Both fields are empty, which is valid
                self.field_validation_changed.emit(f'companion_{ui_number}_name', True)
                self.field_validation_changed.emit(f'companion_{ui_number}_national_id', True)

    def get_field_validation_state(self, field_name):
        """Get validation state for a specific field."""
        data = self.backend.get_data()

        if field_name == 'national_id':
            value = data.get('national_id', '').strip()
            return bool(value) and self.backend._is_valid_national_id(value)
        elif field_name == 'full_name':
            return bool(data.get('full_name', '').strip())
        elif field_name == 'phone':
            value = data.get('phone', '').strip()
            return bool(value) and self.backend._is_valid_phone(value)
        elif field_name == 'address':
            return True  # Address is optional
        else:
            return True

    def get_companion_validation_state(self, index, field_name):
        """Get validation state for a companion field."""
        if index >= len(self.backend.data['companions']):
            return True

        companion = self.backend.data['companions'][index]
        name = companion.get('name', '').strip()
        national_id = companion.get('national_id', '').strip()

        # If any field is filled, both should be filled and valid
        if name or national_id:
            if field_name == 'name':
                return bool(name)
            elif field_name == 'national_id':
                return bool(national_id) and self.backend._is_valid_national_id(national_id)

        return True  # Empty companions are valid
