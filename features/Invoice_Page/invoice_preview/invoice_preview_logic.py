# features/Invoice_Page/invoice_preview/invoice_preview_logic.py

from datetime import datetime, date

from features.Invoice_Page.invoice_preview.invoice_preview_repo import InvoicePreviewRepository
from features.Invoice_Page.invoice_preview.invoice_preview_models import (Invoice, Customer, PreviewItem,
                                                                          PreviewOfficeInfo)
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails
from features.Invoice_Page.invoice_preview.invoice_preview_settings_manager import PreviewSettingsManager

from shared.session_provider import ManagedSessionProvider, SessionManager
from shared.utils.date_utils import jalali_obj_to_gregorian, to_gregorian
from shared.orm_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel


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
        # --- FIX: Add a check for a null invoice object ---
        if not invoice: return 1

        total_items = len(invoice.items)
        if total_items == 0:
            return 1

        conf = self.settings_manager.get_current_settings()['pagination']

        if total_items <= conf['one_page_max_rows']:
            return 1

        # --- SUBTLE BUG FIX: Handle the case where the last page is empty ---
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
            discount_amount=details.discount_amount, advance_payment=details.advance_payment_amount,
            emergency_cost=details.emergency_cost_amount, remarks=details.remarks,
        )

    def issue_invoice_in_database(self, invoice_dto: Invoice, assignments: dict) -> tuple[bool, str]:
        """
        Maps the invoice DTOs to ORM models and calls the repository to save them.
        """
        if not assignments:
            return False, "هیچ سندی برای صدور فاکتور وجود ندارد."

        try:
            total_translation_price = sum(
                item.total_price for items_list in assignments.values() for item in items_list
            )
            translators = {person for person in assignments if person != "__unassigned__"}

            issued_invoice_orm = IssuedInvoiceModel(
                invoice_number=invoice_dto.invoice_number,
                name=invoice_dto.customer.name,
                national_id=invoice_dto.customer.national_id,
                phone=invoice_dto.customer.phone,
                issue_date=invoice_dto.issue_date,
                delivery_date=invoice_dto.delivery_date,
                translator=", ".join(sorted(list(translators))),
                total_items=len(invoice_dto.items),
                total_amount=int(invoice_dto.total_amount),
                total_translation_price=int(total_translation_price),
                advance_payment=int(invoice_dto.advance_payment),
                discount_amount=int(invoice_dto.discount_amount),
                emergency_cost=int(invoice_dto.emergency_cost),
                final_amount=int(invoice_dto.payable_amount),
                username=invoice_dto.username,
                source_language=invoice_dto.source_language,
                target_language=invoice_dto.target_language,
                payment_status=0,
                delivery_status=0
            )
        except (ValueError, TypeError) as e:
            return False, f"خطا در تبدیل داده‌های فاکتور: {e}"

        items_orm_list = []
        for person_name, assigned_items in assignments.items():
            if person_name == "__unassigned__":
                continue
            for item in assigned_items:
                item_orm = InvoiceItemModel(
                    invoice_number=invoice_dto.invoice_number,
                    service=item.service.id,
                    page_count=item.page_count,
                    quantity=item.quantity,
                    is_official=1 if item.is_official else 0,
                    has_judiciary_seal=1 if item.has_judiciary_seal else 0,
                    has_foreign_affairs_seal=1 if item.has_foreign_affairs_seal else 0,
                    total_price=int(item.total_price)
                )
                items_orm_list.append(item_orm)

        with self._invoices_session() as session:
            return self._repo.issue_invoice(session, issued_invoice_orm, items_orm_list)

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
            issue_date=datetime.today().strftime("%Y/%m/%d - %H:%M"),
            delivery_date=datetime.today().strftime("%Y/%m/%d - %H:%M"),
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
