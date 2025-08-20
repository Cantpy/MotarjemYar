# logic.py
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_models import (Invoice, Customer, TranslationOffice,
                                                                                  PreviewItem)
from PySide6.QtCore import QObject
from datetime import datetime, date
from typing import List
import math


class InvoicePreviewLogic(QObject):
    """
    Handles business logic related to invoices, such as pagination and data preparation.
    """

    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager
        self.invoice: Invoice = None
        self.pagination_config = {
            'one_page_max_rows': 12,  # For single-page invoices (with header & footer)
            'first_page_max_rows': 24,  # First of many pages (header, no footer)
            'other_page_max_rows': 28,  # Middle pages (no header, no footer)
            'last_page_max_rows': 22  # Last of many pages (no header, with footer)
        }

    # def get_total_pages(self) -> int:
    #     """
    #     Calculates total pages based on the advanced, content-aware rules.
    #     """
    #     total_items = len(self.invoice.items)
    #     if total_items == 0:
    #         return 1
    #
    #     # Rule 1: Does it fit on a single page?
    #     if total_items <= self.pagination_config['one_page_max_rows']:
    #         return 1
    #
    #     # Rule 2: If not, does it fit on exactly two pages?
    #     # A two-page invoice has one "first_page" and one "last_page".
    #     if total_items <= (self.pagination_config['first_page_max_rows'] +
    #                        self.pagination_config['last_page_max_rows']):
    #         return 2
    #
    #     # Rule 3: It must be three or more pages.
    #     # We subtract the items that will go on the dedicated first and last pages.
    #     items_for_middle_pages = (total_items -
    #                               self.pagination_config['first_page_max_rows'] -
    #                               self.pagination_config['last_page_max_rows'])
    #
    #     # Calculate how many "other" pages are needed for the remaining items.
    #     middle_pages = math.ceil(items_for_middle_pages / self.pagination_config['other_page_max_rows'])
    #
    #     # Total is 1 (first) + 1 (last) + the number of middle pages.
    #     return 2 + middle_pages

    def get_total_pages(self) -> int:
        """
        Calculates total pages based on the advanced, content-aware rules.
        """
        # --- FIX: Add a check for a null invoice object ---
        if not self.invoice:
            return 1

        total_items = len(self.invoice.items)
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

    def get_items_for_page(self, page_number: int) -> List[PreviewItem]:
        """
        Returns the correct slice of invoice items based on the page type.
        """
        if not self.invoice:
            return []

        total_pages = self.get_total_pages()
        if page_number < 1 or page_number > total_pages:
            return []

        total_items = len(self.invoice.items)
        conf = self.pagination_config

        # --- Handle each page type ---

        # Case 1: The invoice is only one page long.
        if total_pages == 1:
            return self.invoice.items[:conf['one_page_max_rows']]

        # Case 2: This is the first page of a multi-page invoice.
        if page_number == 1:
            return self.invoice.items[:conf['first_page_max_rows']]

        # Case 3: This is the last page of a multi-page invoice.
        if page_number == total_pages:
            # Calculate the starting index for the last page's items.
            items_on_previous_pages = (conf['first_page_max_rows'] +
                                       (total_pages - 2) * conf['other_page_max_rows'])
            start_index = items_on_previous_pages
            return self.invoice.items[start_index:]

        # Case 4: This is a "middle" page (not first, not last).
        else:
            start_index = (conf['first_page_max_rows'] +
                           (page_number - 2) * conf['other_page_max_rows'])
            end_index = start_index + conf['other_page_max_rows']
            return self.invoice.items[start_index:end_index]

    def assemble_invoice_data(self):
        """
        The core method that builds the final Invoice object from the StateManager.
        """
        customer = self.state_manager.get_customer()
        doc_items = self.state_manager.get_invoice_items()  # The list from step 2
        assignments = self.state_manager.get_assignments()
        details = self.state_manager.get_invoice_details()

        # --- Create PreviewItem list from assignments ---
        preview_items = []
        if assignments:
            for person_name, assigned_items in assignments.items():
                if person_name == "__unassigned__": continue
                for item in assigned_items:
                    preview_items.append(
                        PreviewItem(
                            name=f"{item.service.name} ({person_name})",
                            type="رسمی" if item.is_official else "غیر رسمی",
                            quantity=1,  # Items are already unpacked
                            judiciary_seal="✔" if item.has_judiciary_seal else "-",
                            foreign_affairs_seal="✔" if item.has_foreign_affairs_seal else "-",
                            total_price=item.total_price
                        )
                    )

        try:
            # Assuming your DatePickerLineEdit uses a 'YYYY/MM/DD' format
            delivery_date_obj = datetime.strptime(details.delivery_date, "%Y/%m/%d").date()
        except (ValueError, TypeError):
            delivery_date_obj = date.today()  # Fallback if parsing fails

        try:
            # Assuming get_persian_date returns a string in 'YYYY/MM/DD' format
            issue_date_obj = datetime.strptime(details.issue_date, "%Y/%m/%d").date()
        except (ValueError, TypeError):
            issue_date_obj = date.today()

        self.invoice = Invoice(
            invoice_number=str(details.invoice_number),
            issue_date=date.today(),  # Placeholder, you'd parse details.issue_date
            delivery_date=date.today(),  # Placeholder, you'd parse details.delivery_date
            username=details.user,
            customer=customer,  # The full Customer object
            office=details.office_info,  # The full OfficeInfo object
            source_language=details.src_lng,
            target_language=details.trgt_lng,
            items=preview_items,
            total_amount=details.total_before_discount,
            discount_amount=details.discount_amount,
            advance_payment=details.advance_payment_amount,
            emergency_cost=details.emergency_cost_amount,
            remarks=details.remarks
        )
        return self.invoice

