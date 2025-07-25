"""
Controller for the Notification History widget.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget
from models import SMSNotification, EmailNotification, NotificationStatus, NotificationFilter
from logic import NotificationService
from repo import NotificationRepository


class NotificationController(QObject):
    """Controller for managing notification operations."""

    # Signals
    sms_data_changed = Signal()
    email_data_changed = Signal()
    loading_changed = Signal(bool)
    error_occurred = Signal(str)
    status_updated = Signal(str)  # For status bar updates

    def __init__(self, database_url: str = "sqlite:///notifications.db"):
        super().__init__()
        self.repository = NotificationRepository(database_url)
        self.service = NotificationService(self.repository)

        # Current data
        self.current_sms_list: List[SMSNotification] = []
        self.current_email_list: List[EmailNotification] = []
        self.current_sms_filter = NotificationFilter()
        self.current_email_filter = NotificationFilter()

        # Pagination
        self.sms_current_page = 1
        self.email_current_page = 1
        self.page_size = 50
        self.sms_total_count = 0
        self.email_total_count = 0

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Initial load
        self.load_initial_data()

    def load_initial_data(self):
        """Load initial data."""
        self.loading_changed.emit(True)
        try:
            self.refresh_sms_data()
            self.refresh_email_data()
            self.status_updated.emit("داده‌ها بارگذاری شدند")
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری داده‌ها: {str(e)}")
        finally:
            self.loading_changed.emit(False)

    # SMS Methods
    def refresh_sms_data(self):
        """Refresh SMS data with current filters."""
        try:
            self.current_sms_list, self.sms_total_count = self.service.get_sms_list(
                self.current_sms_filter,
                self.sms_current_page,
                self.page_size
            )
            self.sms_data_changed.emit()
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری پیامک‌ها: {str(e)}")

    def send_sms(self, recipient_name: str, recipient_phone: str, message: str) -> bool:
        """Send new SMS."""
        if not self.validate_phone(recipient_phone):
            self.error_occurred.emit("شماره تماس معتبر نیست")
            return False

        if not message.strip():
            self.error_occurred.emit("متن پیام نمی‌تواند خالی باشد")
            return False

        self.loading_changed.emit(True)
        try:
            sms = self.service.send_sms(recipient_name.strip(), recipient_phone.strip(), message.strip())
            self.refresh_sms_data()

            if sms.status == NotificationStatus.SENT:
                self.status_updated.emit(f"پیامک به {recipient_name} ارسال شد")
                return True
            else:
                self.error_occurred.emit(f"خطا در ارسال پیامک: {sms.error_message}")
                return False

        except Exception as e:
            self.error_occurred.emit(f"خطا در ارسال پیامک: {str(e)}")
            return False
        finally:
            self.loading_changed.emit(False)

    def filter_sms(self, search_text: str = "", status: Optional[NotificationStatus] = None,
                   date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
                   recipient_filter: str = ""):
        """Apply SMS filters."""
        self.current_sms_filter = NotificationFilter(
            search_text=search_text.strip(),
            status=status,
            date_from=date_from,
            date_to=date_to,
            recipient_filter=recipient_filter.strip()
        )
        self.sms_current_page = 1  # Reset to first page
        self.refresh_sms_data()

    def clear_sms_filters(self):
        """Clear all SMS filters."""
        self.current_sms_filter = NotificationFilter()
        self.sms_current_page = 1
        self.refresh_sms_data()

    def go_to_sms_page(self, page: int):
        """Navigate to specific SMS page."""
        max_pages = (self.sms_total_count + self.page_size - 1) // self.page_size
        if 1 <= page <= max_pages:
            self.sms_current_page = page
            self.refresh_sms_data()

    def get_sms_by_id(self, sms_id: int) -> Optional[SMSNotification]:
        """Get SMS by ID."""
        try:
            return self.service.get_sms_by_id(sms_id)
        except Exception as e:
            self.error_occurred.emit(f"خطا در دریافت پیامک: {str(e)}")
            return None

    # Email Methods
    def refresh_email_data(self):
        """Refresh Email data with current filters."""
        try:
            self.current_email_list, self.email_total_count = self.service.get_email_list(
                self.current_email_filter,
                self.email_current_page,
                self.page_size
            )
            self.email_data_changed.emit()
        except Exception as e:
            self.error_occurred.emit(f"خطا در بارگذاری ایمیل‌ها: {str(e)}")

    def send_email(self, recipient_name: str, recipient_email: str, subject: str,
                   message: str, attachments: List[str] = None) -> bool:
        """Send new Email."""
        if not self.validate_email(recipient_email):
            self.error_occurred.emit("آدرس ایمیل معتبر نیست")
            return False

        if not subject.strip():
            self.error_occurred.emit("موضوع ایمیل نمی‌تواند خالی باشد")
            return False

        if not message.strip():
            self.error_occurred.emit("متن ایمیل نمی‌تواند خالی باشد")
            return False

        self.loading_changed.emit(True)
        try:
            email = self.service.send_email(
                recipient_name.strip(),
                recipient_email.strip(),
                subject.strip(),
                message.strip(),
                attachments or []
            )
            self.refresh_email_data()

            if email.status == NotificationStatus.SENT:
                self.status_updated.emit(f"ایمیل به {recipient_name} ارسال شد")
                return True
            else:
                self.error_occurred.emit(f"خطا در ارسال ایمیل: {email.error_message}")
                return False

        except Exception as e:
            self.error_occurred.emit(f"خطا در ارسال ایمیل: {str(e)}")
            return False
        finally:
            self.loading_changed.emit(False)

    def filter_email(self, search_text: str = "", status: Optional[NotificationStatus] = None,
                     date_from: Optional[datetime] = None, date_to: Optional[datetime] = None,
                     recipient_filter: str = ""):
        """Apply Email filters."""
        self.current_email_filter = NotificationFilter(
            search_text=search_text.strip(),
            status=status,
            date_from=date_from,
            date_to=date_to,
            recipient_filter=recipient_filter.strip()
        )
        self.email_current_page = 1  # Reset to first page
        self.refresh_email_data()

    def clear_email_filters(self):
        """Clear all Email filters."""
        self.current_email_filter = NotificationFilter()
        self.email_current_page = 1
        self.refresh_email_data()

    def go_to_email_page(self, page: int):
        """Navigate to specific Email page."""
        max_pages = (self.email_total_count + self.page_size - 1) // self.page_size
        if 1 <= page <= max_pages:
            self.email_current_page = page
            self.refresh_email_data()

    def get_email_by_id(self, email_id: int) -> Optional[EmailNotification]:
        """Get Email by ID."""
        try:
            return self.service.get_email_by_id(email_id)
        except Exception as e:
            self.error_occurred.emit(f"خطا در دریافت ایمیل: {str(e)}")
            return None

    # Utility Methods
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Iranian mobile number pattern
        pattern = r'^(\+98|0)?9\d{9}$'
        return bool(re.match(pattern, phone.strip()))

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    def get_quick_date_filter(self, filter_type: str) -> tuple:
        """Get quick date filters."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if filter_type == "today":
            return today_start, now
        elif filter_type == "yesterday":
            yesterday = today_start - timedelta(days=1)
            return yesterday, today_start
        elif filter_type == "this_week":
            week_start = today_start - timedelta(days=now.weekday())
            return week_start, now
        elif filter_type == "last_week":
            week_start = today_start - timedelta(days=now.weekday() + 7)
            week_end = week_start + timedelta(days=7)
            return week_start, week_end
        elif filter_type == "this_month":
            month_start = today_start.replace(day=1)
            return month_start, now
        elif filter_type == "last_month":
            if now.month == 1:
                last_month_start = now.replace(year=now.year - 1, month=12, day=1)
            else:
                last_month_start = now.replace(month=now.month - 1, day=1)
            last_month_end = today_start.replace(day=1) - timedelta(days=1)
            return last_month_start, last_month_end
        else:
            return None, None

    def apply_quick_date_filter(self, filter_type: str, notification_type: str):
        """Apply quick date filter."""
        date_from, date_to = self.get_quick_date_filter(filter_type)

        if notification_type == "sms":
            self.current_sms_filter.date_from = date_from
            self.current_sms_filter.date_to = date_to
            self.sms_current_page = 1
            self.refresh_sms_data()
        elif notification_type == "email":
            self.current_email_filter.date_from = date_from
            self.current_email_filter.date_to = date_to
            self.email_current_page = 1
            self.refresh_email_data()

    def get_statistics(self) -> dict:
        """Get notification statistics."""
        try:
            return self.service.get_notification_stats()
        except Exception as e:
            self.error_occurred.emit(f"خطا در دریافت آمار: {str(e)}")
            return {'sms': {}, 'email': {}}

    def refresh_data(self):
        """Refresh all data (called by timer)."""
        try:
            self.refresh_sms_data()
            self.refresh_email_data()
        except Exception as e:
            # Don't show error for auto-refresh failures
            pass

    def export_sms_data(self, file_path: str) -> bool:
        """Export SMS data to CSV."""
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['نام گیرنده', 'شماره تماس', 'متن پیام', 'وضعیت', 'تاریخ ارسال', 'تاریخ ایجاد']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for sms in self.current_sms_list:
                    writer.writerow({
                        'نام گیرنده': sms.recipient_name,
                        'شماره تماس': sms.recipient_phone,
                        'متن پیام': sms.message[:50] + '...' if len(sms.message) > 50 else sms.message,
                        'وضعیت': self.get_status_display(sms.status),
                        'تاریخ ارسال': sms.sent_at.strftime('%Y-%m-%d %H:%M') if sms.sent_at else '',
                        'تاریخ ایجاد': sms.created_at.strftime('%Y-%m-%d %H:%M')
                    })
            return True
        except Exception as e:
            self.error_occurred.emit(f"خطا در خروجی گیری: {str(e)}")
            return False

    def export_email_data(self, file_path: str) -> bool:
        """Export Email data to CSV."""
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['نام گیرنده', 'آدرس ایمیل', 'موضوع', 'وضعیت', 'تعداد پیوست', 'تاریخ ارسال', 'تاریخ ایجاد']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for email in self.current_email_list:
                    writer.writerow({
                        'نام گیرنده': email.recipient_name,
                        'آدرس ایمیل': email.recipient_email,
                        'موضوع': email.subject,
                        'وضعیت': self.get_status_display(email.status),
                        'تعداد پیوست': len(email.attachments),
                        'تاریخ ارسال': email.sent_at.strftime('%Y-%m-%d %H:%M') if email.sent_at else '',
                        'تاریخ ایجاد': email.created_at.strftime('%Y-%m-%d %H:%M')
                    })
            return True
        except Exception as e:
            self.error_occurred.emit(f"خطا در خروجی گیری: {str(e)}")
            return False

    @staticmethod
    def get_status_display(status: NotificationStatus) -> str:
        """Get Persian display text for status."""
        status_map = {
            NotificationStatus.PENDING: "در انتظار",
            NotificationStatus.SENT: "ارسال شده",
            NotificationStatus.FAILED: "ناموفق",
            NotificationStatus.DELIVERED: "تحویل داده شده"
        }
        return status_map.get(status, "نامشخص")

    def get_current_sms_page_info(self) -> tuple:
        """Get current SMS pagination info."""
        max_pages = (self.sms_total_count + self.page_size - 1) // self.page_size if self.sms_total_count > 0 else 1
        return self.sms_current_page, max_pages, self.sms_total_count

    def get_current_email_page_info(self) -> tuple:
        """Get current Email pagination info."""
        max_pages = (self.email_total_count + self.page_size - 1) // self.page_size if self.email_total_count > 0 else 1
        return self.email_current_page, max_pages, self.email_total_count

    def test_connections(self) -> dict:
        """Test API connections."""
        return {
            'sms': self.service.test_sms_connection(),
            'email': self.service.test_email_connection()
        }
