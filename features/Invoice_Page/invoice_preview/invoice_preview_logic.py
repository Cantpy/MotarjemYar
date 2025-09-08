# features/Invoice_Page/invoice_preview/invoice_preview_logic.py

from datetime import datetime, date

from features.Invoice_Page.invoice_preview.invoice_preview_repo import InvoicePreviewRepository
from features.Invoice_Page.invoice_preview.invoice_preview_models import Invoice, Customer, PreviewItem
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails
from shared.session_provider import SessionProvider


class InvoicePreviewLogic:
    """
    Handles business _logic related to invoices, such as pagination and data preparation.
    """
    def __init__(self, repo: InvoicePreviewRepository, session_provider: SessionProvider):
        self._repo = repo
        self._session_provider = session_provider
        self.pagination_config = {
            'one_page_max_rows': 12, 'first_page_max_rows': 24,
            'other_page_max_rows': 28, 'last_page_max_rows': 22
        }

    def get_total_pages(self, invoice: Invoice) -> int:
        """
        Calculates total pages based on the advanced, content-aware rules.
        """
        # --- FIX: Add a check for a null invoice object ---
        if not invoice: return 1

        total_items = len(invoice.items)
        if total_items == 0:
            return 1

        conf = self.pagination_config

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

    def get_items_for_page(self, invoice: Invoice, page_number: int) -> list[PreviewItem]:
        """
        Returns the correct slice of invoice items based on the page type.
        """
        if not invoice: return []

        total_pages = self.get_total_pages(invoice)
        if page_number < 1 or page_number > total_pages:
            return []

        total_items = len(invoice.items)
        conf = self.pagination_config

        # --- Handle each page type ---

        # Case 1: The invoice is only one page long.
        if total_pages == 1:
            return invoice.items[:conf['one_page_max_rows']]

        # Case 2: This is the first page of a multi-page invoice.
        if page_number == 1:
            return invoice.items[:conf['first_page_max_rows']]

        # Case 3: This is the last page of a multi-page invoice.
        if page_number == total_pages:
            # Calculate the starting index for the last page's items.
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
                        total_price=item.total_price
                    ))

        # Safe date parsing
        try:
            delivery_date = datetime.strptime(details.delivery_date, "%Y/%m/%d").date()
        except (ValueError, TypeError):
            delivery_date = date.today()
        try:
            issue_date = datetime.strptime(details.issue_date, "%Y/%m/%d").date()
        except (ValueError, TypeError):
            issue_date = date.today()

        return Invoice(
            invoice_number=str(details.invoice_number),
            issue_date=issue_date, delivery_date=delivery_date,
            username=details.user, customer=customer, office=details.office_info,
            source_language=details.src_lng, target_language=details.trgt_lng,
            items=preview_items, total_amount=details.total_before_discount,
            discount_amount=details.discount_amount, advance_payment=details.advance_payment_amount,
            emergency_cost=details.emergency_cost_amount, remarks=details.remarks
        )

    # --- New methods to handle calls that were previously controller -> repo ---
    def get_invoice_path(self, invoice_number: str) -> str | None:
        """Manages the session to get the invoice path from the repository."""
        with self._session_provider.invoices() as session:
            return self._repo.get_invoice_path(session, invoice_number)

    def update_invoice_path(self, invoice_number: str, file_path: str) -> bool:
        """Manages the session to update the invoice path in the repository."""
        with self._session_provider.invoices() as session:
            return self._repo.update_invoice_path(session, invoice_number, file_path)
