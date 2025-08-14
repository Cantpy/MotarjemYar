"""
Controller layer for Invoice Details functionality.
Connects the view with the business logic.
"""
import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from InvoicePage.invoice_details import (
    InvoiceData, InvoiceDetailsRequest, TranslationOfficeInfo, CustomerInfo, Language
)
from InvoicePage.invoice_details import InvoiceDetailsLogic
from InvoicePage.invoice_details import InvoiceDetailsRepository

logger = logging.getLogger(__name__)


class InvoiceDetailsController(QObject):
    """Controller for managing invoice details operations."""

    # Signals
    data_loaded = Signal(dict)  # Emitted when data is loaded
    error_occurred = Signal(str)  # Emitted when an error occurs
    validation_failed = Signal(list)  # Emitted when validation fails
    office_info_updated = Signal(dict)  # Emitted when office info is updated

    def __init__(self, db_session: Session, current_user: str, parent=None):
        """Initialize controller with database session and current user."""
        super().__init__(parent)
        self.db_session = db_session
        self.current_user = current_user

        # Initialize repository and logic layers
        self.repository = InvoiceDetailsRepository(db_session)
        self.logic = InvoiceDetailsLogic(self.repository)

        # Current invoice data
        self.current_invoice_data: Optional[InvoiceData] = None

        # View reference (will be set by the view)
        self.view = None

    def set_view(self, view):
        """Set the view reference."""
        self.view = view

        # Connect view signals to controller methods
        if hasattr(view, 'data_changed'):
            view.data_changed.connect(self.on_view_data_changed)

    def initialize_invoice(self, document_count: Optional[int] = None,
                           customer_info: Optional[CustomerInfo] = None):
        """Initialize invoice with default data."""
        try:
            request = InvoiceDetailsRequest(
                current_user=self.current_user,
                document_count=document_count,
                customer_info=customer_info
            )

            response = self.logic.initialize_invoice_data(request)

            if response.success:
                self.current_invoice_data = response.invoice_data

                # Update view with initialized data
                if self.view:
                    self._update_view_with_invoice_data(response.invoice_data, response.office_info)

                # Emit signal with loaded data
                self.data_loaded.emit({
                    'invoice_data': response.invoice_data,
                    'office_info': response.office_info,
                    'user_info': response.user_info,
                    'next_receipt_number': response.next_receipt_number
                })

            else:
                self.error_occurred.emit(response.message)

        except Exception as e:
            logger.error(f"Error initializing invoice: {str(e)}")
            self.error_occurred.emit(f"خطا در مقداردهی فاکتور: {str(e)}")

    def load_invoice_data(self, invoice_data: InvoiceData, office_info: TranslationOfficeInfo):
        """Load existing invoice data into the view."""
        try:
            self.current_invoice_data = invoice_data

            if self.view:
                self._update_view_with_invoice_data(invoice_data, office_info)

            self.data_loaded.emit({
                'invoice_data': invoice_data,
                'office_info': office_info
            })

        except Exception as e:
            logger.error(f"Error loading invoice data: {str(e)}")
            self.error_occurred.emit(f"خطا در بارگذاری اطلاعات فاکتور: {str(e)}")

    def validate_current_data(self) -> bool:
        """Validate current invoice data."""
        try:
            if not self.current_invoice_data:
                self.error_occurred.emit("هیچ داده‌ای برای اعتبارسنجی یافت نشد")
                return False

            # Update current data from view
            self._update_invoice_data_from_view()

            # Validate data
            response = self.logic.validate_invoice_data(self.current_invoice_data)

            if response.success:
                return True
            else:
                if response.errors:
                    self.validation_failed.emit(response.errors)
                else:
                    self.error_occurred.emit(response.message)
                return False

        except Exception as e:
            logger.error(f"Error validating invoice data: {str(e)}")
            self.error_occurred.emit(f"خطا در اعتبارسنجی: {str(e)}")
            return False

    def get_current_invoice_data(self) -> Optional[InvoiceData]:
        """Get current invoice data from view."""
        try:
            if self.view and self.current_invoice_data:
                self._update_invoice_data_from_view()
                return self.current_invoice_data
            return None

        except Exception as e:
            logger.error(f"Error getting current invoice data: {str(e)}")
            return None

    def update_financial_calculations(self):
        """Update financial calculations based on current data."""
        try:
            if not self.current_invoice_data or not self.current_invoice_data.financial:
                return

            # Get updated financial data from view
            if self.view:
                view_data = self.view.get_data()
                financial = self.current_invoice_data.financial

                financial.translation_cost = view_data.get('translation_cost', 0)
                financial.confirmation_cost = view_data.get('confirmation_cost', 0)
                financial.office_affairs_cost = view_data.get('office_affairs_cost', 0)
                financial.copy_certification_cost = view_data.get('copy_cert_cost', 0)
                financial.is_emergency = view_data.get('is_emergency', False)
                financial.discount_amount = view_data.get('discount_amount', 0)
                financial.advance_payment = view_data.get('advance_payment', 0)

                # Calculate totals using business logic
                updated_financial = self.logic.calculate_financial_totals(financial)

                # Update view with calculated values
                self.view.update_emergency_cost(updated_financial.emergency_cost)

                # Store updated financial data
                self.current_invoice_data.financial = updated_financial

        except Exception as e:
            logger.error(f"Error updating financial calculations: {str(e)}")
            self.error_occurred.emit(f"خطا در محاسبه مبالغ مالی: {str(e)}")

    def update_office_information(self, office_info: TranslationOfficeInfo):
        """Update translation office information."""
        try:
            response = self.logic.update_office_information(office_info, self.current_user)

            if response.success:
                # Update current invoice data
                if self.current_invoice_data:
                    self.current_invoice_data.office_info = office_info

                # Update view
                if self.view:
                    self.view.set_office_info(
                        name=office_info.name,
                        registration_number=office_info.registration_number,
                        translator=office_info.representative,
                        address=office_info.address,
                        phone=office_info.phone,
                        email=getattr(office_info, 'email', '')
                    )

                self.office_info_updated.emit({
                    'office_info': office_info,
                    'message': response.message
                })

            else:
                if response.errors:
                    self.validation_failed.emit(response.errors)
                else:
                    self.error_occurred.emit(response.message)

        except Exception as e:
            logger.error(f"Error updating office information: {str(e)}")
            self.error_occurred.emit(f"خطا در به‌روزرسانی اطلاعات دارالترجمه: {str(e)}")

    def get_suggested_receipt_number(self) -> str:
        """Get suggested receipt number for new invoice."""
        try:
            return self.logic.get_suggested_receipt_number(self.current_user)
        except Exception as e:
            logger.error(f"Error getting suggested receipt number: {str(e)}")
            return "1"

    def clear_invoice_data(self):
        """Clear current invoice data."""
        try:
            self.current_invoice_data = None

            if self.view:
                self.view.clear_data()

        except Exception as e:
            logger.error(f"Error clearing invoice data: {str(e)}")
            self.error_occurred.emit(f"خطا در پاک‌سازی اطلاعات: {str(e)}")

    def on_view_data_changed(self):
        """Handle view data changes."""
        try:
            # Update financial calculations when view data changes
            self.update_financial_calculations()

        except Exception as e:
            logger.error(f"Error handling view data change: {str(e)}")

    def set_customer_info(self, customer_info: CustomerInfo):
        """Set customer information."""
        try:
            if self.current_invoice_data:
                self.current_invoice_data.customer_info = customer_info

            if self.view:
                self.view.set_customer_info(
                    name=customer_info.name,
                    phone=customer_info.phone,
                    national_id=customer_info.national_id,
                    email=customer_info.email,
                    address=customer_info.address,
                    companion_num=str(customer_info.total_companions)
                )

        except Exception as e:
            logger.error(f"Error setting customer info: {str(e)}")
            self.error_occurred.emit(f"خطا در تنظیم اطلاعات مشتری: {str(e)}")

    def set_document_count(self, count: int):
        """Set document count."""
        try:
            if self.current_invoice_data and self.current_invoice_data.document_counts:
                self.current_invoice_data.document_counts.total_items = count

        except Exception as e:
            logger.error(f"Error setting document count: {str(e)}")

    def update_costs(self, translation_cost: float = 0, confirmation_cost: float = 0,
                     office_affairs_cost: float = 0, copy_cert_cost: float = 0):
        """Update cost values in the view."""
        try:
            if self.view:
                self.view.update_financial_display(
                    translation_cost=translation_cost,
                    confirmation_cost=confirmation_cost,
                    office_affairs_cost=office_affairs_cost,
                    copy_cert_cost=copy_cert_cost
                )

            # Update current invoice data
            if self.current_invoice_data and self.current_invoice_data.financial:
                financial = self.current_invoice_data.financial
                financial.translation_cost = translation_cost
                financial.confirmation_cost = confirmation_cost
                financial.office_affairs_cost = office_affairs_cost
                financial.copy_certification_cost = copy_cert_cost

                # Recalculate totals
                self.update_financial_calculations()

        except Exception as e:
            logger.error(f"Error updating costs: {str(e)}")
            self.error_occurred.emit(f"خطا در به‌روزرسانی هزینه‌ها: {str(e)}")

    def _update_view_with_invoice_data(self, invoice_data: InvoiceData, office_info: TranslationOfficeInfo):
        """Update view with invoice data."""
        if not self.view:
            return

        try:
            # Set invoice data in view
            self.view.set_data(invoice_data, office_info)

            # Set additional information
            self.view.set_receipt_number(invoice_data.receipt_number)
            self.view.set_username(invoice_data.username)

            # Set customer info if available
            if invoice_data.customer_info:
                self.view.set_customer_info(
                    name=invoice_data.customer_info.name,
                    phone=invoice_data.customer_info.phone,
                    national_id=invoice_data.customer_info.national_id,
                    email=invoice_data.customer_info.email,
                    address=invoice_data.customer_info.address,
                    companion_num=str(invoice_data.customer_info.total_companions)
                )

            # Update language display
            self.view.update_language_display()

        except Exception as e:
            logger.error(f"Error updating view with invoice data: {str(e)}")
            raise

    def _update_invoice_data_from_view(self):
        """Update invoice data from view values."""
        if not self.view or not self.current_invoice_data:
            return

        try:
            view_data = self.view.get_data()

            # Update basic info
            self.current_invoice_data.receipt_number = view_data.get('receipt_number', '')
            self.current_invoice_data.username = view_data.get('username', '')

            # Update languages
            source_lang_text = view_data.get('source_language', Language.FARSI.value)
            target_lang_text = view_data.get('target_language', Language.ENGLISH.value)

            # Find matching Language enum values
            for lang in Language:
                if lang.value == source_lang_text:
                    self.current_invoice_data.source_language = lang
                    break

            for lang in Language:
                if lang.value == target_lang_text:
                    self.current_invoice_data.target_language = lang
                    break

            # Update financial data
            if self.current_invoice_data.financial:
                financial = self.current_invoice_data.financial
                financial.translation_cost = view_data.get('translation_cost', 0)
                financial.confirmation_cost = view_data.get('confirmation_cost', 0)
                financial.office_affairs_cost = view_data.get('office_affairs_cost', 0)
                financial.copy_certification_cost = view_data.get('copy_cert_cost', 0)
                financial.emergency_cost = view_data.get('emergency_cost', 0)
                financial.is_emergency = view_data.get('is_emergency', False)
                financial.discount_amount = view_data.get('discount_amount', 0)
                financial.advance_payment = view_data.get('advance_payment', 0)
                financial.final_amount = view_data.get('final_amount', 0)

            # Update remarks
            self.current_invoice_data.remarks = view_data.get('remarks', '')

            # Update customer info
            customer_data = view_data.get('customer_info', {})
            if customer_data and self.current_invoice_data.customer_info:
                customer = self.current_invoice_data.customer_info
                customer.name = customer_data.get('name', '')
                customer.phone = customer_data.get('phone', '')
                customer.national_id = customer_data.get('national_id', '')
                customer.email = customer_data.get('email', '')
                customer.address = customer_data.get('address', '')

                # Convert companions to int
                try:
                    companions_str = customer_data.get('total_companions', '0')
                    customer.total_companions = int(companions_str) if companions_str.isdigit() else 0
                except (ValueError, AttributeError):
                    customer.total_companions = 0

        except Exception as e:
            logger.error(f"Error updating invoice data from view: {str(e)}")
            raise
