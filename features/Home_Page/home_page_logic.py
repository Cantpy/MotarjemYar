# home_page/_logic.py

import jdatetime
from datetime import date, timedelta
from typing import List, Optional, Tuple
import requests

# Import the stateless _repository and the DTOs
from features.Home_Page.home_page_repo import HomePageRepository
from features.Home_Page.home_page_models import TimeInfo, DashboardStats, StatusChangeRequest
from shared.dtos.notification_dialog_dtos import NotificationDataDTO, SmsRequestDTO, EmailRequestDTO
from shared.dtos.invoice_dtos import IssuedInvoiceDTO
from shared.orm_models.invoices_models import IssuedInvoiceModel
from shared.utils.persian_tools import to_persian_numbers
from shared.enums import DeliveryStatus
from shared.session_provider import ManagedSessionProvider


class HomePageLogic:
    """Business _logic for home page operations. Manages units of work."""

    def __init__(self, repository: HomePageRepository,
                 customer_engine: ManagedSessionProvider,
                 invoices_engine: ManagedSessionProvider):
        """Initialize with _repository class and session makers."""
        self._repository = repository
        self._customer_session = customer_engine
        self._invoices_session = invoices_engine

    # --- PUBLIC METHODS ---

    def get_dashboard_statistics(self) -> DashboardStats:
        """Get all dashboard statistics. This is a read-only unit of work."""
        total_customers = 0
        with self._customer_session() as customer_session:
            total_customers = self._repository.get_customer_count(customer_session)

        # REFACTORED: Get the session from the provider
        with self._invoices_session() as invoice_session:
            total_invoices = self._repository.get_total_invoices_count(invoice_session)
            today_invoices = self._repository.get_today_invoices_count(invoice_session, date.today())
            doc_stats = self._repository.get_document_statistics(invoice_session)
            most_repeated_raw = self._repository.get_most_repeated_doc(invoice_session)
            most_repeated_month_raw = self._repository.get_most_repeated_doc_month(invoice_session)
            most_repeated_formatted = self._format_most_repeated_doc(most_repeated_raw)
            most_repeated_month_formatted = self._format_most_repeated_doc_month(most_repeated_month_raw)

        return DashboardStats(
            total_customers=total_customers,
            total_invoices=total_invoices,
            today_invoices=today_invoices,
            total_documents=doc_stats.total_documents,
            available_documents=doc_stats.in_office_documents,
            most_repeated_document=most_repeated_formatted,
            most_repeated_document_month=most_repeated_month_formatted
        )

    def get_recent_invoices_with_priority(self, days_threshold: int = 7) -> List[Tuple[IssuedInvoiceDTO, str]]:
        """
        Get recent invoices with priority labels.
        This business _logic does not belong in the _repository.
        """
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)

        invoice_priority_list = []
        with self._invoices_session() as session:
            invoice_models = self._repository.get_invoices_by_delivery_date_range(
                session,
                start_date=today,
                end_date=threshold_date,
                exclude_completed=True
            )

            for model in invoice_models:
                priority = self._calculate_priority(model.delivery_date, today)
                # Convert ORM Model to DTO for the layer above
                invoice_dto = self._map_orm_to_invoice_dto(model)
                invoice_priority_list.append((invoice_dto, priority))

        # Sorting is business _logic
        invoice_priority_list.sort(key=lambda x: x[0].delivery_date)
        return invoice_priority_list

    def get_data_for_notification(self, invoice_number: int) -> Optional[NotificationDataDTO]:
        """
        Gathers the necessary customer and invoice data required for sending a notification.
        This is a read-only unit of work that may span multiple databases.
        """
        # We need data from two different databases, so we'll use two sessions.
        with self._invoices_session() as invoice_session:
            invoice_model = self._repository.get_invoice_by_number(invoice_session, invoice_number)

        if not invoice_model:
            # If the invoice doesn't exist, we can't proceed.
            return None

        customer_model = None
        if invoice_model.national_id:
            national_id = str(invoice_model.national_id)
            with self._customer_session() as customer_session:
                customer_model = self._repository.get_customer_by_national_id(customer_session,
                                                                              national_id)

        # Now, map the data from our ORM models into the clean DTO.
        # Prioritize the data from the official customer record, but fall back
        # to the data stored on the invoice if necessary. This is business _logic!
        customer_name = customer_model.name if customer_model else invoice_model.name
        customer_phone = customer_model.phone if customer_model else invoice_model.phone
        customer_email = customer_model.email if customer_model else None

        return NotificationDataDTO(
            invoice_number=invoice_model.invoice_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email
        )

    def change_invoice_status(self, request: StatusChangeRequest) -> Tuple[bool, str]:
        """
        Handles all business _logic for changing an invoice's status.
        This is a single, consolidated transactional unit of work.
        """
        with self._invoices_session() as session:
            try:
                invoice = self._repository.get_invoice_by_number(session, request.invoice_number)
                if not invoice:
                    return False, "فاکتور یافت نشد"

                # === Business Rules Validation (all in one place) ===
                if invoice.delivery_status >= DeliveryStatus.COLLECTED:
                    return False, "فاکتور در آخرین مرحله قرار دارد"
                if request.target_status != invoice.delivery_status + 1:
                    return False, "تنها می‌توانید یک مرحله جلوتر بروید"
                if request.target_status == DeliveryStatus.ASSIGNED and not request.translator:
                    # Specific rule for this step
                    return False, "برای این مرحله تعیین مترجم الزامی است."

                # === Update the record ===
                success = self._repository.update_invoice_status(
                    session, request.invoice_number, request.target_status, request.translator
                )

                if success:
                    session.commit()
                    return True, "وضعیت با موفقیت تغییر کرد."
                else:
                    session.rollback()
                    return False, "خطا در به‌روزرسانی پایگاه داده"
            except Exception as e:
                session.rollback()
                return False, f"خطای سیستمی: {str(e)}"

    def get_invoice_for_menu(self, invoice_number: int) -> Optional[IssuedInvoiceDTO]:
        """Gets the necessary invoice data (as a DTO) for creating a context menu."""
        with self._invoices_session() as session:
            invoice_model = self._repository.get_invoice_by_number(session, invoice_number)
            if invoice_model:
                return self._map_orm_to_invoice_dto(invoice_model)
            return None

    def get_current_time_info(self) -> TimeInfo:
        """Get current time and date information in Persian format."""
        from PySide6.QtCore import QTime

        # Get current time
        current_time = QTime.currentTime().toString("HH:mm:ss")
        persian_time = to_persian_numbers(current_time)

        # Get Persian date
        jalali_date = jdatetime.date.today()
        persian_date = self._format_persian_date(jalali_date)

        return TimeInfo(
            time_string=persian_time,
            date_string=persian_date,
            jalali_date=jalali_date
        )

    # --- PRIVATE HELPER METHODS ---
    @staticmethod
    def _calculate_priority(delivery_date: date, today: date) -> str:
        days_until_delivery = (delivery_date - today).days
        if days_until_delivery <= 0: return 'urgent'
        if days_until_delivery <= 3: return 'needs_attention'
        return 'normal'

    @staticmethod
    def _format_most_repeated_doc(raw_data: Optional[Tuple[str, int]]) -> Optional[str]:
        if not raw_data:
            return None
        name, total_qty = raw_data
        # Formatting and conversion _logic lives here!
        return f"{name} - {to_persian_numbers(total_qty)}"

    @staticmethod
    def _format_most_repeated_doc_month(raw_data: Optional[Tuple[str, int, int, int]]) -> Optional[str]:
        if not raw_data:
            return None

        name, year, month, total_qty = raw_data

        persian_month_names = {1: "فروردین",
                               2: "اردیبهشت",
                               3: "خرداد",
                               4: "تیر",
                               5: "مرداد",
                               6: "شهریور",
                               7: "مهر",
                               8: "آبان",
                               9: "آذر",
                               10: "دی",
                               11: "بهمن",
                               12: "اسفند"}

        try:
            # Date and number conversion _logic lives here!
            g_date = jdatetime.date.fromgregorian(year=int(year), month=int(month), day=1)
            persian_month = persian_month_names.get(g_date.month, "")
            persian_year = to_persian_numbers(g_date.year)
            persian_total_qty = to_persian_numbers(total_qty)

            return f"{name} - {persian_month} {persian_year} - {persian_total_qty}"
        except (ValueError, TypeError):
            # Gracefully handle potential errors during conversion
            return f"{name} (Data Error)"

    @staticmethod
    def _map_orm_to_invoice_dto(orm_invoice: IssuedInvoiceModel) -> IssuedInvoiceDTO:
        """Maps an SQLAlchemy ORM object to a plain DTO."""
        return IssuedInvoiceDTO(
            invoice_number=orm_invoice.invoice_number,
            name=orm_invoice.name,
            national_id=orm_invoice.national_id,
            phone=orm_invoice.phone,
            issue_date=orm_invoice.issue_date,
            delivery_date=orm_invoice.delivery_date,
            translator=orm_invoice.translator,
            total_items=orm_invoice.total_items,
            total_amount=orm_invoice.total_amount,
            total_translation_price=orm_invoice.total_translation_price,
            advance_payment=orm_invoice.advance_payment,
            discount_amount=orm_invoice.discount_amount,
            force_majeure=orm_invoice.force_majeure,
            final_amount=orm_invoice.final_amount,
            payment_status=orm_invoice.payment_status,
            delivery_status=orm_invoice.delivery_status,
            username=orm_invoice.username,
            pdf_file_path=orm_invoice.pdf_file_path,
        )

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

        return (f"{weekday}، {to_persian_numbers(jalali_date.day)} "
                f"{month} {to_persian_numbers(jalali_date.year)}")

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

    def get_available_next_step(self, invoice_number: int) -> Optional[Tuple[DeliveryStatus, str]]:
        """
        Determines the next valid step in the invoice lifecycle based on business rules.

        Args:
            invoice_number: The ID of the invoice to check.

        Returns:
            A tuple of (next_status_enum, next_step_button_text) if an advance is possible.
            None if the invoice is not found or is already in the final state.
        """
        with self._invoices_session() as session:
            invoice = self._repository.get_invoice_by_number(session, invoice_number)
            if not invoice:
                return None

            # The business _logic from the old `can_advance` method is now here.
            # Note how readable this is with the Enum!
            if invoice.delivery_status >= DeliveryStatus.COLLECTED:
                return None

            # The business _logic from `get_next_step_text` is now here.
            current_status = DeliveryStatus(invoice.delivery_status)  # Cast int to Enum
            next_step_map = {
                DeliveryStatus.ISSUED: "تعیین مترجم",
                DeliveryStatus.ASSIGNED: "تأیید ترجمه",
                DeliveryStatus.TRANSLATED: "آماده تحویل",
                DeliveryStatus.READY: "تحویل به مشتری"
            }

            # Determine the next status
            next_status = DeliveryStatus(current_status + 1)
            next_step_text = next_step_map.get(current_status, "")

            return next_status, next_step_text

    def send_sms_notification(self, sms_request: SmsRequestDTO) -> Tuple[bool, str]:
        """
        Handles the business _logic of sending an SMS via an external API.
        """
        try:
            url = 'https://console.melipayamak.com/api/send/simple/...'  # Your API key
            data = {'from': '...', 'to': sms_request.recipient_phone, 'text': sms_request.message}
            response = requests.post(url, json=data)

            if response.status_code == 200:
                return True, "پیامک با موفقیت ارسال شد."
            else:
                return False, f"ارسال پیامک با شکست مواجه شد: {response.text}"
        except Exception as e:
            return False, f"خطای سیستمی هنگام ارسال پیامک: {str(e)}"

    def send_email_notification(self, email_request: EmailRequestDTO, national_id: str) -> Tuple[bool, str]:
        """
        Handles the business _logic of sending an email and updating customer info.
        """
        # Business Rule: Update the customer's email if it has changed.
        with self._customer_session() as session:
            try:
                customer = self._repository.get_customer_by_national_id(session, national_id)
                if customer and customer.email != email_request.recipient_email:
                    self._repository.update_customer_email(session, national_id, email_request.recipient_email)
                    session.commit()
            except Exception as e:
                session.rollback()
                return False, f"خطا در به‌روزرسانی ایمیل مشتری: {e}"

        # Actual email sending _logic would go here.
        # For now, we simulate success.
        print(
            f"Simulating email send to {email_request.recipient_email} with {len(email_request.attachments)} attachments.")
        return True, "ایمیل با موفقیت ارسال شد (شبیه‌سازی)."
