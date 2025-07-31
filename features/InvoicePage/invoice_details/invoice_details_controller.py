from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox
from typing import Optional, Dict, Any
from datetime import datetime, date
from invoice_details_models import InvoiceData, FinancialDetails, TranslationOfficeInfo, Language


class InvoiceController(QObject):
    """Controller for managing invoice data and business logic."""

    # Signals
    data_changed = Signal()
    validation_changed = Signal(bool)  # True if valid, False if invalid
    error_occurred = Signal(str)  # Error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._invoice_data = InvoiceData()
        self._view = None
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.setSingleShot(True)

    def set_view(self, view):
        """Set the associated view."""
        self._view = view
        if view:
            view.data_changed.connect(self._on_view_data_changed)

    def get_invoice_data(self) -> InvoiceData:
        """Get current invoice data."""
        return self._invoice_data

    def set_invoice_data(self, data: InvoiceData):
        """Set invoice data and update view."""
        self._invoice_data = data
        if self._view:
            self._view.set_data(self._invoice_data)
        self._validate_and_emit()

    def load_from_dict(self, data: Dict[str, Any]):
        """Load invoice data from dictionary."""
        try:
            self._invoice_data = InvoiceData.from_dict(data)
            if self._view:
                self._view.set_data(self._invoice_data)
            self._validate_and_emit()
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری داده‌ها: {str(e)}")

    def save_to_dict(self) -> Dict[str, Any]:
        """Save invoice data to dictionary."""
        self._sync_data_from_view()
        return self._invoice_data.to_dict()

    def clear_data(self):
        """Clear all invoice data."""
        self._invoice_data = InvoiceData()
        if self._view:
            self._view.clear_data()
        self._validate_and_emit()

    def set_translation_costs(self, translation_cost: float, confirmation_cost: float = 0.0,
                              office_affairs_cost: float = 0.0, copy_cert_cost: float = 0.0):
        """Set translation-related costs."""
        self._invoice_data.financial.translation_cost = translation_cost
        self._invoice_data.financial.confirmation_cost = confirmation_cost
        self._invoice_data.financial.office_affairs_cost = office_affairs_cost
        self._invoice_data.financial.copy_certification_cost = copy_cert_cost

        # Update emergency cost if emergency is enabled
        if self._invoice_data.financial.is_emergency:
            self._calculate_emergency_cost()

        if self._view:
            self._view.update_financial_display()

        self._validate_and_emit()

    def set_emergency_status(self, is_emergency: bool):
        """Set emergency status and calculate emergency cost."""
        self._invoice_data.financial.is_emergency = is_emergency
        if is_emergency:
            self._calculate_emergency_cost()
        else:
            self._invoice_data.financial.emergency_cost = 0.0

        if self._view:
            self._view.update_emergency_cost(self._invoice_data.financial.emergency_cost)

        self._validate_and_emit()

    def set_emergency_cost(self, cost: float):
        """Manually set emergency cost."""
        self._invoice_data.financial.emergency_cost = max(0, cost)
        self._validate_and_emit()

    def set_office_info(self, name: str = None, address: str = None, phone: str = None,
                        email: str = None, license_number: str = None):
        """Set translation office information."""
        if name is not None:
            self._invoice_data.office_info.name = name
        if address is not None:
            self._invoice_data.office_info.address = address
        if phone is not None:
            self._invoice_data.office_info.phone = phone
        if email is not None:
            self._invoice_data.office_info.email = email
        if license_number is not None:
            self._invoice_data.office_info.license_number = license_number

        if self._view:
            self._view.update_office_info_display()

        self.data_changed.emit()

    def set_languages(self, source_lang: Language, target_lang: Language):
        """Set source and target languages."""
        self._invoice_data.source_language = source_lang
        self._invoice_data.target_language = target_lang

        if self._view:
            self._view.update_language_display()

        self.data_changed.emit()

    def validate(self) -> tuple[bool, list]:
        """Validate current data and return validation status and errors."""
        self._sync_data_from_view()
        errors = self._invoice_data.get_validation_errors()
        is_valid = len(errors) == 0
        return is_valid, errors

    def show_validation_errors(self):
        """Show validation errors in a message box."""
        is_valid, errors = self.validate()
        if not is_valid and self._view:
            error_text = "خطاهای اعتبارسنجی:\n\n" + "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self._view, "خطاهای اعتبارسنجی", error_text)

    def calculate_totals(self) -> Dict[str, float]:
        """Calculate and return financial totals."""
        self._sync_data_from_view()
        return {
            'subtotal': self._invoice_data.financial.subtotal,
            'discount': self._invoice_data.financial.discount_amount,
            'advance': self._invoice_data.financial.advance_payment,
            'final_amount': self._invoice_data.financial.final_amount
        }

    def enable_auto_save(self, interval_ms: int = 2000):
        """Enable auto-save functionality."""
        self._auto_save_timer.setInterval(interval_ms)

    def disable_auto_save(self):
        """Disable auto-save functionality."""
        self._auto_save_timer.stop()

    def _calculate_emergency_cost(self):
        """Calculate emergency cost as half of translation cost."""
        emergency_cost = self._invoice_data.financial.translation_cost / 2
        self._invoice_data.financial.emergency_cost = emergency_cost

    def _sync_data_from_view(self):
        """Synchronize data from view to model."""
        if not self._view:
            return

        view_data = self._view.get_data()

        # Update basic info
        self._invoice_data.receipt_number = view_data.get('receipt_number', 'نامشخص')
        self._invoice_data.username = view_data.get('username', 'نامشخص')
        self._invoice_data.delivery_date = view_data.get('delivery_date', date.today())
        self._invoice_data.remarks = view_data.get('remarks', '')

        # Update financial data
        self._invoice_data.financial.discount_amount = view_data.get('discount_amount', 0.0)
        self._invoice_data.financial.advance_payment = view_data.get('advance_payment', 0.0)
        self._invoice_data.financial.emergency_cost = view_data.get('emergency_cost', 0.0)
        self._invoice_data.financial.is_emergency = view_data.get('is_emergency', False)

        # Update languages
        source_lang_text = view_data.get('source_language', 'فارسی')
        target_lang_text = view_data.get('target_language', 'انگلیسی')

        for lang in Language:
            if lang.value == source_lang_text:
                self._invoice_data.source_language = lang
            if lang.value == target_lang_text:
                self._invoice_data.target_language = lang

        # Update office info
        office_data = view_data.get('office_info', {})
        if office_data:
            self._invoice_data.office_info.name = office_data.get('name', 'نامشخص')
            self._invoice_data.office_info.address = office_data.get('address', 'نامشخص')
            self._invoice_data.office_info.phone = office_data.get('phone', 'نامشخص')
            self._invoice_data.office_info.email = office_data.get('email', 'نامشخص')
            self._invoice_data.office_info.license_number = office_data.get('license_number', 'نامشخص')

    def _validate_and_emit(self):
        """Validate data and emit appropriate signals."""
        is_valid, _ = self.validate()
        self.validation_changed.emit(is_valid)
        self.data_changed.emit()

    def _on_view_data_changed(self):
        """Handle view data changes."""
        self._validate_and_emit()

        # Start auto-save timer
        if self._auto_save_timer.interval() > 0:
            self._auto_save_timer.start()

    def _auto_save(self):
        """Auto-save functionality (can be overridden by subclasses)."""
        # This method can be overridden to implement actual auto-save functionality
        # For now, it just validates the data
        self._sync_data_from_view()
        self.data_changed.emit()

    def format_currency(self, amount: float) -> str:
        """Format currency amount in Persian."""
        if amount == 0:
            return "۰ تومان"
        return f"{amount:,.0f} تومان".replace(',', '٬')

    def get_translation_direction_text(self) -> str:
        """Get formatted translation direction text."""
        return f"ترجمه از {self._invoice_data.source_language.value} به {self._invoice_data.target_language.value}"
