# features/Invoice_Page/invoice_preview/invoice_preview_logic.py

from datetime import datetime
from typing import List, Tuple, Optional

from features.Invoice_Page.invoice_preview.invoice_preview_repo import InvoicePreviewRepository
from features.Invoice_Page.invoice_preview.invoice_preview_models import (Invoice, Customer, PreviewItem,
                                                                          PreviewOfficeInfo)
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.invoice_preview.invoice_preview_settings_manager import PreviewSettingsManager

from shared.session_provider import ManagedSessionProvider, SessionManager
from shared.utils.date_utils import to_gregorian
from shared.orm_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel, EditedInvoiceModel


class InvoicePreviewLogic:
    """
    Handles business _logic related to invoices, such as pagination and data preparation.
    """
    def __init__(self, repo: InvoicePreviewRepository,
                 invoices_engine: ManagedSessionProvider,
                 settings_manager: PreviewSettingsManager):
        self._repo = repo
        self._invoices_session = invoices_engine
        self.settings_manager = settings_manager

    def get_issued_invoice(self, invoice_number: str) -> IssuedInvoiceModel | None:
        with self._invoices_session() as session:
            return self._repo.get_issued_invoice(session, invoice_number)

    def get_total_pages(self, invoice: Invoice) -> int:
        """
        Calculates total pages based on the advanced, content-aware rules.
        """
        if not invoice: return 1

        total_items = len(invoice.items)
        if total_items == 0:
            return 1

        conf = self.settings_manager.get_current_settings()['pagination']

        if total_items <= conf['one_page_max_rows']:
            return 1

        items_on_first_page = conf['first_page_max_rows']
        if total_items <= items_on_first_page:
            # This can happen if one_page_max_rows is smaller than first_page_max_rows
            return 1

        items_for_middle_and_last = total_items - items_on_first_page

        # We need at least one last page
        if items_for_middle_and_last <= conf['last_page_max_rows']:
            return 2

        items_for_middle_pages = items_for_middle_and_last - conf['last_page_max_rows']

        # Use integer division for clarity
        middle_pages = (items_for_middle_pages + conf['other_page_max_rows'] - 1) // conf['other_page_max_rows']

        return 2 + middle_pages

    @staticmethod
    def map_dto_to_orm(dto: InvoiceItem, invoice_number: str) -> InvoiceItemModel:
        """
        Maps the InvoiceItem DTO to the InvoiceItemModel ORM object for database saving.

        Args:
            dto: The fully populated InvoiceItem data transfer object.
            invoice_number: The invoice number this item belongs to.

        Returns:
            An instance of InvoiceItemModel ready to be added to a session.
        """
        orm_item = InvoiceItemModel(
            invoice_number=invoice_number,
            service_id=dto.service.id,
            service_name=dto.service.name,
            quantity=dto.quantity,
            page_count=dto.page_count,
            additional_issues=dto.extra_copies,  # The schema column is 'additional_issues'
            is_official=1 if dto.is_official else 0,
            has_judiciary_seal=1 if dto.has_judiciary_seal else 0,
            has_foreign_affairs_seal=1 if dto.has_foreign_affairs_seal else 0,
            remarks=dto.remarks,

            # Map the detailed financial breakdown directly
            translation_price=dto.translation_price,
            certified_copy_price=dto.certified_copy_price,
            registration_price=dto.registration_price,
            judiciary_seal_price=dto.judiciary_seal_price,
            foreign_affairs_seal_price=dto.foreign_affairs_seal_price,
            additional_issues_price=dto.extra_copy_price,
            total_price=dto.total_price
        )

        # --- Map the dynamic price details to the fixed DB columns ---
        # The database schema has fixed slots for two dynamic prices. We fill them sequentially.
        if len(dto.dynamic_price_details) > 0:
            # The schema uses dynamic_price_1 for the name and amount_1 for the value.
            orm_item.dynamic_price_1 = dto.dynamic_price_details[0][0]  # e.g., "تعداد ترم"
            orm_item.dynamic_price_amount_1 = dto.dynamic_price_details[0][2]  # e.g., 80000

        if len(dto.dynamic_price_details) > 1:
            orm_item.dynamic_price_2 = dto.dynamic_price_details[1][0]
            orm_item.dynamic_price_amount_2 = dto.dynamic_price_details[1][2]

        return orm_item

    def _parse_flexible_date(self, date_str: str) -> datetime:
        """
        Tries to parse a date string first as a date-time, then as a date-only.
        Returns datetime.now() only if both formats fail.
        """
        # 1. Define the possible formats, from most specific to least specific.
        datetime_format = "%Y/%m/%d - %H:%M"
        date_only_format = "%Y/%m/%d"

        # 2. Try the first format.
        try:
            return datetime.strptime(date_str, datetime_format)
        except ValueError:
            # 3. If the first fails, try the second format.
            try:
                return datetime.strptime(date_str, date_only_format)
            except ValueError:
                # 4. If all formats fail, log a warning and use the fallback.
                print(f"WARNING: Could not parse date '{date_str}' with any known format. Falling back.")
                return datetime.now()

    def get_items_for_page(self, invoice: Invoice, page_number: int) -> list[PreviewItem]:
        """
        Returns the correct slice of invoice items based on the page type.
        """
        if not invoice: return []

        total_pages = self.get_total_pages(invoice)
        if page_number < 1 or page_number > total_pages:
            return []

        total_items = len(invoice.items)
        conf = self.settings_manager.get_current_settings()['pagination']

        # --- Handle each page type ---

        # Case 1: The invoice is only one page long.
        if total_pages == 1:
            return invoice.items[:conf['one_page_max_rows']]

        # Case 2: This is the first page of a multi-page invoice.
        if page_number == 1:
            return invoice.items[:conf['first_page_max_rows']]

        # Case 3: This is the last page of a multi-page invoice.
        if page_number == total_pages:
            items_on_previous_pages = (conf['first_page_max_rows'] +
                                       (total_pages - 2) * conf['other_page_max_rows'])
            start_index = items_on_previous_pages
            return invoice.items[start_index:]

        # Case 4: This is a "middle" page (not first, not last).
        else:
            start_index = (conf['first_page_max_rows'] +
                           (page_number - 2) * conf['other_page_max_rows'])
            end_index = start_index + conf['other_page_max_rows']
            return invoice.items[start_index:end_index]

    def get_issued_invoice_with_items(self, invoice_number: str) -> IssuedInvoiceModel | None:
        """Manages the session to get an invoice and its items."""
        with self._invoices_session() as session:
            return self._repo.get_issued_invoice_with_items(session, invoice_number)

    def get_next_invoice_version_number(self, base_invoice_number: str) -> str:
        """
        Calculates the next version suffix for an invoice (e.g., -v2, -v3).
        This is now session-safe.
        """
        with self._invoices_session() as session:
            latest_invoice = self._repo.get_latest_invoice_version(session, base_invoice_number)

            if not latest_invoice:
                # If no previous version exists, the next one is -v2.
                return f"{base_invoice_number}-v2"

            # Access the attribute while the session is active.
            latest_num = latest_invoice.invoice_number
            import re
            match = re.search(r'-v(\d+)$', latest_num)

            if match:
                version = int(match.group(1))
                return f"{base_invoice_number}-v{version + 1}"
            else:
                # The existing invoice is the base version (e.g., 'INV-101'), so the next is -v2.
                return f"{base_invoice_number}-v2"

    def compare_invoice_data(self, new_invoice_dto: Invoice, new_items: list[InvoiceItem],
                             old_invoice_orm: IssuedInvoiceModel) -> bool:
        """
        Compares new invoice data with old data from the database.
        Returns True if identical, False otherwise.
        """
        # 1. Compare main invoice fields
        if (
                new_invoice_dto.customer.name != old_invoice_orm.name or
                new_invoice_dto.customer.national_id != old_invoice_orm.national_id or
                int(new_invoice_dto.payable_amount) != old_invoice_orm.final_amount or
                int(new_invoice_dto.discount_amount) != old_invoice_orm.discount_amount or
                int(new_invoice_dto.emergency_cost) != old_invoice_orm.emergency_cost
        ):
            return False

        # 2. Compare number of items
        if len(new_items) != len(old_invoice_orm.items):
            return False

        # 3. Compare each item in detail
        # Sort both lists to ensure a consistent comparison order
        sorted_new_items = sorted(new_items, key=lambda item: item.service.id)
        sorted_old_items = sorted(old_invoice_orm.items, key=lambda item: item.service_id)

        for new_item, old_item in zip(sorted_new_items, sorted_old_items):
            if (
                    new_item.service.id != old_item.service_id or
                    new_item.quantity != old_item.quantity or
                    new_item.page_count != old_item.page_count or
                    (1 if new_item.is_official else 0) != old_item.is_official or
                    (1 if new_item.has_judiciary_seal else 0) != old_item.has_judiciary_seal or
                    (1 if new_item.has_foreign_affairs_seal else 0) != old_item.has_foreign_affairs_seal or
                    new_item.total_price != old_item.total_price
            ):
                return False  # Found a difference

        # If all checks pass, the data is identical
        return True

    def check_for_invoice_changes(self,
                                  base_invoice_number: str,
                                  new_invoice_dto: Invoice,
                                  new_items: List[InvoiceItem]) -> Tuple[bool, IssuedInvoiceModel | None]:
        """
        Opens a session to fetch the latest version of an invoice and compares it
        with the new data. This entire operation is within a single session to
        avoid DetachedInstanceError.

        Returns:
            A tuple containing:
            - bool: True if the data is identical, False otherwise.
            - IssuedInvoiceModel | None: The fetched ORM object for reference, or None.
        """
        with self._invoices_session() as session:
            # Fetch the latest version using the active session
            latest_orm = self._repo.get_issued_invoice_with_items(session, base_invoice_number)

            if not latest_orm:
                # No existing invoice found, so it's definitely not identical.
                return False, None

            # Perform the comparison while the latest_orm object is still attached to the session
            is_identical = self._compare_invoice_data(new_invoice_dto, new_items, latest_orm)
            return is_identical, latest_orm

    @staticmethod
    def _generate_edit_logs(old_orm: IssuedInvoiceModel,
                            new_dto: Invoice,
                            new_items: List[InvoiceItem]) -> List[EditedInvoiceModel]:
        """
        Compares an old ORM invoice with new DTO data and generates a list of
        ORM objects detailing every change for the edit history table.
        """
        logs = []
        user_info = SessionManager().get_session()
        edited_by = user_info.username if user_info else "نامشخص"

        # Helper to create a log entry
        def add_log(field, old, new, remarks=""):
            logs.append(EditedInvoiceModel(
                invoice_number=old_orm.invoice_number,  # Log against the original number
                edited_field=field,
                old_value=str(old),
                new_value=str(new),
                edited_by=edited_by,
                remarks=remarks
            ))

        # 1. Compare Customer and Financial Fields
        if old_orm.name != new_dto.customer.name:
            add_log("نام مشتری", old_orm.name, new_dto.customer.name)
        if old_orm.national_id != new_dto.customer.national_id:
            add_log("کد ملی", old_orm.national_id, new_dto.customer.national_id)
        if old_orm.phone != new_dto.customer.phone:
            add_log("تلفن", old_orm.phone, new_dto.customer.phone)
        if old_orm.final_amount != int(new_dto.payable_amount):
            add_log("مبلغ نهایی", old_orm.final_amount, int(new_dto.payable_amount))
        if old_orm.discount_amount != int(new_dto.discount_amount):
            add_log("تخفیف", old_orm.discount_amount, int(new_dto.discount_amount))
        if old_orm.emergency_cost != int(new_dto.emergency_cost):
            add_log("هزینه فوریت", old_orm.emergency_cost, int(new_dto.emergency_cost))
        if old_orm.delivery_date != new_dto.delivery_date:
            add_log("تاریخ تحویل", old_orm.delivery_date.strftime('%Y-%m-%d'),
                    new_dto.delivery_date.strftime('%Y-%m-%d'))
        if old_orm.remarks != new_dto.remarks:
            add_log("توضیحات", old_orm.remarks, new_dto.remarks)

        # 2. Compare Items (more complex)
        old_items_map = {item.service_id: item for item in old_orm.items}
        new_items_map = {item.service.id: item for item in new_items}

        all_service_ids = set(old_items_map.keys()) | set(new_items_map.keys())

        for service_id in all_service_ids:
            old_item = old_items_map.get(service_id)
            new_item = new_items_map.get(service_id)

            if old_item and not new_item:
                add_log("آیتم‌های فاکتور", old_item.service_name, "حذف شده", f"آیتم '{old_item.service_name}' حذف شد.")
            elif new_item and not old_item:
                add_log("آیتم‌های فاکتور", "اضافه شده", new_item.service.name,
                        f"آیتم '{new_item.service.name}' اضافه شد.")
            elif old_item and new_item:
                # Item exists in both, check for modifications
                if old_item.total_price != new_item.total_price:
                    add_log(f"قیمت آیتم: {new_item.service.name}", old_item.total_price, new_item.total_price)
                if old_item.quantity != new_item.quantity:
                    add_log(f"تعداد آیتم: {new_item.service.name}", old_item.quantity, new_item.quantity)

        return logs

    def prepare_reissue_data(self,
                             base_invoice_number: str,
                             new_invoice_dto: Invoice,
                             new_items: List[InvoiceItem]
                             ) -> Tuple[bool, Optional[List[EditedInvoiceModel]]]:
        """
        A session-safe method that handles the entire process of checking for
        changes and generating edit logs.

        Returns:
            A tuple containing:
            - bool: True if the data has changed, False otherwise.
            - Optional[List[EditedInvoiceModel]]: A list of generated edit logs if
              changes were found, otherwise None.
        """
        with self._invoices_session() as session:
            # 1. Fetch the latest version using the active session
            latest_orm = self._repo.get_issued_invoice_with_items(session, base_invoice_number)

            if not latest_orm:
                # No existing invoice found, so there are changes (it's a new issue)
                return True, None

            # 2. Perform the comparison while the object is attached to the session
            is_identical = self._compare_invoice_data(new_invoice_dto, new_items, latest_orm)

            if is_identical:
                return False, None  # Data has NOT changed

            # 3. If not identical, generate logs while the object is still attached
            edit_logs = self._generate_edit_logs(latest_orm, new_invoice_dto, new_items)
            return True, edit_logs # Data HAS changed, and here are the logs

    @staticmethod
    def _compare_invoice_data(new_invoice_dto: Invoice, new_items: List[InvoiceItem],
                              old_invoice_orm: IssuedInvoiceModel) -> bool:
        """
        Compares new invoice data with old data from the database.
        Returns True if identical, False otherwise.
        (Now a static helper method).
        """
        # 1. Compare main invoice fields
        if (
                new_invoice_dto.customer.name != old_invoice_orm.name or
                new_invoice_dto.customer.national_id != old_invoice_orm.national_id or
                int(new_invoice_dto.payable_amount) != old_invoice_orm.final_amount or
                int(new_invoice_dto.discount_amount) != old_invoice_orm.discount_amount or
                int(new_invoice_dto.emergency_cost) != old_invoice_orm.emergency_cost
        ):
            return False

        # 2. Compare number of items
        if len(new_items) != len(old_invoice_orm.items):
            return False

        # 3. Compare each item in detail
        sorted_new_items = sorted(new_items, key=lambda item: item.service.id)
        sorted_old_items = sorted(old_invoice_orm.items, key=lambda item: item.service_id)

        for new_item, old_item in zip(sorted_new_items, sorted_old_items):
            if (
                    new_item.service.id != old_item.service_id or
                    new_item.quantity != old_item.quantity or
                    new_item.page_count != old_item.page_count or
                    (1 if new_item.is_official else 0) != old_item.is_official or
                    (1 if new_item.has_judiciary_seal else 0) != old_item.has_judiciary_seal or
                    (1 if new_item.has_foreign_affairs_seal else 0) != old_item.has_foreign_affairs_seal or
                    new_item.total_price != old_item.total_price
            ):
                return False  # Found a difference

        return True  # If all checks pass, the data is identical

    def assemble_invoice_data(self, customer: Customer, details: InvoiceDetails, assignments: dict) -> Invoice:
        """Core method to build the final Invoice DTO from other DTOs."""
        preview_items = []
        if assignments:
            for person_name, assigned_items in assignments.items():
                if person_name == "__unassigned__": continue
                for item in assigned_items:
                    preview_items.append(PreviewItem(
                        name=f"{item.service.name} ({person_name})",
                        type="رسمی" if item.is_official else "غیر رسمی",
                        quantity=1,
                        judiciary_seal="✔" if item.has_judiciary_seal else "-",
                        foreign_affairs_seal="✔" if item.has_foreign_affairs_seal else "-",
                        total_price=item.total_price,
                    ))

        print(f'raw issued date {details.issue_date} and delivery date {details.delivery_date}')
        issue_date = datetime.now()
        delivery_date = to_gregorian(details.delivery_date)

        print(f'issue date: {issue_date}, delivery date: {delivery_date}')

        user_info = SessionManager().get_session()

        issuer_name = "نامشخص"
        if user_info:
            issuer_name = user_info.full_name or user_info.username

        return Invoice(
            invoice_number=str(details.invoice_number),
            issue_date=issue_date, delivery_date=delivery_date,
            username=issuer_name, customer=customer, office=details.office_info,
            source_language=details.src_lng, target_language=details.trgt_lng,
            items=preview_items, total_amount=details.total_before_discount,
            total_translation_price=details.translation_cost, total_confirmation_price=details.confirmation_cost,
            total_office_price=details.office_costs, total_certified_copy_price=details.certified_copy_costs,
            discount_amount=details.discount_amount, advance_payment=details.advance_payment_amount,
            emergency_cost=details.emergency_cost_amount, remarks=details.remarks,
        )

    def issue_invoice_in_database(self, invoice_dto: Invoice, assignments: dict,
                                  edit_logs: Optional[List[EditedInvoiceModel]] = None) -> tuple[bool, str]:
        """
        Maps the invoice DTOs to ORM models and calls the repository to save them.
        """
        if not assignments:
            return False, "هیچ سندی برای صدور فاکتور وجود ندارد."

        try:
            total_translation_price = invoice_dto.total_translation_price
            total_confirmation_price = invoice_dto.total_confirmation_price
            total_office_price = invoice_dto.total_office_price
            total_certified_copy_price = invoice_dto.total_certified_copy_price
            total_additional_price = invoice_dto.total_additional_price
            total_amount = (total_additional_price + total_certified_copy_price + total_office_price +
                            total_confirmation_price + total_translation_price)

            issued_invoice_orm = IssuedInvoiceModel(
                invoice_number=invoice_dto.invoice_number,
                name=invoice_dto.customer.name,
                national_id=invoice_dto.customer.national_id,
                phone=invoice_dto.customer.phone,
                issue_date=invoice_dto.issue_date,
                delivery_date=invoice_dto.delivery_date,
                translator="",  # Translator will be assigned later
                total_items=len(invoice_dto.items),
                total_amount=int(total_amount),
                total_translation_price=int(total_translation_price),
                total_confirmation_price=int(total_confirmation_price),
                total_registration_price=int(total_office_price),
                total_certified_copy_price=int(total_certified_copy_price),
                total_additional_issues_price=int(total_additional_price),
                advance_payment=int(invoice_dto.advance_payment),
                discount_amount=int(invoice_dto.discount_amount),
                emergency_cost=int(invoice_dto.emergency_cost),
                final_amount=int(invoice_dto.payable_amount),
                username=invoice_dto.username,
                source_language=invoice_dto.source_language,
                target_language=invoice_dto.target_language,
                payment_status=0,
                delivery_status=0,
                remarks=invoice_dto.remarks or "",
            )
        except (ValueError, TypeError) as e:
            return False, f"خطا در تبدیل داده‌های فاکتور: {e}"

        items_orm_list = []
        for person_name, assigned_items in assignments.items():
            if person_name == "__unassigned__":
                continue
            for item_dto in assigned_items:
                item_orm = self.map_dto_to_orm(item_dto, invoice_dto.invoice_number)
                items_orm_list.append(item_orm)

        with self._invoices_session() as session:
            return self._repo.issue_invoice(session, issued_invoice_orm, items_orm_list, edit_logs)

    # --- New methods to handle calls that were previously controller -> _repo ---
    def get_invoice_path(self, invoice_number: str) -> str | None:
        """Manages the session to get the invoice path from the _repository."""
        with self._invoices_session() as session:
            return self._repo.get_invoice_path(session, invoice_number)

    def update_invoice_path(self, invoice_number: str, file_path: str) -> bool:
        """Manages the session to update the invoice path in the _repository."""
        with self._invoices_session() as session:
            return self._repo.update_invoice_path(session, invoice_number, file_path)

    def create_empty_preview(self):
        """Creates an empty preview for resetting the view layer."""
        empty_customer = Customer(
            name="",
            national_id="",
            phone="",
            address=""
        )
        empty_preview_office = PreviewOfficeInfo(
            name="",
            reg_no="",
            representative="",
            address="",
            phone="",
            email="",
            website="",
            whatsapp="",
            telegram="",
        )
        empty_invoice = Invoice(
            invoice_number="",
            issue_date=datetime.today(),
            delivery_date=datetime.today(),
            username="",
            customer=empty_customer,
            office=empty_preview_office,
            source_language="",
            target_language="",
            items=[],
            total_amount=0,
            discount_amount=0,
            advance_payment=0,
            emergency_cost=0,
            remarks=""
        )

        return empty_invoice
