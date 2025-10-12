# features/Invoice_Table/invoice_table_logic.py

from __future__ import annotations
import csv
import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional, Tuple

from features.Invoice_Table.invoice_table_models import InvoiceSummary, InvoiceFilter, ColumnSettings
from features.Invoice_Table.invoice_table_repo import (RepositoryManager, InvoiceData, InvoiceItemData,
                                                       EditedInvoiceData, DeletedInvoiceData)
from shared.session_provider import ManagedSessionProvider
from shared.utils.path_utils import get_user_data_path

logger = logging.getLogger(__name__)


# =============================================================================
# 1. SETTINGS SERVICE (Replaces QSettings with JSON)
# =============================================================================

class SettingsService:
    """Handles loading and saving of UI settings to a JSON file."""

    def __init__(self):
        self.settings_path = get_user_data_path("config", "invoice_table_settings.json")
        self.column_settings = ColumnSettings()

    def _load_settings(self) -> Dict:
        """Loads the raw settings dictionary from the JSON file."""
        if not self.settings_path.exists():
            return {}
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load settings from {self.settings_path}: {e}")
            return {}

    def _save_settings(self, settings: Dict):
        """Saves the raw settings dictionary to the JSON file."""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save settings to {self.settings_path}: {e}")

    def load_column_visibility(self) -> List[bool]:
        """Loads the column visibility state, returning defaults if not found."""
        settings = self._load_settings()
        visibility = settings.get('column_visibility', self.column_settings.visible_columns)
        # Ensure the loaded list has the correct length
        if len(visibility) != len(self.column_settings.COLUMN_NAMES):
            return self.column_settings.visible_columns
        self.column_settings.visible_columns = visibility
        return visibility

    def save_column_visibility(self):
        """Saves the current column visibility state."""
        settings = self._load_settings()
        settings['column_visibility'] = self.column_settings.visible_columns
        self._save_settings(settings)

    def set_column_visibility(self, index: int, visible: bool):
        """Updates the visibility for a specific column."""
        self.column_settings.set_column_visible(index, visible)

    def is_column_visible(self, index: int) -> bool:
        """Checks if a column is marked as visible."""
        return self.column_settings.is_column_visible(index)

    def get_column_names(self) -> List[str]:
        """Gets the names of all columns."""
        return self.column_settings.COLUMN_NAMES


# =============================================================================
# 2. CORE INVOICE SERVICE (Focused on Repository Interaction)
# =============================================================================

