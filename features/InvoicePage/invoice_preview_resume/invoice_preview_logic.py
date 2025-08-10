"""
Business logic for invoice preview functionality.
"""

import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import date, datetime
from contextlib import contextmanager

from features.InvoicePage.invoice_preview_resume.invoice_preview_models import (
    InvoiceData, InvoiceItem, InvoiceSummary, ScaleConfig,
    PaginationConfig, InvoiceStatistics, InvoiceExportData
)
from features.InvoicePage.invoice_preview_resume.invoice_preview_repo import InvoicePreviewRepository


class InvoicePreviewLogic:
    """Business logic for invoice preview operations."""

    # Scale factor configurations
    SCALE_CONFIGS = {
        "125%": ScaleConfig(
            ui_module='qt_designer_ui.ui_paginated_invoice_widget_large',
            column_width=[4, 300, 90, 50, 50, 50, 130],
            first_page_rows=17,
            last_page_rows=16,
            first_table_rows=10,
            other_page_rows=26,
            remarks_font=10.0,
            scale_factor=1.0
        ),
        "100%": ScaleConfig(
            ui_module='qt_designer_ui.ui_paginated_invoice_widget_medium',
            column_width=[3, 230, 50, 30, 30, 30, 70],
            first_page_rows=14,
            last_page_rows=9,
            first_table_rows=6,
            other_page_rows=21,
            remarks_font=9.0,
            scale_factor=0.75
        ),
        "75%": ScaleConfig(
            ui_module='qt_designer_ui.ui_paginated_invoice_widget_small',
            column_width=[2, 190, 35, 20, 20, 20, 50],
            first_page_rows=11,
            last_page_rows=8,
            first_table_rows=5,
            other_page_rows=17,
            remarks_font=7.5,
            scale_factor=0.5
        )
    }

    def __init__(self, repository: InvoicePreviewRepository):
        self.repository = repository
        self.pagination_config = PaginationConfig()

    def get_scale_config(self, scale_factor: str = "100%") -> ScaleConfig:
        """Get scale configuration for UI display."""
        return self.SCALE_CONFIGS.get(scale_factor, self.SCALE_CONFIGS["100%"])

    def calculate_invoice_summary(self, table_data: List[List[str]]) -> InvoiceSummary:
        """Calculate invoice summary from table data."""
        summary = InvoiceSummary()

        for row_data in table_data:
            if len(row_data) < 6:  # Skip incomplete rows
                continue

            try:
                # Parse quantities and prices
                quantity = int(row_data[2]) if row_data[2].strip() else 0
                judiciary_count = int(row_data[3]) if row_data[3].strip() else 0
                foreign_affairs_count = int(row_data[4]) if row_data[4].strip() else 0
                price_str = row_data[5].replace(",", "") if len(row_data) > 5 else "0"
                item_price = int(price_str) if price_str.strip() else 0

                # Determine document type based on item name
                item_name = row_data[1].lower()
                is_official = "رسمی" in item_name or "official" in item_name

                # Update summary
                if is_official:
                    summary.total_official_docs_count += quantity
                else:
                    summary.total_unofficial_docs_count += quantity

                summary.total_pages_count += quantity
                summary.total_judiciary_count += judiciary_count
                summary.total_foreign_affairs_count += foreign_affairs_count
                summary.total_translation_price += item_price

            except (ValueError, IndexError):
                continue  # Skip rows with invalid data

        return summary

    def calculate_pagination_config(self, total_rows: int, scale_config: ScaleConfig) -> PaginationConfig:
        """Calculate pagination configuration based on data size and scale."""
        config = PaginationConfig(
            total_rows=total_rows,
            first_page_rows=scale_config.first_page_rows,
            last_page_rows=scale_config.last_page_rows,
            first_table_rows=scale_config.first_table_rows,
            other_page_rows=scale_config.other_page_rows
        )

        # Calculate total pages
        if total_rows <= config.first_table_rows:
            config.total_pages = 1
        elif config.first_table_rows < total_rows <= config.first_page_rows:
            config.total_pages = 2
        elif total_rows <= config.first_page_rows + config.last_page_rows:
            config.total_pages = 2
        else:
            remaining_rows = total_rows - config.first_page_rows
            middle_pages = remaining_rows // config.other_page_rows
            last_page_rows = remaining_rows % config.other_page_rows

            if last_page_rows > config.last_page_rows:
                middle_pages += 1

            config.total_pages = 2 + middle_pages

        return config

    def get_page_data(self, table_data: List[List[str]], page: int,
                      pagination_config: PaginationConfig) -> Tuple[int, int]:
        """Get start and end indices for current page data."""
        total_rows = len(table_data)
        total_pages = pagination_config.total_pages

        if page == 1:
            return 0, min(total_rows, pagination_config.first_page_rows)
        elif page == total_pages:
            start_index = pagination_config.first_page_rows + (page - 2) * pagination_config.other_page_rows
            return start_index, total_rows
        else:
            start_index = pagination_config.first_page_rows + (page - 2) * pagination_config.other_page_rows
            end_index = min(start_index + pagination_config.other_page_rows, total_rows)
            return start_index, end_index

    def calculate_amounts(self, base_amount: int, advance_payment: int = 0,
                          discount_amount: int = 0) -> Dict[str, int]:
        """Calculate various amounts for the invoice."""
        final_amount = max(0, base_amount - advance_payment - discount_amount)

        return {
            'base_amount': base_amount,
            'advance_payment': advance_payment,
            'discount_amount': discount_amount,
            'final_amount': final_amount
        }

    def apply_discount(self, base_amount: int, discount_percentage: int) -> int:
        """Apply percentage discount to base amount."""
        if not (1 <= discount_percentage <= 100):
            raise ValueError("Discount percentage must be between 1 and 100")

        return int((discount_percentage / 100) * base_amount)

    def validate_advance_payment(self, advance_payment: int, total_amount: int) -> bool:
        """Validate that advance payment doesn't exceed total amount."""
        return 0 <= advance_payment <= total_amount

    def format_currency(self, amount: int) -> str:
        """Format currency amount with Persian numbers and separators."""
        formatted = f"{amount:,}"
        # Convert to Persian numbers
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'

        for eng, per in zip(english_digits, persian_digits):
            formatted = formatted.replace(eng, per)

        return f"{formatted} تومان"

    def parse_currency_text(self, currency_text: str) -> int:
        """Parse currency text and return integer amount."""
        # Remove "تومان" and extra spaces
        clean_text = currency_text.replace("تومان", "").strip()

        # Convert Persian digits to English
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'

        for per, eng in zip(persian_digits, english_digits):
            clean_text = clean_text.replace(per, eng)

        # Remove all non-digit characters except commas
        clean_text = re.sub(r"[^\d,]", "", clean_text)
        clean_text = clean_text.replace(",", "")

        try:
            return int(clean_text) if clean_text else 0
        except ValueError:
            return 0

    def create_invoice_data(self, invoice_number: int, customer_name: str, national_id: str,
                            phone: str, issue_date: date, translator: str, username: str,
                            table_data: List[List[str]], delivery_date: Optional[date] = None,
                            advance_payment: int = 0, discount_amount: int = 0,
                            source_language: str = None, target_language: str = None,
                            remarks: str = None) -> InvoiceData:
        """Create complete invoice data structure."""

        # Calculate total amount from table data
        total_amount = self._calculate_total_from_table_data(table_data)

        # Calculate summary
        summary = self.calculate_invoice_summary(table_data)

        # Calculate final amount
        final_amount = max(0, total_amount - advance_payment - discount_amount)

        # Create invoice items
        items = self._create_invoice_items_from_table_data(table_data)

        return InvoiceData(
            invoice_number=invoice_number,
            customer_name=customer_name,
            national_id=national_id,
            phone=phone,
            issue_date=issue_date,
            delivery_date=delivery_date,
            translator=translator,
            total_amount=total_amount,
            advance_payment=advance_payment,
            discount_amount=discount_amount,
            final_amount=final_amount,
            source_language=source_language,
            target_language=target_language,
            remarks=remarks,
            username=username,
            items=items,
            summary=summary
        )

    def _calculate_total_from_table_data(self, table_data: List[List[str]]) -> int:
        """Calculate total amount from table data."""
        total = 0
        for row_data in table_data:
            if len(row_data) > 5:  # Assuming price is in column 5
                try:
                    price_str = row_data[5].replace(",", "")
                    if price_str.strip():
                        total += int(price_str)
                except (ValueError, IndexError):
                    continue
        return total

    def _create_invoice_items_from_table_data(self, table_data: List[List[str]]) -> List[InvoiceItem]:
        """Create invoice items from table data."""
        items = []
        for row_data in table_data:
            if len(row_data) > 1 and row_data[1].strip():
                try:
                    item = InvoiceItem(
                        item_name=row_data[1],
                        item_qty=int(row_data[2]) if len(row_data) > 2 and row_data[2].strip() else 1,
                        item_price=int(row_data[5].replace(",", "")) if len(row_data) > 5 and row_data[
                            5].strip() else 0,
                        officiality=1 if "رسمی" in row_data[1].lower() else 0,
                        judiciary_seal=int(row_data[3]) if len(row_data) > 3 and row_data[3].strip() else 0,
                        foreign_affairs_seal=int(row_data[4]) if len(row_data) > 4 and row_data[4].strip() else 0
                    )
                    items.append(item)
                except (ValueError, IndexError):
                    continue
        return items

    def save_invoice(self, invoice_data: InvoiceData, table_data: List[List[str]]) -> bool:
        """Save invoice using repository."""
        return self.repository.save_invoice(invoice_data, table_data)

    def load_invoice(self, invoice_number: int) -> Optional[InvoiceData]:
        """Load invoice using repository."""
        return self.repository.load_invoice(invoice_number)

    def delete_invoice(self, invoice_number: int) -> bool:
        """Delete invoice using repository."""
        return self.repository.delete_invoice(invoice_number)

    def get_user_invoices(self, username: str) -> List[Dict[str, Any]]:
        """Get all invoices for a user."""
        return self.repository.get_all_invoices_for_user(username)

    def get_invoice_statistics(self, username: str) -> InvoiceStatistics:
        """Get invoice statistics for a user."""
        return self.repository.get_invoice_statistics(username)

    def update_invoice_status(self, invoice_number: int, payment_status: int = None,
                              delivery_status: int = None) -> bool:
        """Update invoice status."""
        return self.repository.update_invoice_status(invoice_number, payment_status, delivery_status)

    def prepare_export_data(self, invoices: List[Dict[str, Any]]) -> List[InvoiceExportData]:
        """Prepare invoice data for export."""
        export_data = []

        for inv in invoices:
            export_item = InvoiceExportData(
                invoice_number=str(inv.get('invoice_number', '')),
                customer_name=inv.get('customer_name', ''),
                national_id=inv.get('national_id', ''),
                phone=inv.get('phone', ''),
                issue_date=str(inv.get('issue_date', '')),
                delivery_date=str(inv.get('delivery_date', '')),
                translator=inv.get('translator', ''),
                total_official_docs_count=inv.get('total_official_docs_count', 0),
                total_unofficial_docs_count=inv.get('total_unofficial_docs_count', 0),
                total_pages_count=inv.get('total_pages_count', 0),
                total_judiciary_count=inv.get('total_judiciary_count', 0),
                total_foreign_affairs_count=inv.get('total_foreign_affairs_count', 0),
                total_additional_doc_count=inv.get('total_additional_doc_count', 0),
                total_translation_price=float(inv.get('total_translation_price', 0)),
                total_amount=float(inv.get('total_amount', 0)),
                advance_payment=float(inv.get('advance_payment', 0)),
                discount_amount=float(inv.get('discount_amount', 0)),
                final_amount=float(inv.get('final_amount', 0)),
                language=inv.get('language', ''),
                invoice_status='نهایی' if inv.get('payment_status') == 1 else 'پیش‌نویس'
            )
            export_data.append(export_item)

        return export_data

    def validate_invoice_data(self, invoice_data: InvoiceData) -> List[str]:
        """Validate invoice data and return list of errors."""
        errors = []

        if not invoice_data.customer_name.strip():
            errors.append("نام مشتری الزامی است")

        if not invoice_data.national_id.strip():
            errors.append("کد ملی الزامی است")

        if not invoice_data.phone.strip():
            errors.append("شماره تلفن الزامی است")

        if invoice_data.total_amount <= 0:
            errors.append("مبلغ کل باید بیشتر از صفر باشد")

        if invoice_data.advance_payment > invoice_data.total_amount:
            errors.append("مبلغ بیعانه نمی‌تواند بیشتر از مبلغ کل باشد")

        if invoice_data.discount_amount > invoice_data.total_amount:
            errors.append("مبلغ تخفیف نمی‌تواند بیشتر از مبلغ کل باشد")

        if not invoice_data.items:
            errors.append("حداقل یک آیتم در فاکتور الزامی است")

        return errors

    def get_translation_office_info(self) -> Dict[str, str]:
        """Get translation office information."""
        office_data = self.repository.get_translation_office_data()

        if office_data:
            return {
                'name': office_data.get('name', 'دارالترجمه'),
                'reg_no': office_data.get('reg_no', ''),
                'address': office_data.get('address', ''),
                'phone': office_data.get('phone', ''),
                'website': office_data.get('website', ''),
                'representative': office_data.get('representative', ''),
                'manager': office_data.get('manager', '')
            }

        # Default values if no data in database
        return {
            'name': 'دارالترجمه زارعی',
            'reg_no': '۶۶۳',
            'address': 'اصفهان، خ هزار جریب، حد فاصل کوچه هشتم و دهم، ساختمان ۱۱۶',
            'phone': '۰۳۱۳۶۶۹۱۳۷۹',
            'website': 'translator663@gmail.com',
            'representative': '',
            'manager': ''
        }

    def get_user_display_name(self, username: str) -> str:
        """Get user's display name from profile."""
        profile = self.repository.get_user_profile(username)
        return profile.get('full_name', username) if profile else username

    def generate_invoice_filename(self, invoice_data: InvoiceData, file_extension: str) -> str:
        """Generate appropriate filename for invoice."""
        safe_customer_name = re.sub(r'[^\w\s-]', '', invoice_data.customer_name)
        safe_customer_name = re.sub(r'[-\s]+', '-', safe_customer_name)

        filename = f"invoice_{invoice_data.invoice_number}_{safe_customer_name}"
        return f"{filename}.{file_extension.lstrip('.')}"

    def calculate_page_visibility(self, current_page: int, total_pages: int) -> Dict[str, bool]:
        """Calculate which UI elements should be visible on current page."""
        return {
            'show_header': current_page == 1,
            'show_customer_info': current_page == 1,
            'show_footer': current_page == total_pages,
            'show_pagination': total_pages > 1,
            'show_price_summary': current_page == total_pages
        }

    @contextmanager
    def temporary_page_state(self, current_page: int, target_page: int):
        """Context manager for temporarily changing page state."""
        original_page = current_page
        try:
            current_page = target_page
            yield current_page
        finally:
            current_page = original_page
