"""
Controller layer for home page.
Handles coordination between the view and business logic.
"""
from typing import Optional, Callable
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox
from typing import List, Tuple

from features.Home.logic import HomePageLogic
from features.Home.models import DashboardStats
from features.Home.repo import InvoiceModel
from shared import show_question_message_box, NotificationDialog, return_resource

customers_database = return_resource("databases", "customers.db")
invoices_database = return_resource("databases", "invoices.db")
services_database = return_resource('databases', 'services.db')


class HomePageController(QObject):
    """Controller for home page operations."""

    # Signals for updating the view
    time_updated = Signal(str)
    date_updated = Signal(str)
    dashboard_updated = Signal(DashboardStats)
    table_updated = Signal(list)  # List of InvoiceTableRow
    error_occurred = Signal(str, str)  # title, message
    success_occurred = Signal(str, str)  # title, message
    recent_invoices = Signal(list)

    def __init__(self, logic: HomePageLogic, parent=None):
        """Initialize controller with business logic dependency."""
        super().__init__(parent)
        self.logic = logic
        self.timer = None
        self._setup_timer()

    def _setup_timer(self):
        """Set up timer for periodic updates."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_and_date)
        self.timer.start(1000)  # Update every second

    def initialize(self):
        """Initialize the controller and load initial data."""
        try:
            self.update_time_and_date()
            self.update_dashboard()
            self.update_invoice_table()
        except Exception as e:
            self.error_occurred.emit("خطای مقداردهی اولیه", f"خطا در بارگذاری اولیه: {str(e)}")

    def refresh_data(self):
        """Refresh all data displayed on the home page."""
        try:
            self.update_dashboard()
            self.update_invoice_table()
        except Exception as e:
            self.error_occurred.emit("خطای بروزرسانی", f"خطا در بروزرسانی اطلاعات: {str(e)}")

    def update_time_and_date(self):
        """Update time and date display."""
        try:
            time_info = self.logic.get_current_time_info()
            self.time_updated.emit(time_info.time_string)
            self.date_updated.emit(time_info.date_string)
        except Exception as e:
            self.error_occurred.emit("خطای زمان", f"خطا در بروزرسانی زمان: {str(e)}")

    def update_dashboard(self):
        """Update dashboard statistics."""
        try:
            stats = self.logic.get_dashboard_statistics()
            self.dashboard_updated.emit(stats)
            return stats
        except Exception as e:
            self.error_occurred.emit("خطای داشبورد", f"خطا در بروزرسانی داشبورد: {str(e)}")
            return None

    def get_recent_invoices(self) -> List[Tuple[InvoiceModel, str]]:
        """
        Get recent invoices with priority information.

        Returns:
            List of tuples containing (invoice, priority_label)
        """
        try:
            recent_invoices = self.logic.get_recent_invoices_with_priority(days_threshold=15)
            self.recent_invoices.emit(recent_invoices)
        except Exception as e:
            self.error_occurred.emit("خطای بارگذاری", f"خطا در بارگذاری فاکتورها: {str(e)}")
        return self.logic.get_recent_invoices_with_priority()

    def update_invoice_table(self):
        """Update invoice table data."""
        try:
            table_data = self.logic.get_invoice_table_data()
            self.table_updated.emit(table_data)
        except Exception as e:
            self.error_occurred.emit("خطای جدول", f"خطا در بارگذاری فاکتورها: {str(e)}")

    def handle_ready_delivery_request(self, invoice_number: str, parent_widget):
        """Handle ready for delivery notification request."""
        try:
            # Get invoice data
            invoice = self.logic.get_invoice_for_notification(invoice_number)
            if not invoice:
                self.error_occurred.emit("خطا", "فاکتور مورد نظر یافت نشد.")
                return

            # Show confirmation dialog
            title = "اطلاع‌رسانی آماده تحویل"
            message = "آیا می‌خواهید به مشتری اطلاع دهید که فاکتور آماده تحویل است؟"
            button1 = "بله، می‌خواهم اطلاع دهم"
            button2 = "خیر"

            show_question_message_box(
                parent_widget, title, message, button1,
                lambda: self._show_notification_dialog(invoice_number, parent_widget),
                button2
            )

        except Exception as e:
            self.error_occurred.emit("خطای اطلاع‌رسانی", f"خطا در پردازش درخواست: {str(e)}")

    def handle_delivery_confirmation_request(self, invoice_number: str, parent_widget):
        """Handle delivery confirmation request."""
        try:
            # Validate that invoice can be marked as delivered
            if not self.logic.validate_delivery_confirmation(invoice_number):
                self.error_occurred.emit("خطا", "فاکتور مورد نظر یافت نشد یا قبلاً تحویل داده شده است.")
                return

            # Show confirmation dialog
            title = "تأیید تحویل"
            message = "آیا مشتری فاکتور خود را دریافت کرده است؟"

            reply = QMessageBox.question(parent_widget, title, message,
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                success = self.logic.mark_invoice_delivered(invoice_number)
                if success:
                    self.success_occurred.emit("موفقیت", "فاکتور به عنوان تحویل شده علامت‌گذاری شد.")
                    # Refresh data to show updated status
                    self.refresh_data()
                else:
                    self.error_occurred.emit("خطا", "خطا در به‌روزرسانی وضعیت تحویل.")

        except Exception as e:
            self.error_occurred.emit("خطای تحویل", f"خطا در پردازش تحویل: {str(e)}")

    def handle_view_pdf_request(self, pdf_path: str):
        """Handle PDF viewing request."""
        try:
            from shared import open_file
            open_file(pdf_path)
        except Exception as e:
            self.error_occurred.emit("خطای نمایش", f"خطا در نمایش فایل PDF: {str(e)}")

    def _show_notification_dialog(self, invoice_number: str, parent_widget):
        """Show SMS/Email notification dialog."""
        try:

            dialog = NotificationDialog(
                invoice_number,
                invoices_database,
                customers_database,
                parent_widget
            )
            dialog.exec_()

        except Exception as e:
            self.error_occurred.emit("خطای اطلاع‌رسانی", f"خطا در نمایش پنجره اطلاع‌رسانی: {str(e)}")

    def stop_timer(self):
        """Stop the update timer."""
        if self.timer:
            self.timer.stop()

    def start_timer(self):
        """Start the update timer."""
        if self.timer:
            self.timer.start(1000)


class HomePageControllerFactory:
    """Factory for creating home page controller instances."""

    @staticmethod
    def create_controller(customers_db_path: str, invoices_db_path: str, documents_db_path: str) -> HomePageController:
        """Create a fully configured home page controller."""
        from repo import HomePageRepository

        # Create repository
        repository = HomePageRepository(customers_db_path=customers_database,
                                        invoices_db_path=invoices_database,
                                        services_db_path=services_database)

        # Create business logic
        logic = HomePageLogic(repository)

        # Create controller
        controller = HomePageController(logic)

        return controller