class InvoiceService:
    """
    Manages core invoice data operations by interacting with the repository.
    This class is the single gateway to the database for invoices.
    """

    def __init__(self,
                 repo_manager: RepositoryManager,
                 invoices_engine: ManagedSessionProvider,
                 users_engine: ManagedSessionProvider,
                 services_engine: ManagedSessionProvider):
        self._repo_manager = repo_manager
        self._invoice_session = invoices_engine
        self._users_session = users_engine
        self._services_session = services_engine
        self._document_counts_cache: Dict[str, int] = {}

    # ==============================================================
    # BASIC FETCH OPERATIONS
    # ==============================================================

    def get_all_invoices(self) -> List[InvoiceData]:
        """Loads all invoices and updates the document count cache."""
        with self._invoice_session() as session:
            invoices = self._repo_manager.get_invoice_repository().get_all_invoices(session)
            self._update_document_counts_cache()
            return invoices

    def get_invoice_by_number(self, invoice_number: str) -> Optional[InvoiceData]:
        """Retrieves a single invoice by its number."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().get_invoice_by_number(session, invoice_number)

    # ==============================================================
    # DETAILED FETCH (Invoice + Items + Services)
    # ==============================================================

    def get_invoice_with_details(self, invoice_number: str) -> Optional[tuple[InvoiceData, list[InvoiceItemData]]]:
        """
        Fetches an invoice and all its associated items,
        then enriches them with dynamic price names.
        """
        repo = self._repo_manager.get_invoice_repository()

        # Step 1: Fetch invoice and item dataclasses from the invoices DB.
        # This is safe because the repository converts ORM objects to dataclasses inside the session.
        with self._invoice_session() as invoice_session:
            invoice_data, items_data = repo.get_invoice_and_items(invoice_session, invoice_number)

            if not invoice_data:
                return None

            if not items_data:
                return invoice_data, []

        # Step 2: Collect ONLY the dynamic price IDs needed for enrichment.
        # We no longer need to look up the main service name; it's already in items_data.
        dynamic_price_ids: set[int] = set()
        for item in items_data:
            if item.dynamic_price_1: # Assuming the dataclass field is named `dynamic_price_1_id`
                dynamic_price_ids.add(item.dynamic_price_1)
            if item.dynamic_price_2: # Assuming the dataclass field is named `dynamic_price_2_id`
                dynamic_price_ids.add(item.dynamic_price_2)

        # Step 3: Fetch ONLY dynamic price names from the services DB.
        with self._services_session() as services_session:
            # We pass an empty set for service_ids as it's no longer needed.
            _, dynamic_price_map = repo.get_services_and_dynamic_prices(
                services_session, set(), dynamic_price_ids
            )

        # Step 4: Enrich the existing item dataclasses with the dynamic price names.
        for item in items_data:
            # The service_name is already correct from the repository. We just add the dynamic price names.
            item.dynamic_price_1_name = dynamic_price_map.get(item.dynamic_price_1)
            item.dynamic_price_2_name = dynamic_price_map.get(item.dynamic_price_2)

        return invoice_data, items_data

    # ==============================================================
    # UPDATE / DELETE OPERATIONS
    # ==============================================================

    def delete_invoices(self, invoice_numbers: List[str], deleted_by_user: str) -> List[str]:
        """
        Deletes one or more invoices by processing them one at a time.
        Each deletion is a separate transaction.
        """
        if not invoice_numbers:
            return []

        repo = self._repo_manager.get_invoice_repository()
        failed_deletions: List[str] = []

        for number in invoice_numbers:
            with self._invoice_session() as session:
                # MODIFICATION: Pass the username to the repository method
                if not repo.delete_invoice(session, number, deleted_by_user):
                    failed_deletions.append(number)
                    logger.error(f"Failed to delete invoice: {number}")

        if not failed_deletions:
            logger.info(f"Successfully deleted invoices: {invoice_numbers}")

        return failed_deletions

    def update_invoice_data(self, invoice_number: str, updates: Dict[str, Any]) -> bool:
        """Updates specific fields of an invoice."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().update_invoice(session, invoice_number, updates)

    def update_translator(self, invoice_number: str, translator_name: str) -> bool:
        """Updates translator for an invoice."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().update_translator(
                session, invoice_number, translator_name
            )

    def update_pdf_path(self, invoice_number: str, new_path: str) -> bool:
        """Updates the PDF file path for an invoice."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().update_pdf_path(session, invoice_number, new_path)

    # ==============================================================
    # UTILITY OPERATIONS
    # ==============================================================

    def get_translator_names(self) -> List[str]:
        """Gets a list of all available translator names."""
        with self._users_session() as session:
            return self._repo_manager.get_user_repository().get_translator_names(session)

    def get_document_counts(self) -> Dict[str, int]:
        """Returns the cached document counts for all invoices."""
        return self._document_counts_cache

    def _update_document_counts_cache(self):
        """Refreshes the internal cache of document counts from the database."""
        with self._invoice_session() as session:
            self._document_counts_cache = self._repo_manager.get_invoice_repository().get_all_document_counts(session)

    def get_invoice_summary(self) -> Optional[InvoiceSummary]:
        """Retrieves summary statistics for all invoices."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().get_invoice_summary(session)

    def get_invoices_for_export(self, invoice_numbers: List[str]) -> List[Dict[str, Any]]:
        """Fetches simplified invoice data suitable for exporting."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().export_invoices_data(session, invoice_numbers)

    # ==============================================================
    # EDIT HISTORY OPERATIONS
    # ==============================================================

    def log_invoice_edits(self, edits: List[EditedInvoiceData]) -> bool:
        """Logs a list of changes made to an invoice."""
        if not edits:
            return True  # Nothing to log
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().add_invoice_edits(session, edits)

    def get_invoice_edit_history(self, invoice_number: str) -> List[EditedInvoiceData]:
        """Retrieves the full edit history for a given invoice."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().get_edit_history_by_invoice_number(session,
                                                                                                  invoice_number)

    def get_all_deleted_invoices(self) -> List[DeletedInvoiceData]:
        """Retrieves all invoices from the deleted_invoices table."""
        with self._invoice_session() as session:
            return self._repo_manager.get_invoice_repository().get_all_deleted_invoices(session)


# =============================================================================
# 3. SPECIALIZED HELPER SERVICES (Single-Responsibility Classes)
# =============================================================================

class NumberFormatService:
    """Handles conversion and formatting of numbers, especially for Persian locale."""
    PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
    ENGLISH_DIGITS = '0123456789'
    TO_PERSIAN_TABLE = str.maketrans(ENGLISH_DIGITS, PERSIAN_DIGITS)
    TO_ENGLISH_TABLE = str.maketrans(PERSIAN_DIGITS, ENGLISH_DIGITS)

    @staticmethod
    def to_persian_number(text: Any) -> str:
        return str(text).translate(NumberFormatService.TO_PERSIAN_TABLE)

    @staticmethod
    def to_english_number(text: Any) -> str:
        return str(text).translate(NumberFormatService.TO_ENGLISH_TABLE)

    @staticmethod
    def format_currency(amount: float) -> str:
        try:
            formatted = f"{int(amount):,}"
            return NumberFormatService.to_persian_number(formatted)
        except (ValueError, TypeError):
            return NumberFormatService.to_persian_number("0")


class FileService:
    """Provides utilities for file system operations like searching and validation."""

    @staticmethod
    def validate_pdf_path(file_path: Optional[str]) -> bool:
        if not file_path:
            return False
        path = Path(file_path)
        return path.exists() and path.is_file() and path.suffix.lower() == '.pdf'


class ValidationService:
    """Provides methods for validating business-specific data."""

    @staticmethod
    def validate_invoice_update(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates data for an existing invoice being updated."""
        errors = []
        if not data.get('name', '').strip():
            errors.append("فیلد نام الزامی است")

        national_id = data.get('national_id', '')
        if national_id and (len(national_id) != 10 or not national_id.isdigit()):
            errors.append("کد ملی باید 10 رقم باشد")

        phone = data.get('phone', '')
        if phone and not (phone.isdigit() and 8 <= len(phone) <= 11):
            errors.append("شماره تماس معتبر نیست")

        return not errors, errors

    @staticmethod
    def validate_bulk_delete(selected_count: int, max_allowed: int = 100) -> tuple[bool, str]:
        """Validate bulk delete operation"""
        if selected_count == 0:
            return False, "هیچ فاکتوری انتخاب نشده است"

        if selected_count > max_allowed:
            return False, f"نمی‌توان بیش از {max_allowed} فاکتور را همزمان حذف کرد"

        return True, ""


