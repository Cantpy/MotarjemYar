import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from features.InvoiceTable.invoice_table_models import InvoiceData, InvoiceSummary, InvoiceFilter, ColumnSettings
from features.InvoiceTable.invoice_table_repo import RepositoryManager
import logging

logger = logging.getLogger(__name__)


class InvoiceLogic:
    """Business logic for invoice operations"""

    def __init__(self, repo_manager: RepositoryManager):
        self.repo_manager = repo_manager
        self.filter = InvoiceFilter()
        self.column_settings = ColumnSettings()
        self._document_counts_cache = {}

    def load_invoices(self) -> List[InvoiceData]:
        """Load all invoices from repository"""
        invoices = self.repo_manager.get_invoice_repository().get_all_invoices()
        print("invoices: ", invoices)
        # Update document counts cache
        self._update_document_counts_cache()
        return invoices

    def get_filtered_invoices(self, invoices: List[InvoiceData]) -> List[InvoiceData]:
        """Get invoices filtered by current filter criteria"""
        if not self.filter.search_text:
            return invoices

        return [invoice for invoice in invoices if self.filter.matches_search(invoice)]

    def search_invoices(self, search_text: str, invoices: List[InvoiceData]) -> List[InvoiceData]:
        """Search invoices by text"""
        self.filter.set_search_text(search_text)
        return self.get_filtered_invoices(invoices)

    def delete_single_invoice(self, invoice_number: str) -> bool:
        """Delete a single invoice"""
        return self.repo_manager.get_invoice_repository().delete_invoices([invoice_number])

    def delete_multiple_invoices(self, invoice_numbers: List[str]) -> bool:
        """Delete multiple invoices"""
        if not invoice_numbers:
            return False
        return self.repo_manager.get_invoice_repository().delete_invoices(invoice_numbers)

    def update_invoice_data(self, invoice_number: str, updates: Dict[str, Any]) -> bool:
        """Update invoice data"""
        return self.repo_manager.get_invoice_repository().update_invoice(invoice_number, updates)

    def update_translator(self, invoice_number: str, translator_name: str) -> bool:
        """Update translator for invoice"""
        return self.repo_manager.get_invoice_repository().update_translator(invoice_number, translator_name)

    def get_translator_names(self) -> List[str]:
        """Get list of available translator names"""
        return self.repo_manager.get_user_repository().get_translator_names()

    def get_document_count(self, invoice_number: str) -> int:
        """Get document count for specific invoice"""
        if invoice_number in self._document_counts_cache:
            return self._document_counts_cache[invoice_number]

        count = self.repo_manager.get_invoice_repository().get_document_count(invoice_number)
        self._document_counts_cache[invoice_number] = count
        return count

    def _update_document_counts_cache(self):
        """Update document counts cache for all invoices"""
        self._document_counts_cache = self.repo_manager.get_invoice_repository().get_all_document_counts()

    def get_invoice_summary(self) -> Optional[InvoiceSummary]:
        """Get invoice summary statistics"""
        return self.repo_manager.get_invoice_repository().get_invoice_summary()

    def export_invoices_to_csv(self, invoice_numbers: List[str], file_path: str) -> bool:
        """Export selected invoices to CSV file"""
        try:
            data = self.repo_manager.get_invoice_repository().export_invoices_data(invoice_numbers)

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

    def get_column_names(self) -> List[str]:
        """Get list of column names"""
        return self.column_settings.COLUMN_NAMES

    def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
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


class FileLogic:
    """Logic for file operations"""

    @staticmethod
    def find_file_by_name(filename: str, search_path: str) -> Optional[str]:
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
    def recover_lost_pdf(invoice_number: str) -> Optional[str]:
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
                    found_file = FileLogic.find_file_by_name(pattern, path)
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


class NumberFormatLogic:
    """Logic for number formatting"""

    PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
    ENGLISH_DIGITS = '0123456789'

    @staticmethod
    def to_persian_number(text: str) -> str:
        """Convert English digits to Persian digits"""
        if not isinstance(text, str):
            text = str(text)

        translation_table = str.maketrans(
            NumberFormatLogic.ENGLISH_DIGITS,
            NumberFormatLogic.PERSIAN_DIGITS
        )
        return text.translate(translation_table)

    @staticmethod
    def to_english_number(text: str) -> str:
        """Convert Persian digits to English digits"""
        if not isinstance(text, str):
            text = str(text)

        translation_table = str.maketrans(
            NumberFormatLogic.PERSIAN_DIGITS,
            NumberFormatLogic.ENGLISH_DIGITS
        )
        return text.translate(translation_table)

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency with Persian digits and separators"""
        try:
            formatted = f"{int(amount):,}"
            return NumberFormatLogic.to_persian_number(formatted)
        except (ValueError, TypeError):
            return NumberFormatLogic.to_persian_number("0")


class ValidationLogic:
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
    def validate_amount(amount_str: str) -> Tuple[bool, float]:
        """Validate and parse amount string"""
        try:
            # Remove Persian digits and separators
            clean_amount = NumberFormatLogic.to_english_number(amount_str)
            clean_amount = clean_amount.replace(',', '').replace(' ', '')

            amount = float(clean_amount)
            return amount >= 0, amount
        except (ValueError, TypeError):
            return False, 0.0


class SearchLogic:
    """Logic for search and filtering operations"""

    @staticmethod
    def create_search_terms(search_text: str) -> List[str]:
        """Create search terms from search text"""
        if not search_text:
            return []

        # Convert Persian numbers to English for consistent searching
        normalized_text = NumberFormatLogic.to_english_number(search_text.lower())

        # Split by spaces and remove empty terms
        terms = [term.strip() for term in normalized_text.split() if term.strip()]

        return terms

    @staticmethod
    def matches_any_field(invoice: InvoiceData, search_terms: List[str]) -> bool:
        """Check if invoice matches any search term in any field"""
        if not search_terms:
            return True

        # Prepare searchable content
        searchable_content = [
            NumberFormatLogic.to_english_number(invoice.invoice_number.lower()),
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


class SortLogic:
    """Logic for sorting operations"""

    @staticmethod
    def sort_invoices(invoices: List[InvoiceData], sort_column: str, reverse: bool = False) -> List[InvoiceData]:
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


class ExportLogic:
    """Logic for export operations"""

    @staticmethod
    def prepare_export_data(invoices: List[InvoiceData], document_counts: Dict[str, int]) -> List[Dict[str, Any]]:
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
                'مبلغ کل': NumberFormatLogic.format_currency(invoice.total_amount)
            })

        return export_data

    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], file_path: str) -> bool:
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


class BulkOperationLogic:
    """Logic for bulk operations"""

    @staticmethod
    def validate_bulk_delete(selected_count: int, max_allowed: int = 100) -> Tuple[bool, str]:
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
