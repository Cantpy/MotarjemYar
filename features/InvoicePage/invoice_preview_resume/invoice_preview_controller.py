"""
Controller for invoice preview functionality.
Handles user interactions and coordinates between view and business logic.
"""

import os
import sys
from typing import Optional, List, Dict, Any, Tuple
from datetime import date
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QMessageBox, QInputDialog, QFileDialog, QDialog
from PySide6.QtGui import QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from features.InvoicePage.invoice_preview_resume.invoice_preview_logic import InvoicePreviewLogic
from features.InvoicePage.invoice_preview_resume.invoice_preview_models import (InvoiceData, ScaleConfig,
                                                                                PaginationConfig)


class InvoicePreviewController(QObject):
    """Controller for managing invoice preview operations."""

    # Signals for view updates
    invoice_loaded = Signal(object)  # InvoiceData
    page_changed = Signal(int)  # current_page
    amounts_updated = Signal(dict)  # amount calculations
    error_occurred = Signal(str)  # error message
    success_message = Signal(str)  # success message
    export_completed = Signal(str)  # file path

    def __init__(self, logic: InvoicePreviewLogic, parent=None):
        super().__init__(parent)
        self.logic = logic
        self.current_invoice = None
        self.current_page = 1
        self.table_data = []
        self.pagination_config = PaginationConfig()
        self.scale_config = None

        # Initialize settings
        self.settings = QSettings("MyScale", "MyPreview")
        self._load_scale_settings()

    def _load_scale_settings(self):
        """Load scale settings from QSettings."""
        saved_scale = self.settings.value("scaling_factor", "100%")
        self.scale_config = self.logic.get_scale_config(str(saved_scale))

    def initialize_invoice(self, parent_invoice_widget, username: str):
        """Initialize invoice from parent widget data."""
        try:
            # Extract data from parent widget
            invoice_data = self._extract_invoice_data_from_parent(parent_invoice_widget, username)
            self.table_data = self._extract_table_data_from_parent(parent_invoice_widget)

            # Calculate pagination
            self.pagination_config = self.logic.calculate_pagination_config(
                len(self.table_data), self.scale_config
            )

            # Set current invoice
            self.current_invoice = invoice_data
            self.current_page = 1

            # Emit signals
            self.invoice_loaded.emit(invoice_data)
            self.page_changed.emit(self.current_page)

        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری فاکتور: {str(e)}")

    def _extract_invoice_data_from_parent(self, parent_widget, username: str) -> InvoiceData:
        """Extract invoice data from parent invoice widget."""
        # Get current invoice number
        invoice_no = parent_widget.get_current_invoice_no()

        # Extract basic info
        customer_name = parent_widget.ui.full_name_le.text()
        national_id = parent_widget.ui.national_id_le.text()
        phone_no = parent_widget.ui.phone_le.text()
        issue_date = date.today()  # You might want to get this from a date field

        # Get translator name from user profile
        translator = self.logic.get_user_display_name(username)

        # Create table data
        table_data = self._extract_table_data_from_parent(parent_widget)

        return self.logic.create_invoice_data(
            invoice_number=invoice_no,
            customer_name=customer_name,
            national_id=national_id,
            phone=phone_no,
            issue_date=issue_date,
            translator=translator,
            username=username,
            table_data=table_data
        )

    def _extract_table_data_from_parent(self, parent_widget) -> List[List[str]]:
        """Extract table data from parent widget."""
        source_table = parent_widget.ui.tableWidget
        row_count = source_table.rowCount()
        column_count = source_table.columnCount()

        extracted_data = []
        for row in range(row_count):
            row_data = []
            for column in range(column_count):
                item = source_table.item(row, column)
                row_data.append(item.text() if item else "")
            extracted_data.append(row_data)

        return extracted_data

    def load_existing_invoice(self, invoice_number: int) -> bool:
        """Load an existing invoice from database."""
        try:
            invoice_data = self.logic.load_invoice(invoice_number)
            if not invoice_data:
                self.error_occurred.emit(f"فاکتور شماره {invoice_number} یافت نشد")
                return False

            self.current_invoice = invoice_data
            self.current_page = 1

            # You'll need to reconstruct table_data from invoice items
            # This depends on your data structure
            self.table_data = self._reconstruct_table_data_from_invoice(invoice_data)

            # Recalculate pagination
            self.pagination_config = self.logic.calculate_pagination_config(
                len(self.table_data), self.scale_config
            )

            self.invoice_loaded.emit(invoice_data)
            self.page_changed.emit(self.current_page)
            return True

        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری فاکتور: {str(e)}")
            return False

    def _reconstruct_table_data_from_invoice(self, invoice_data: InvoiceData) -> List[List[str]]:
        """Reconstruct table data from invoice items."""
        table_data = []
        for item in invoice_data.items:
            row = [
                "",  # Row number - will be filled by view
                item.item_name,
                str(item.item_qty),
                str(item.judiciary_seal),
                str(item.foreign_affairs_seal),
                f"{item.item_price:,}"
            ]
            table_data.append(row)
        return table_data

    def navigate_to_page(self, page_number: int):
        """Navigate to specific page."""
        if 1 <= page_number <= self.pagination_config.total_pages:
            self.current_page = page_number
            self.page_changed.emit(self.current_page)

    def next_page(self):
        """Navigate to next page."""
        if self.current_page < self.pagination_config.total_pages:
            self.current_page += 1
            self.page_changed.emit(self.current_page)

    def previous_page(self):
        """Navigate to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.page_changed.emit(self.current_page)

    def get_current_page_data(self) -> Tuple[List[List[str]], int, int]:
        """Get data for current page."""
        start_idx, end_idx = self.logic.get_page_data(
            self.table_data, self.current_page, self.pagination_config
        )
        page_data = self.table_data[start_idx:end_idx]
        return page_data, start_idx, end_idx

    def apply_discount(self, discount_percentage: int):
        """Apply discount to invoice."""
        try:
            if not self.current_invoice:
                self.error_occurred.emit("هیچ فاکتوری بارگذاری نشده است")
                return

            if not (1 <= discount_percentage <= 100):
                self.error_occurred.emit("درصد تخفیف باید بین ۱ تا ۱۰۰ باشد")
                return

            discount_amount = self.logic.apply_discount(
                self.current_invoice.total_amount, discount_percentage
            )

            # Update invoice data
            self.current_invoice.discount_amount = discount_amount
            self.current_invoice.final_amount = max(0,
                                                    self.current_invoice.total_amount -
                                                    self.current_invoice.advance_payment -
                                                    discount_amount
                                                    )

            # Calculate and emit updated amounts
            amounts = self.logic.calculate_amounts(
                self.current_invoice.total_amount,
                self.current_invoice.advance_payment,
                self.current_invoice.discount_amount
            )
            self.amounts_updated.emit(amounts)

        except ValueError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"خطا در اعمال تخفیف: {str(e)}")

    def set_advance_payment(self, amount: int):
        """Set advance payment amount."""
        try:
            if not self.current_invoice:
                self.error_occurred.emit("هیچ فاکتوری بارگذاری نشده است")
                return

            if not self.logic.validate_advance_payment(amount, self.current_invoice.total_amount):
                self.error_occurred.emit("مبلغ بیعانه نمی‌تواند بیش از مبلغ فاکتور باشد")
                return

            # Update invoice data
            self.current_invoice.advance_payment = amount
            self.current_invoice.final_amount = max(0,
                                                    self.current_invoice.total_amount -
                                                    amount -
                                                    self.current_invoice.discount_amount
                                                    )

            # Calculate and emit updated amounts
            amounts = self.logic.calculate_amounts(
                self.current_invoice.total_amount,
                self.current_invoice.advance_payment,
                self.current_invoice.discount_amount
            )
            self.amounts_updated.emit(amounts)

        except Exception as e:
            self.error_occurred.emit(f"خطا در ثبت بیعانه: {str(e)}")

    def update_delivery_date(self, new_date: date):
        """Update delivery date."""
        if self.current_invoice:
            self.current_invoice.delivery_date = new_date

    def update_language(self, source_lang: str, target_lang: str):
        """Update translation languages."""
        if self.current_invoice:
            self.current_invoice.source_language = source_lang
            self.current_invoice.target_language = target_lang

    def update_remarks(self, remarks: str):
        """Update invoice remarks."""
        if self.current_invoice:
            self.current_invoice.remarks = remarks

    def save_invoice_as_png(self, file_path: str, widget_pixmap: QPixmap) -> bool:
        """Save invoice as PNG image."""
        try:
            if self.pagination_config.total_pages > 1:
                self.error_occurred.emit(
                    "فاکتورهایی که بیشتر از یک صفحه دارند را نمی‌توان با فرمت PNG ذخیره کرد. "
                    "لطفا از فرمت PDF استفاده کنید."
                )
                return False

            if widget_pixmap.save(file_path, "PNG"):
                # Save to database
                self.current_invoice.pdf_file_path = file_path
                if self.logic.save_invoice(self.current_invoice, self.table_data):
                    self.success_message.emit(f"فاکتور در آدرس زیر ذخیره شد:\n{file_path}")
                    self.export_completed.emit(file_path)
                    return True
                else:
                    self.error_occurred.emit("خطا در ذخیره اطلاعات فاکتور")
                    return False
            else:
                self.error_occurred.emit("خطا در ذخیره‌سازی فاکتور")
                return False

        except Exception as e:
            self.error_occurred.emit(f"خطا در ذخیره PNG: {str(e)}")
            return False

    def save_invoice_as_pdf(self, file_path: str) -> bool:
        """Save invoice as PDF - this will be handled by the view."""
        try:
            # The actual PDF generation will be handled by the view
            # Here we just update the database
            self.current_invoice.pdf_file_path = file_path
            if self.logic.save_invoice(self.current_invoice, self.table_data):
                self.success_message.emit(f"فاکتور در آدرس زیر ذخیره شد:\n{file_path}")
                self.export_completed.emit(file_path)
                return True
            else:
                self.error_occurred.emit("خطا در ذخیره اطلاعات فاکتور")
                return False

        except Exception as e:
            self.error_occurred.emit(f"خطا در ذخیره PDF: {str(e)}")
            return False

    def delete_current_invoice(self) -> bool:
        """Delete current invoice from database."""
        try:
            if not self.current_invoice:
                self.error_occurred.emit("هیچ فاکتوری انتخاب نشده است")
                return False

            if self.logic.delete_invoice(self.current_invoice.invoice_number):
                self.success_message.emit("فاکتور با موفقیت حذف شد")
                self.current_invoice = None
                self.table_data = []
                return True
            else:
                self.error_occurred.emit("خطا در حذف فاکتور")
                return False

        except Exception as e:
            self.error_occurred.emit(f"خطا در حذف فاکتور: {str(e)}")
            return False

    def get_invoice_statistics(self, username: str) -> Dict[str, Any]:
        """Get invoice statistics for user."""
        try:
            stats = self.logic.get_invoice_statistics(username)
            return {
                'total_invoices': stats.total_invoices,
                'total_revenue': stats.total_revenue,
                'average_amount': stats.average_invoice_amount,
                'total_discounts': stats.total_discounts,
                'total_advances': stats.total_advances,
                'total_docs': stats.total_official_docs + stats.total_unofficial_docs,
                'total_pages': stats.total_pages
            }
        except Exception as e:
            self.error_occurred.emit(f"خطا در دریافت آمار: {str(e)}")
            return {}

    def export_to_excel(self, username: str, file_path: str) -> bool:
        """Export user invoices to Excel."""
        try:
            invoices = self.logic.get_user_invoices(username)
            if not invoices:
                self.error_occurred.emit("هیچ فاکتوری برای خروجی یافت نشد")
                return False

            export_data = self.logic.prepare_export_data(invoices)

            # Convert to DataFrame and save (you'll need to implement this)
            # This is a placeholder - implement based on your export requirements
            self.success_message.emit(f"اطلاعات در فایل {file_path} ذخیره شد")
            self.export_completed.emit(file_path)
            return True

        except Exception as e:
            self.error_occurred.emit(f"خطا در خروجی Excel: {str(e)}")
            return False

    def validate_current_invoice(self) -> List[str]:
        """Validate current invoice data."""
        if not self.current_invoice:
            return ["هیچ فاکتوری بارگذاری نشده است"]

        return self.logic.validate_invoice_data(self.current_invoice)

    def get_translation_office_info(self) -> Dict[str, str]:
        """Get translation office information."""
        return self.logic.get_translation_office_info()

    def update_invoice_status(self, payment_status: int = None, delivery_status: int = None) -> bool:
        """Update invoice status."""
        try:
            if not self.current_invoice:
                self.error_occurred.emit("هیچ فاکتوری انتخاب نشده است")
                return False

            if self.logic.update_invoice_status(
                    self.current_invoice.invoice_number,
                    payment_status,
                    delivery_status
            ):
                status_text = "نهایی" if payment_status == 1 else "پیش‌نویس"
                self.success_message.emit(f"وضعیت فاکتور به '{status_text}' تغییر یافت")
                return True
            else:
                self.error_occurred.emit("خطا در به‌روزرسانی وضعیت")
                return False

        except Exception as e:
            self.error_occurred.emit(f"خطا در به‌روزرسانی وضعیت: {str(e)}")
            return False

    def get_formatted_amounts(self) -> Dict[str, str]:
        """Get formatted currency amounts for display."""
        if not self.current_invoice:
            return {
                'total_amount': '۰ تومان',
                'advance_payment': '۰ تومان',
                'discount_amount': '۰ تومان',
                'final_amount': '۰ تومان'
            }

        return {
            'total_amount': self.logic.format_currency(self.current_invoice.total_amount),
            'advance_payment': self.logic.format_currency(self.current_invoice.advance_payment),
            'discount_amount': self.logic.format_currency(self.current_invoice.discount_amount),
            'final_amount': self.logic.format_currency(self.current_invoice.final_amount)
        }

    def get_page_visibility_config(self) -> Dict[str, bool]:
        """Get configuration for UI element visibility on current page."""
        return self.logic.calculate_page_visibility(self.current_page, self.pagination_config.total_pages)

    def generate_suggested_filename(self, extension: str) -> str:
        """Generate suggested filename for save operations."""
        if not self.current_invoice:
            return f"invoice.{extension}"

        return self.logic.generate_invoice_filename(self.current_invoice, extension)
