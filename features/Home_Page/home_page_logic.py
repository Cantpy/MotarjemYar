# features/Home_Page/home_page_logic.py

import jdatetime
from datetime import date, timedelta, datetime
from typing import Optional, Tuple
import requests

from features.Home_Page.home_page_repo import HomePageRepository
from features.Home_Page.home_page_models import TimeInfo, DashboardStats, StatusChangeRequest, InvoiceDTO, CustomerDTO

from shared.dtos.notification_dialog_dtos import NotificationDataDTO, SmsRequestDTO, EmailRequestDTO
from shared.orm_models.invoices_models import IssuedInvoiceModel

from shared.utils.persian_tools import to_persian_numbers
from shared.enums import DeliveryStatus
from shared.session_provider import ManagedSessionProvider


class HomePageLogic:
    """Business _logic for home page operations. Manages units of work."""

    def __init__(self, repository: HomePageRepository,
                 customer_engine: ManagedSessionProvider,
                 invoices_engine: ManagedSessionProvider,
                 services_engine: ManagedSessionProvider):
        """Initialize with _repository class and session makers."""
        self._repository = repository
        self._customer_session = customer_engine
        self._invoices_session = invoices_engine
        self._services_session = services_engine

    # --- PUBLIC METHODS ---

    def get_dashboard_statistics(self) -> DashboardStats:
        """Get all dashboard statistics. This is an orchestrating unit of work."""
        total_customers = 0
        with self._customer_session() as customer_session:
            total_customers = self._repository.customers_repo.get_total_count(customer_session)

        # --- THIS IS THE CORE CHANGE ---
        most_repeated_name = None
        most_repeated_month_name = None

        with self._invoices_session() as invoice_session:
            # 1. Get raw data (with IDs) from the invoices DB
            total_invoices = self._repository.invoices_repo.get_total_count(invoice_session)
            today_invoices = self._repository.invoices_repo.get_today_count(invoice_session, date.today())
            doc_stats = self._repository.invoices_repo.get_document_statistics(invoice_session)
            most_repeated_raw = self._repository.invoices_repo.get_most_repeated_doc(invoice_session)
            most_repeated_month_raw = self._repository.invoices_repo.get_most_repeated_doc_month(invoice_session)

        # 2. If we found IDs, use the services DB to get the names
        if most_repeated_raw:
            service_id, total_qty = most_repeated_raw
            with self._services_session() as services_session:
                service_name = self._repository.services_repo.get_name_by_id(services_session, service_id)
                if service_name:
                    # Pass a tuple with the resolved NAME to the formatting function
                    most_repeated_name = self._format_most_repeated_doc((service_name, total_qty))

        if most_repeated_month_raw:
            service_id, year, month, total_qty = most_repeated_month_raw
            with self._services_session() as services_session:
                service_name = self._repository.services_repo.get_name_by_id(services_session, service_id)
                if service_name:
                    # Pass a tuple with the resolved NAME to the formatting function
                    most_repeated_month_name = self._format_most_repeated_doc_month(
                        (service_name, year, month, total_qty))

        default_display_value = ("نامشخص", "")

        return DashboardStats(
            total_customers=total_customers,
            total_invoices=total_invoices,
            today_invoices=today_invoices,
            total_documents=doc_stats.total_documents,
            available_documents=doc_stats.in_office_documents,
            most_repeated_document=most_repeated_name or default_display_value,
            most_repeated_document_month=most_repeated_month_name or default_display_value
        )

    def get_recent_invoices_with_priority(self, days_threshold: int) -> list[tuple[InvoiceDTO, str]]:
        """
        Retrieves recent invoices within the specified threshold and calculates their priority.
        Returns a list of tuples: (InvoiceDTO, priority_str)
        """
        today = date.today()
        threshold_date = today + timedelta(days=days_threshold)

        print(f'finding invoices between {today} to {threshold_date}')
        invoice_priority_list = []
        with self._invoices_session() as session:
            invoice_models = self._repository.invoices_repo.get_by_delivery_date_range(
                session,
                start_date=today,
                end_date=threshold_date,
                exclude_completed=True
            )
            print(f'found {len(invoice_models)} invoice(s)')

            for model in invoice_models:
                delivery_date = self.normalize_date(model.delivery_date)
                priority = self._calculate_priority(delivery_date, date.today())
                print(f'Invoice {model.invoice_number} with delivery {delivery_date} is {priority}')
                invoice_dto = self.map_orm_to_invoice_dto(model)
                invoice_priority_list.append((invoice_dto, priority))

        # Sorting is business _logic
        invoice_priority_list.sort(key=lambda x: x[0].delivery_date)
        return invoice_priority_list

    def get_data_for_notification(self, invoice_number: str) -> Optional[NotificationDataDTO]:
        with self._invoices_session() as invoice_session:
            invoice_model = self._repository.invoices_repo.get_by_number(invoice_session, invoice_number)

            if not invoice_model:
                raise Exception("اطلاعات فاکتور برای ارسال یافت نشد")

            invoice_name = invoice_model.name
            invoice_national_id = str(invoice_model.national_id)
            invoice_phone = invoice_model.phone
            invoice_number_value = invoice_model.invoice_number

        print(f'found invoice for {invoice_name}, national id: {invoice_national_id}')

        # Now safely open second session
        customer_data = None
        if invoice_national_id:
            with self._customer_session() as customer_session:
                customer_model = self._repository.customers_repo.get_by_national_id(customer_session,
                                                                                    invoice_national_id)
                if customer_model:
                    customer_data = {
                        "name": customer_model.name,
                        "phone": customer_model.phone,
                        "email": customer_model.email,
                        "national_id": customer_model.national_id
                    }

        if customer_data:
            customer_name = customer_data["name"]
            customer_phone = customer_data["phone"]
            customer_email = customer_data["email"]
            customer_national_id = customer_data["national_id"]
        else:
            customer_name = invoice_name
            customer_phone = invoice_phone
            customer_email = None
            customer_national_id = invoice_national_id

        return NotificationDataDTO(
            invoice_number=invoice_number_value,
            customer_name=customer_name,
            customer_national_id=customer_national_id,
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
                invoice = self._repository.invoices_repo.get_by_number(session, request.invoice_number)
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
                success = self._repository.invoices_repo.update_status(session,
                                                                       request.invoice_number,
                                                                       request.target_status,
                                                                       request.translator)

                if success:
                    session.commit()
                    return True, "وضعیت با موفقیت تغییر کرد."
                else:
                    session.rollback()
                    return False, "خطا در به‌روزرسانی پایگاه داده"
            except Exception as e:
                session.rollback()
                return False, f"خطای سیستمی: {str(e)}"

    def get_invoice_for_menu(self, invoice_number: str) -> Optional[InvoiceDTO]:
        """Gets the necessary invoice data (as a DTO) for creating a services menu."""
        with self._invoices_session() as session:
            invoice_model = self._repository.invoices_repo.get_by_number(session, invoice_number)
            if invoice_model:
                return self.map_orm_to_invoice_dto(invoice_model)
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

    def normalize_date(self, value):
        """Converts string, datetime, or date into a Python date object."""
        if isinstance(value, date) and not isinstance(value, datetime):
            # Already a date
            return value
        elif isinstance(value, datetime):
            # Convert datetime to date
            return value.date()
        elif isinstance(value, str):
            # Handle common formats
            try:
                # First try ISO format (handles "2025-10-12T09:00:00")
                return datetime.fromisoformat(value).date()
            except ValueError:
                # Try fallback format without 'T'
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()
                except ValueError:
                    # Final fallback: just date only
                    return datetime.strptime(value, "%Y-%m-%d").date()
        else:
            raise TypeError(f"Unsupported type for date normalization: {type(value)}")

    # --- PRIVATE HELPER METHODS ---
    @staticmethod
    def _calculate_priority(delivery_date: date, today: date) -> str:
        days_until_delivery = (delivery_date - today).days
        if days_until_delivery <= 0: return 'urgent'
        if days_until_delivery <= 3: return 'needs_attention'
        return 'normal'

    @staticmethod
    def _create_short_service_name(full_name: str, max_words: int = 2) -> str:
        """Creates a shorter, more readable summary of a service name."""
        words = full_name.split()
        if len(words) <= max_words:
            return full_name  # It's already short

        return " ".join(words[-max_words:])

    @staticmethod
    def _format_most_repeated_doc(data: Optional[Tuple[str, int]]) -> Optional[Tuple[str, str]]:
        """
        Formats the most repeated document data into a structured tuple for the view.
        Returns: (Primary Text, Secondary Text)
        """
        if not data:
            return None
        service_name, total_qty = data

        primary_text = service_name
        secondary_text = f"{to_persian_numbers(total_qty)} بار تکرار"

        return primary_text, secondary_text

    @staticmethod
    def _format_most_repeated_doc_month(data: Optional[Tuple[str, int, int, int]]) -> Optional[Tuple[str, str]]:
        """
        Formats the monthly most repeated document data into a structured tuple.
        Returns: (Primary Text, Secondary Text)
        """
        if not data:
            return None

        service_name, year, month, total_qty = data

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
            g_date = jdatetime.date.fromgregorian(year=int(year), month=int(month), day=1)
            persian_month = persian_month_names.get(g_date.month, "")
            persian_month = persian_month_names.get(g_date.month, "")
            persian_year = to_persian_numbers(g_date.year)
            persian_total_qty = to_persian_numbers(total_qty)

            primary_text = service_name
            secondary_text = f"{persian_month} {persian_year} - {persian_total_qty} بار"

            return primary_text, secondary_text
        except (ValueError, TypeError):
            error_text = f"{service_name} (Data Error)"
            return error_text, ""

    def map_orm_to_invoice_dto(self, orm: IssuedInvoiceModel) -> InvoiceDTO:
        """
        Maps the IssuedInvoiceModel ORM object to an InvoiceDTO.
        Handles datetime conversion for issue_date and delivery_date.
        """
        # Create the nested CustomerDTO
        customer_dto = CustomerDTO(
            name=orm.name,
            national_id=orm.national_id,
            phone=orm.phone
        )

        # Safely convert ORM datetimes to ISO format strings for DTO (if DTO expects strings)
        issue_date = orm.issue_date.isoformat() if isinstance(orm.issue_date, datetime) else str(orm.issue_date)
        delivery_date = orm.delivery_date.isoformat() if isinstance(orm.delivery_date, datetime) else str(
            orm.delivery_date)

        # Build the InvoiceDTO
        dto = InvoiceDTO(
            invoice_number=orm.invoice_number,
            issue_date=self.normalize_date(issue_date),
            delivery_date=self.normalize_date(delivery_date),
            username=orm.username or "",
            customer=customer_dto,
            source_language=orm.source_language,
            target_language=orm.target_language,
            translator=orm.translator or "",
            total_amount=orm.total_amount,
            discount_amount=orm.discount_amount,
            advance_payment=orm.advance_payment,
            emergency_cost=orm.emergency_cost,
            final_amount=orm.final_amount,
            payment_status=orm.payment_status,
            delivery_status=orm.delivery_status,
            remarks=orm.remarks or "",
            pdf_file_path=orm.pdf_file_path,
        )

        # The invoice items are typically populated elsewhere
        dto.items = []
        return dto

    @staticmethod
    def map_dto_to_orm(dto: InvoiceDTO) -> IssuedInvoiceModel:
        """
        Maps an InvoiceDTO back to the ORM model.
        Handles string → datetime conversion for issue_date and delivery_date.
        """

        # Convert strings to datetime if needed
        def parse_dt(value):
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    # Try parsing ISO 8601 or 'YYYY/MM/DD - HH:MM' style formats
                    return datetime.fromisoformat(value)
                except ValueError:
                    try:
                        return datetime.strptime(value, "%Y/%m/%d - %H:%M")
                    except ValueError:
                        return datetime.strptime(value, "%Y/%m/%d")
            raise TypeError(f"Unsupported datetime format: {value}")

        orm = IssuedInvoiceModel(
            invoice_number=dto.invoice_number,
            issue_date=parse_dt(dto.issue_date),
            delivery_date=parse_dt(dto.delivery_date),
            username=dto.username,
            name=dto.customer.name,
            national_id=dto.customer.national_id,
            phone=dto.customer.phone,
            source_language=dto.source_language,
            target_language=dto.target_language,
            total_amount=dto.total_amount,
            discount_amount=dto.discount_amount,
            advance_payment=dto.advance_payment,
            emergency_cost=dto.emergency_cost,
            final_amount=dto.payable_amount,
            payment_status=dto.payment_status or 0,
            delivery_status=dto.delivery_status or 0,
            remarks=dto.remarks,
            pdf_file_path=dto.pdf_file_path,
            total_items=len(dto.items),
            total_translation_price=sum(item.total_price for item in dto.items),
            translator=dto.translator or "",
        )
        return orm

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

    def get_available_next_step(self, invoice_number: str) -> Optional[Tuple[DeliveryStatus, str]]:
        """
        Determines the next valid step in the invoice lifecycle based on business rules.

        Args:
            invoice_number: The ID of the invoice to check.

        Returns:
            A tuple of (next_status_enum, next_step_button_text) if an advance is possible.
            None if the invoice is not found or is already in the final state.
        """
        with self._invoices_session() as session:
            invoice = self._repository.invoices_repo.get_by_number(session, invoice_number)
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
                customer = self._repository.customers_repo.get_by_national_id(session, national_id)
                if customer and customer.email != email_request.recipient_email:
                    self._repository.customers_repo.update_email(session, national_id, email_request.recipient_email)
                    session.commit()
            except Exception as e:
                session.rollback()
                return False, f"خطا در به‌روزرسانی ایمیل مشتری: {e}"

        # Actual email sending _logic would go here.
        # For now, we simulate success.
        print(
            f"Simulating email send to {email_request.recipient_email}"
            f"with {len(email_request.attachments)} attachments.")
        return True, "ایمیل با موفقیت ارسال شد (شبیه‌سازی)."
