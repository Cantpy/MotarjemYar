"""
Business logic layer for home page functionality.
Contains all the business rules and data processing logic.
"""
import jdatetime
from typing import List, Tuple, Optional
from datetime import date, timedelta

from features.Home.models import (
    DashboardStats, TimeInfo, InvoiceTableRow, Invoice, DocumentStatistics
)
from features.Home.repo import HomePageRepository, InvoiceModel
from shared import to_persian_number


class HomePageLogic:
    """Business logic for home page operations."""

    def __init__(self, repository: HomePageRepository):
        """Initialize with repository dependency."""
        self.repository = repository

    def get_current_time_info(self) -> TimeInfo:
        """Get current time and date information in Persian format."""
        from PySide6.QtCore import QTime

        # Get current time
        current_time = QTime.currentTime().toString("HH:mm:ss")
        persian_time = to_persian_number(current_time)

        # Get Persian date
        jalali_date = jdatetime.date.today()
        persian_date = self._format_persian_date(jalali_date)

        return TimeInfo(
            time_string=persian_time,
            date_string=persian_date,
            jalali_date=jalali_date
        )

    def get_dashboard_statistics(self) -> DashboardStats:
        """Get all dashboard statistics."""
        # Get customer count
        total_customers = self.repository.get_customer_count()

        # Get invoice counts
        total_invoices = self.repository.get_total_invoices_count()

        # Get today's invoices
        today_jalali = jdatetime.date.today().strftime("%Y/%m/%d")
        persian_today = to_persian_number(today_jalali)
        today_invoices = self.repository.get_today_invoices_count(persian_today)

        # Get document statistics
        doc_stats = self.repository.get_document_statistics()
        dashboard_stats = self.repository.get_dashboard_stats(today_jalali)
        print("most repeated doc: ", dashboard_stats.most_repeated_document)
        print("most repeated doc in month: ", dashboard_stats.most_repeated_document_month)

        return DashboardStats(
            total_customers=total_customers,
            total_invoices=total_invoices,
            today_invoices=today_invoices,
            total_documents=doc_stats.total_documents,
            available_documents=doc_stats.in_office_documents,
            most_repeated_document=dashboard_stats.most_repeated_document,
            most_repeated_document_month=dashboard_stats.most_repeated_document_month
        )

    def get_invoice_table_data(self, limit: int = 20) -> List[InvoiceTableRow]:
        """Get invoice data for table display, filtered and sorted."""
        # Get all invoices
        invoices = self.repository.get_invoices_for_table()

        # Filter and sort
        filtered_invoices = self._filter_and_sort_invoices(invoices)

        # Convert to table rows
        table_rows = []
        today = jdatetime.date.today().togregorian()

        for invoice in filtered_invoices[:limit]:
            delivery_date = self._parse_jalali_date(invoice.delivery_date)
            if delivery_date:
                row_color = self._get_row_color(delivery_date, today)

                table_row = InvoiceTableRow(
                    invoice_number=invoice.invoice_number,
                    name=invoice.name,
                    phone=invoice.phone,
                    delivery_date=invoice.delivery_date,
                    translator=invoice.translator,
                    pdf_file_path=invoice.pdf_file_path,
                    delivery_status=invoice.delivery_status,
                    delivery_date_obj=delivery_date,
                    row_color=row_color
                )
                table_rows.append(table_row)

        return table_rows

    def mark_invoice_delivered(self, invoice_number: str) -> bool:
        """Mark an invoice as delivered."""
        return self.repository.mark_invoice_as_delivered(invoice_number)

    def get_invoice_for_notification(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice data for notification purposes."""
        return self.repository.get_invoice_by_number(invoice_number)

    def get_recent_invoices_with_priority(self, days_threshold: int = 7) -> List[Tuple[InvoiceModel, str]]:
        """
        Get recent invoices within the specified threshold with priority labels.

        Args:
            days_threshold: Number of days to look ahead for upcoming deliveries

        Returns:
            List of tuples containing (invoice, priority_label)
        """
        today = date.today()
        threshold_date = today - timedelta(days=days_threshold)

        # Get invoices from repository with delivery dates within the threshold
        invoices = self.repository.get_invoices_by_delivery_date_range(
            start_date=threshold_date,
            end_date=today,
            exclude_completed=True
        )
        invoice_priority_list = []

        for invoice in invoices:
            priority = self._calculate_priority(invoice.delivery_date, today)
            invoice_priority_list.append((invoice, priority))

        # Sort by delivery date ascending
        invoice_priority_list.sort(key=lambda x: x[0].delivery_date)

        return invoice_priority_list

    @staticmethod
    def _calculate_priority(delivery_date: date, today: date) -> str:
        """
        Calculate priority based on delivery date.

        Args:
            delivery_date: The delivery date of the invoice
            today: Current date

        Returns:
            Priority string: 'urgent', 'needs_attention', or 'normal'
        """
        days_until_delivery = (delivery_date - today).days

        if days_until_delivery <= 0:  # Today or past due
            return 'urgent'
        elif days_until_delivery <= 3:  # 3 days or less
            return 'needs_attention'
        else:
            return 'normal'

    @staticmethod
    def _format_persian_date(jalali_date: jdatetime.date) -> str:
        """Format Persian date with day name and month name."""
        persian_weekdays = {
            "Saturday": "شنبه", "Sunday": "یکشنبه", "Monday": "دوشنبه",
            "Tuesday": "سه‌شنبه", "Wednesday": "چهارشنبه",
            "Thursday": "پنج‌شنبه", "Friday": "جمعه"
        }

        persian_months = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
            5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
            9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند"
        }

        weekday = persian_weekdays[jalali_date.strftime("%A")]
        month = persian_months[jalali_date.month]

        return (f"{weekday}، {to_persian_number(jalali_date.day)} "
                f"{month} {to_persian_number(jalali_date.year)}")

    def _filter_and_sort_invoices(self, invoices: List[Invoice]) -> List[Invoice]:
        """Filter out invalid dates and sort by delivery date."""
        today = jdatetime.date.today().togregorian()
        valid_invoices = []

        for invoice in invoices:
            delivery_date_str = invoice.delivery_date.strip()

            if delivery_date_str == "نامشخص":
                continue

            delivery_date = self._parse_jalali_date(delivery_date_str)
            if delivery_date:
                valid_invoices.append(invoice)

        # Sort by delivery date (overdue first)
        return sorted(valid_invoices,
                      key=lambda inv: self._parse_jalali_date(inv.delivery_date) or date.max)

    def _parse_jalali_date(self, date_str: str) -> Optional[date]:
        """Parse Persian date string to date object."""
        try:
            # Remove Persian numbers and convert to English
            english_date = date_str
            persian_to_english = {
                '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
            }

            for persian, english in persian_to_english.items():
                english_date = english_date.replace(persian, english)

            # Parse date in format YYYY/MM/DD
            parts = english_date.split('/')
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                jalali_date = jdatetime.date(year, month, day)
                return jalali_date.togregorian()

            return None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _get_row_color(delivery_date: date, today: date) -> str:
        """Determine row color based on delivery date urgency."""
        days_diff = (delivery_date - today).days

        if days_diff <= 0:
            return "red"  # Overdue
        elif days_diff <= 2:
            return "yellow"  # Soon
        else:
            return "white"  # Normal

    def validate_delivery_confirmation(self, invoice_number: str) -> bool:
        """Validate that invoice can be marked as delivered."""
        invoice = self.repository.get_invoice_by_number(invoice_number)
        return invoice is not None and invoice.delivery_status == 0

    def calculate_document_statistics(self) -> DocumentStatistics:
        """Calculate comprehensive document statistics."""
        return self.repository.get_document_statistics()
