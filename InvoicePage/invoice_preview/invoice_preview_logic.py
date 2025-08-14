# logic.py

from InvoicePage import (Invoice, Customer,
                         TranslationOffice, InvoiceItem)
from datetime import date
from typing import List
import math


class InvoiceService:
    """
    Handles business logic related to invoices, such as pagination and data preparation.
    """

    def __init__(self, invoice_data: Invoice):
        self.invoice = invoice_data

        self.pagination_config = {
            'one_page_max_rows': 12,  # For single-page invoices (with header & footer)
            'first_page_max_rows': 24,  # First of many pages (header, no footer)
            'other_page_max_rows': 28,  # Middle pages (no header, no footer)
            'last_page_max_rows': 22  # Last of many pages (no header, with footer)
        }

    def get_total_pages(self) -> int:
        """
        Calculates total pages based on the advanced, content-aware rules.
        """
        total_items = len(self.invoice.items)
        if total_items == 0:
            return 1

        # Rule 1: Does it fit on a single page?
        if total_items <= self.pagination_config['one_page_max_rows']:
            return 1

        # Rule 2: If not, does it fit on exactly two pages?
        # A two-page invoice has one "first_page" and one "last_page".
        if total_items <= (self.pagination_config['first_page_max_rows'] +
                           self.pagination_config['last_page_max_rows']):
            return 2

        # Rule 3: It must be three or more pages.
        # We subtract the items that will go on the dedicated first and last pages.
        items_for_middle_pages = (total_items -
                                  self.pagination_config['first_page_max_rows'] -
                                  self.pagination_config['last_page_max_rows'])

        # Calculate how many "other" pages are needed for the remaining items.
        middle_pages = math.ceil(items_for_middle_pages / self.pagination_config['other_page_max_rows'])

        # Total is 1 (first) + 1 (last) + the number of middle pages.
        return 2 + middle_pages

    def get_items_for_page(self, page_number: int) -> List[InvoiceItem]:
        """
        Returns the correct slice of invoice items based on the page type.
        """
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
                InvoiceItem(f"ترجمه رسمی شناسنامه به همراه تاییدات", "رسمی", 1, "دارد", "دارد", 1500000),
                InvoiceItem(f"ترجمه رسمی کارت ملی", "رسمی", 2, "دارد", "ندارد", 800000),
                InvoiceItem(f"ترجمه مقاله ISI در زمینه مهندسی", "غیررسمی", 15, "ندارد", "ندارد", 2250000),
                InvoiceItem(f"ترجمه رسمی دانشنامه و ریزنمرات", "رسمی", 1, "دارد", "دارد", 3500000),
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