class SearchService:
    """Implements the logic for filtering invoices based on search text."""

    def __init__(self):
        self.filter = InvoiceFilter()

    def search(self, search_text: str, invoices: List[InvoiceData]) -> List[InvoiceData]:
        """Filters a list of invoices based on the search text."""
        self.filter.set_search_text(search_text)
        if not self.filter.search_text:
            return invoices
        return [inv for inv in invoices if self.filter.matches_search(inv)]


class InvoiceExportService:
    """Handles the entire process of exporting invoice data to CSV."""

    def __init__(self, invoice_service: InvoiceService):
        self._invoice_service = invoice_service

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

    def export_to_csv(self, invoice_numbers: List[str], file_path: str) -> bool:
        """Exports selected invoices to a CSV file."""
        if not invoice_numbers:
            return False

        try:
            export_data = self._invoice_service.get_invoices_for_export(invoice_numbers)
            if not export_data:
                logger.warning("No data found for export.")
                return False

            headers = [
                'شماره فاکتور', 'نام', 'کد ملی', 'شماره تماس',
                'تاریخ صدور', 'تاریخ تحویل', 'مترجم', 'مبلغ کل'
            ]

            # Map model keys to Persian headers
            key_map = {
                'invoice_number': 'شماره فاکتور', 'name': 'نام', 'national_id': 'کد ملی',
                'phone': 'شماره تماس', 'issue_date': 'تاریخ صدور', 'delivery_date': 'تاریخ تحویل',
                'translator': 'مترجم', 'total_amount': 'مبلغ کل'
            }

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                for row_data in export_data:
                    # Create a new dict with Persian keys
                    persian_row = {key_map[key]: value for key, value in row_data.items()}
                    writer.writerow(persian_row)

            return True
        except (IOError, KeyError) as e:
            logger.error(f"Error exporting invoices to CSV: {e}")
            return False


# =============================================================================
# 4. LOGIC FAÇADE (The Controller's Single Point of Contact)
# =============================================================================

class InvoiceLogic:
    """
    A façade that provides a simplified interface to all invoice-related business logic.
    The controller interacts with this class, not the individual services.
    """

    def __init__(self,
                 invoice_service: InvoiceService,
                 settings_service: SettingsService,
                 file_service: FileService,
                 validation_service: ValidationService,
                 search_service: SearchService,
                 export_service: InvoiceExportService,
                 format_service: NumberFormatService):
        # Assign services to namespaced properties for clarity
        self.invoice = invoice_service
        self.settings = settings_service
        self.file = file_service
        self.validation = validation_service
        self.search = search_service
        self.export = export_service
        self.format = format_service
