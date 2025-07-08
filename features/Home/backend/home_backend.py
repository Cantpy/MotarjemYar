"""
Backend business logic for the home page.
"""

import jdatetime
from datetime import date, datetime
from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QVariantAnimation, QEasingCurve
from PySide6.QtWidgets import QLabel, QMessageBox

from features.Home.models.home_models import DatabaseManager, IssuedInvoice, Customer
from shared import to_persian_number, parse_jalali_date


class HomePageBackend(QObject):
    """Backend service for home page operations."""

    # Signals
    stats_updated = Signal(dict)
    invoices_updated = Signal(list)
    datetime_updated = Signal(str, str)
    document_stats_updated = Signal(str, str)
    error_occurred = Signal(str, str)  # title, message

    def __init__(self, customers_db_path: str, invoices_db_path: str, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager(customers_db_path, invoices_db_path)
        self.persian_weekdays = {
            "Saturday": "شنبه", "Sunday": "یکشنبه", "Monday": "دوشنبه",
            "Tuesday": "سه‌شنبه", "Wednesday": "چهارشنبه",
            "Thursday": "پنج‌شنبه", "Friday": "جمعه"
        }
        self.persian_months = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
            5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
            9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند"
        }

    def update_datetime(self):
        """Update current date and time with Persian formatting."""
        try:
            # Update time
            current_time = datetime.now().strftime("%H:%M:%S")
            persian_time = to_persian_number(current_time)

            # Update date
            jalali_date = jdatetime.date.today()
            weekday = self.persian_weekdays[jalali_date.strftime("%A")]
            month = self.persian_months[jalali_date.month]

            date_str = (f"{weekday}، {to_persian_number(jalali_date.day)} "
                        f"{month} {to_persian_number(jalali_date.year)}")

            self.datetime_updated.emit(date_str, persian_time)

        except Exception as e:
            self.error_occurred.emit("خطای زمان", f"خطا در بروزرسانی زمان: {str(e)}")

    def update_dashboard_stats(self):
        """Update all dashboard statistics."""
        try:
            stats = self.db_manager.get_dashboard_stats()
            # Emit the stats for UI update
            self.stats_updated.emit(stats)

        except Exception as e:
            self.error_occurred.emit("خطای داشبورد", f"خطا در بروزرسانی داشبورد: {str(e)}")

    def update_invoices_table(self):
        """Update invoices table data."""
        try:
            invoices = self.db_manager.get_recent_invoices()
            processed_invoices = []

            today = jdatetime.date.today().togregorian()

            for invoice in invoices:
                # Parse delivery date
                delivery_date_str = invoice.delivery_date.strip()
                if delivery_date_str == "نامشخص":
                    continue

                delivery_date = parse_jalali_date(delivery_date_str)
                if not delivery_date:
                    continue

                # Determine row color based on delivery date
                days_diff = (delivery_date - today).days

                if days_diff <= 0:
                    row_color = "overdue"  # Red
                elif days_diff <= 2:
                    row_color = "soon"  # Yellow
                else:
                    row_color = "normal"  # White

                processed_invoices.append({
                    'invoice': invoice,
                    'delivery_date': delivery_date,
                    'row_color': row_color
                })

            # Sort by delivery date (overdue first)
            processed_invoices.sort(key=lambda x: x['delivery_date'])

            # Take top 20
            processed_invoices = processed_invoices[:20]

            self.invoices_updated.emit(processed_invoices)

        except Exception as e:
            self.error_occurred.emit("خطای جدول", f"خطا در بارگذاری فاکتورها: {str(e)}")


    def mark_invoice_delivered(self, invoice_number: str) -> bool:
        """Mark an invoice as delivered."""
        try:
            success = self.db_manager.update_delivery_status(invoice_number, 1)
            if success:
                # Update both table and dashboard stats
                self.update_invoices_table()
                self.update_dashboard_stats()
            return success

        except Exception as e:
            self.error_occurred.emit("خطای پایگاه داده", f"خطا در به‌روزرسانی وضعیت تحویل: {str(e)}")
            return False


    def get_customer_info(self, invoice_number: str) -> Optional[Customer]:
        """Get customer information for notification."""
        try:
            return self.db_manager.get_customer_by_invoice(invoice_number)
        except Exception as e:
            self.error_occurred.emit("خطای مشتری", f"خطا در دریافت اطلاعات مشتری: {str(e)}")
            return None


class AnimationManager(QObject):
    """Manages label animations for dashboard statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_animations = []

    def animate_label(self, label: QLabel, start_value: int, end_value: int, duration: int = 1500):
        """Animate label value from start to end with smooth transition."""
        if end_value <= 0:
            label.setText(to_persian_number(0))
            return

        animation = QVariantAnimation(self)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        animation.valueChanged.connect(
            lambda value: label.setText(to_persian_number(int(value)))
        )

        # Clean up when animation finishes
        animation.finished.connect(lambda: self._cleanup_animation(animation))

        self.active_animations.append(animation)
        animation.start()

    def _cleanup_animation(self, animation):
        """Remove finished animation from active list."""
        if animation in self.active_animations:
            self.active_animations.remove(animation)

    def stop_all_animations(self):
        """Stop all active animations."""
        for animation in self.active_animations:
            animation.stop()
        self.active_animations.clear()