def create_mock_invoice() -> Invoice:
    """Creates a sample invoice object with mock data for demonstration."""

    office = TranslationOffice(
        name="دارالترجمه رسمی زارعی",
        reg_no="۶۶۳",
        representative="آقای دکتر زارعی",
        address="اصفهان، خیابان هزارجریب، بین کوچه هشتم و دهم، ساختمان ۱۱۶",
        phone="۰۳۱-۳۶۶۹۱۳۷۹",
        email="translator663@gmail.com",
        socials="واتساپ: ۰۹۱۳۱۲۳۴۵۶۷",
        logo_path="assets/logo.png"
    )

    customer = Customer(
        name="علی رضایی",
        national_id="۱۲۳۴۵۶۷۸۹۰",
        phone="۰۹۱۳۱۲۳۴۵۶۷",
        address="تهران، میدان آزادی، خیابان آزادی، پلاک ۱۱۰"
    )

    items = [
                PreviewItem(f"ترجمه رسمی شناسنامه به همراه تاییدات", "رسمی", 1, "دارد", "دارد", 1500000),
                PreviewItem(f"ترجمه رسمی کارت ملی", "رسمی", 2, "دارد", "ندارد", 800000),
                PreviewItem(f"ترجمه مقاله ISI در زمینه مهندسی", "غیررسمی", 15, "ندارد", "ندارد", 2250000),
                PreviewItem(f"ترجمه رسمی دانشنامه و ریزنمرات", "رسمی", 1, "دارد", "دارد", 3500000),
            ] * 3

    subtotal = sum(item.total_price for item in items)
    vat_rate = 0.09
    vat_amount = subtotal * vat_rate

    # Updated: Added emergency cost instead of VAT
    emergency_cost = 500000.0
    remarks = ("لطفا اصل مدارک در زمان تحویل ارائه گردد. این فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک در زمان تحویل "
               "ارائه گردد. این فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک در زمان تحویل ارائه گردد. این فاکتور تا ۷ "
               "روز معتبر است.لطفا اصل مدارک در زمان تحویل ارائه گردد. این فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک "
               "در زمان تحویل ارائه گردد. این فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک در زمان تحویل ارائه گردد. این "
               "فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک در زمان تحویل ارائه گردد. این فاکتور تا ۷ روز معتبر است.لطفا "
               "اصل مدارک در زمان تحویل ارائه گردد. این فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک در زمان تحویل ارائه "
               "گردد. این فاکتور تا ۷ روز معتبر است.لطفا اصل مدارک در زمان تحویل ارائه گردد. این فاکتور تا ۷ روز "
               "معتبر است.")

    invoice = Invoice(
        invoice_number="140399",
        issue_date=date.today(),
        delivery_date=date(2025, 9, 15),
        username="محمد کریمی",
        customer=customer,
        office=office,
        source_language="فارسی",
        target_language="انگلیسی",
        items=items,
        total_amount=subtotal,
        discount_amount=15000,
        advance_payment=200000,
        emergency_cost=emergency_cost,
        remarks=remarks
    )

    return invoice
