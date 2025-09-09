# features/Invoice_Table/invoice_table_logic.py

import os
import csv
from pathlib import Path
from typing import Any
from features.Invoice_Table.invoice_table_models import (InvoiceData, InvoiceSummary, InvoiceFilter,
                                                         ColumnSettings)
from features.Invoice_Table.invoice_table_repo import RepositoryManager
from PySide6.QtCore import QSettings
from shared.session_provider import SessionProvider
import logging

logger = logging.getLogger(__name__)


class InvoiceService:
    """Business _logic for invoice operations"""

    def __init__(self, repo_manager: RepositoryManager, session_provider: SessionProvider):
        self._repo_manager = repo_manager
        self._session_provider = session_provider
        self.filter = InvoiceFilter()
        self.column_settings = ColumnSettings()
        self._document_counts_cache = {}

    def get_all_invoices(self) -> list[InvoiceData]:
        """Load all invoices from repository"""
        with self._session_provider.invoices() as session:
            invoices = self._repo_manager.get_invoice_repository().get_all_invoices(session)
            # Update document counts cache
            self._update_document_counts_cache()
            return invoices

    def get_filtered_invoices(self, invoices: list[InvoiceData]) -> list[InvoiceData]:
        """Get invoices filtered by current filter criteria"""
        if not self.filter.search_text:
            return invoices

        return [invoice for invoice in invoices if self.filter.matches_search(invoice)]

    def search_invoices(self, search_text: str, invoices: list[InvoiceData]) -> list[InvoiceData]:
        """Search invoices by text"""
        self.filter.set_search_text(search_text)
        return self.get_filtered_invoices(invoices)

    def delete_single_invoice(self, invoice_number: str) -> bool:
        """Delete a single invoice"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().delete_invoices(session, [invoice_number])

    def delete_multiple_invoices(self, invoice_numbers: list[str]) -> bool:
        """Delete multiple invoices"""
        if not invoice_numbers:
            return False
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().delete_invoices(session, invoice_numbers)

    def update_invoice_data(self, invoice_number: str, updates: dict[str, object]) -> bool:
        """Update invoice data"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().update_invoice(session, invoice_number, updates)

    def update_translator(self, invoice_number: str, translator_name: str) -> bool:
        """Update translator for invoice"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().update_translator(session, invoice_number,
                                                                                 translator_name)
    def get_invoice_by_number(self, invoice_number: str):
        """"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().get_invoice_by_number(session, invoice_number)

    def get_translator_names(self) -> list[str]:
        """Get list of available translator names"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_user_repository().get_translator_names(session)

    def get_document_count(self, invoice_number: str) -> int:
        """Get document count for specific invoice"""
        if invoice_number in self._document_counts_cache:
            return self._document_counts_cache[invoice_number]

        with self._session_provider.invoices() as session:
            count = self._repo_manager.get_invoice_repository().get_document_count(session, invoice_number)
            self._document_counts_cache[invoice_number] = count
            return count

    def get_all_document_counts(self):
        """"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().get_all_document_counts(session)

    def _update_document_counts_cache(self):
        """Update document counts cache for all invoices"""
        with self._session_provider.invoices() as session:
            self._document_counts_cache = self._repo_manager.get_invoice_repository().get_all_document_counts(session)

    def get_invoice_summary(self) -> InvoiceSummary | None:
        """Get invoice summary statistics"""
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().get_invoice_summary(session)

    def export_invoices_to_csv(self, invoice_numbers: list[str], file_path: str) -> bool:
        """Export selected invoices to CSV file"""
        try:
            with self._session_provider.invoices() as session:
                data = self._repo_manager.get_invoice_repository().export_invoices_data(session, invoice_numbers)

                if not data:
                    logger.warning("No data to export")
                    return False

                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)

                    # Write header
                    writer.writerow([
                        'شماره فاکتور', 'نام', 'کد ملی', 'شماره تماس',
                        'تاریخ صدور', 'تاریخ تحویل', 'مترجم', 'مبلغ کل'
                    ])

                    # Write data
                    for row in data:
                        writer.writerow([
                            row['invoice_number'], row['name'], row['national_id'],
                            row['phone'], row['issue_date'], row['delivery_date'],
                            row['translator'], row['total_amount']
                        ])

                return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False

    def set_column_visibility(self, column_index: int, visible: bool):
        """Set column visibility"""
        self.column_settings.set_column_visible(column_index, visible)

    def is_column_visible(self, column_index: int) -> bool:
        """Check if column is visible"""
        return self.column_settings.is_column_visible(column_index)

    def get_column_names(self) -> list[str]:
        """Get list of column names"""
        return self.column_settings.COLUMN_NAMES

    def validate_invoice_data(self, invoice_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate invoice data"""
        errors = []

        # Required fields validation
        required_fields = ['invoice_number', 'name', 'national_id', 'phone']
        for field in required_fields:
            if not invoice_data.get(field, '').strip():
                errors.append(f"فیلد {field} الزامی است")

        # National ID validation (basic check)
        national_id = invoice_data.get('national_id', '')
        if national_id and (len(national_id) != 10 or not national_id.isdigit()):
            errors.append("کد ملی باید 10 رقم باشد")

        # Phone validation (basic check)
        phone = invoice_data.get('phone', '')
        if phone and (len(phone) < 10 or not phone.replace('-', '').replace(' ', '').isdigit()):
            errors.append("شماره تماس معتبر نیست")

        # Amount validation
        try:
            amount = float(invoice_data.get('total_amount', 0))
            if amount < 0:
                errors.append("مبلغ نمی‌تواند منفی باشد")
        except (ValueError, TypeError):
            errors.append("مبلغ معتبر نیست")

        return len(errors) == 0, errors

    def load_column_settings_from_source(self) -> list[bool]:
        """
        In a real app, this would load from QSettings or a config file.
        For now, it returns the default state from ColumnSettings.
        """
        settings = QSettings("YourApp", "InvoiceView")
        visibility = []
        for i in range(len(self.column_settings.COLUMN_NAMES)):
            is_visible = settings.value(f"col_{i}_visible", True, type=bool)
            visibility.append(is_visible)
            self.column_settings.set_column_visible(i, is_visible)
        return visibility
        # return self.column_settings.visible_columns  # Placeholder

    def save_column_settings_to_source(self):
        """
        In a real app, this would save the current state to QSettings.
        """
        settings = QSettings("YourApp", "InvoiceView")
        for i, is_visible in enumerate(self.column_settings.visible_columns):
            settings.setValue(f"col_{i}_visible", is_visible)
        # pass  # Placeholder

    def update_pdf_path(self, invoice_number: str, new_path: str):
        """

        """
        with self._session_provider.invoices() as session:
            return self._repo_manager.get_invoice_repository().update_pdf_path(session, invoice_number, new_path)


class NumberFormatService:
    """Logic for number formatting"""

    PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
    ENGLISH_DIGITS = '0123456789'

    @staticmethod
    def to_persian_number(text: str) -> str:
        """Convert English digits to Persian digits"""
        if not isinstance(text, str):
            text = str(text)

        translation_table = str.maketrans(
            NumberFormatService.ENGLISH_DIGITS,
            NumberFormatService.PERSIAN_DIGITS
        )
        return text.translate(translation_table)

    @staticmethod
    def to_english_number(text: str) -> str:
        """Convert Persian digits to English digits"""
        if not isinstance(text, str):
            text = str(text)

        translation_table = str.maketrans(
            NumberFormatService.PERSIAN_DIGITS,
            NumberFormatService.ENGLISH_DIGITS
        )
        return text.translate(translation_table)

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency with Persian digits and separators"""
        try:
            formatted = f"{int(amount):,}"
            return NumberFormatService.to_persian_number(formatted)
        except (ValueError, TypeError):
            return NumberFormatService.to_persian_number("0")


class FileService:
    """Logic for file operations"""

    @staticmethod
    def find_file_by_name(filename: str, search_path: str) -> str | None:
        """Find file by name in given path"""
        try:
            for root, dirs, files in os.walk(search_path):
                if filename in files:
                    return os.path.join(root, filename)
            return None
        except Exception as e:
            logger.error(f"Error searching for file {filename}: {e}")
            return None

    @staticmethod
    def recover_lost_pdf(invoice_number: str) -> str | None:
        """Try to recover lost PDF file by searching in common directories"""
        common_paths = [
            os.path.join(os.getcwd(), "invoices"),
            os.path.join(os.getcwd(), "pdfs"),
            os.path.join(os.getcwd(), "documents"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents")
        ]

        filename_patterns = [
            f"invoice_{invoice_number}.pdf",
            f"فاکتور_{invoice_number}.pdf",
            f"{invoice_number}.pdf"
        ]

        for path in common_paths:
            if os.path.exists(path):
                for pattern in filename_patterns:
                    found_file = FileService.find_file_by_name(pattern, path)
                    if found_file:
                        return found_file

        return None

    @staticmethod
    def validate_pdf_path(file_path: str) -> bool:
        """Validate PDF file path"""
        if not file_path:
            return False

        path = Path(file_path)
        return path.exists() and path.suffix.lower() == '.pdf'


class ValidationService:
    """Logic for data validation"""

    @staticmethod
    def validate_national_id(national_id: str) -> bool:
        """Validate Iranian national ID"""
        if not national_id or len(national_id) != 10:
            return False

        if not national_id.isdigit():
            return False

        # Check for repeated digits
        if len(set(national_id)) == 1:
            return False

        # Calculate checksum
        total = sum(int(national_id[i]) * (10 - i) for i in range(9))
        remainder = total % 11

        check_digit = int(national_id[9])

        if remainder < 2:
            return check_digit == remainder
        else:
            return check_digit == (11 - remainder)

    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate Iranian phone number"""
        if not phone:
            return False

        # Remove common separators
        clean_phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')

        # Check if all characters are digits
        if not clean_phone.isdigit():
            return False

        # Check length (Iranian mobile: 11 digits starting with 09, landline: 8-11 digits)
        if len(clean_phone) < 8 or len(clean_phone) > 11:
            return False

        # Check mobile number format
        if len(clean_phone) == 11 and not clean_phone.startswith('09'):
            return False

        return True

    @staticmethod
    def validate_amount(amount_str: str) -> tuple[bool, float]:
        """Validate and parse amount string"""
        try:
            # Remove Persian digits and separators
            clean_amount = NumberFormatService.to_english_number(amount_str)
            clean_amount = clean_amount.replace(',', '').replace(' ', '')

            amount = float(clean_amount)
            return amount >= 0, amount
        except (ValueError, TypeError):
            return False, 0.0


class SearchService:
    """Logic for search and filtering operations"""

    @staticmethod
    def create_search_terms(search_text: str) -> list[str]:
        """Create search terms from search text"""
        if not search_text:
            return []

        # Convert Persian numbers to English for consistent searching
        normalized_text = NumberFormatService.to_english_number(search_text.lower())

        # Split by spaces and remove empty terms
        terms = [term.strip() for term in normalized_text.split() if term.strip()]

        return terms

    @staticmethod
    def matches_any_field(invoice: InvoiceData, search_terms: list[str]) -> bool:
        """Check if invoice matches any search term in any field"""
        if not search_terms:
            return True

        # Prepare searchable content
        searchable_content = [
            NumberFormatService.to_english_number(invoice.invoice_number.lower()),
            invoice.name.lower(),
            invoice.national_id.lower(),
            invoice.phone.lower(),
            invoice.translator.lower(),
            invoice.issue_date.lower(),
            invoice.delivery_date.lower() if invoice.delivery_date else ""
        ]

        # Join all content for searching
        combined_content = ' '.join(searchable_content)

        # Check if any search term matches
        return any(term in combined_content for term in search_terms)


class SortService:
    """Logic for sorting operations"""

    @staticmethod
    def sort_invoices(invoices: list[InvoiceData], sort_column: str, reverse: bool = False) -> list[InvoiceData]:
        """Sort invoices by specified column"""
        sort_key_map = {
            'invoice_number': lambda x: x.invoice_number,
            'name': lambda x: x.name,
            'national_id': lambda x: x.national_id,
            'phone': lambda x: x.phone,
            'issue_date': lambda x: x.issue_date,
            'delivery_date': lambda x: x.delivery_date or "",
            'translator': lambda x: x.translator,
            'total_amount': lambda x: x.total_amount
        }

        if sort_column not in sort_key_map:
            return invoices

        try:
            return sorted(invoices, key=sort_key_map[sort_column], reverse=reverse)
        except Exception as e:
            logger.error(f"Error sorting invoices: {e}")
            return invoices


class InvoiceExportService:
    """Logic for export operations"""

    @staticmethod
    def prepare_export_data(invoices: list[InvoiceData], document_counts: dict[str, int]) -> list[dict[str, object]]:
        """Prepare invoice data for export"""
        export_data = []

        for invoice in invoices:
            doc_count = document_counts.get(invoice.invoice_number, 0)

            export_data.append({
                'شماره فاکتور': invoice.invoice_number,
                'نام': invoice.name,
                'کد ملی': invoice.national_id,
                'شماره تماس': invoice.phone,
                'تاریخ صدور': invoice.issue_date,
                'تاریخ تحویل': invoice.delivery_date,
                'مترجم': invoice.translator,
                'تعداد اسناد': doc_count,
                'مبلغ کل': NumberFormatService.format_currency(invoice.total_amount)
            })

        return export_data

    @staticmethod
    def export_to_csv(data: list[dict[str, object]], file_path: str) -> bool:
        """Export data to CSV file"""
        try:
            if not data:
                return False

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False


class BulkOperationService:
    """Logic for bulk operations"""

    @staticmethod
    def validate_bulk_delete(selected_count: int, max_allowed: int = 100) -> tuple[bool, str]:
        """Validate bulk delete operation"""
        if selected_count == 0:
            return False, "هیچ فاکتوری انتخاب نشده است"

        if selected_count > max_allowed:
            return False, f"نمی‌توان بیش از {max_allowed} فاکتور را همزمان حذف کرد"

        return True, ""

    @staticmethod
    def create_bulk_confirmation_message(operation: str, count: int) -> str:
        """Create confirmation message for bulk operations"""
        operation_names = {
            'delete': 'حذف',
            'export': 'صادر کردن',
            'update': 'به‌روزرسانی'
        }

        operation_name = operation_names.get(operation, operation)
        return f"آیا از {operation_name} {count} فاکتور انتخاب شده مطمئن هستید؟"
