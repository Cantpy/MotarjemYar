"""
Controller layer for home page.
Handles coordination between the view and business logic.
"""
from typing import Optional, Callable
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox, QWidget
from typing import List, Tuple

from features.Home.home_logic import HomePageLogic
from features.Home.home_models import DashboardStats, DeliveryStatus, StatusChangeRequest
from features.Home.home_settings_models import Settings
from features.Home.home_repo import IssuedInvoiceModel
from shared import (show_question_message_box, show_information_message_box, NotificationDialog, return_resource,
                    show_error_message_box, show_warning_message_box)

customers_database = return_resource("databases", "customers.db")
invoices_database = return_resource("databases", "invoices.db")
services_database = return_resource('databases', 'services.db')


class HomepageSettingsManager(QObject):
    settings_updated = Signal(Settings)  # signal to notify changes

    def __init__(self, default_settings: Settings):
        super().__init__()
        self._settings = default_settings

    def get_settings(self) -> Settings:
        return self._settings

    def update_settings(self, new_settings: Settings):
        self._settings = new_settings
        self.settings_updated.emit(self._settings)

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
    context_menu_data = Signal(list)

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

    def get_recent_invoices(self) -> List[Tuple[IssuedInvoiceModel, str]]:
        """
        Get recent invoices with priority information.

        Returns:
            List of tuples containing (invoice, priority_label)
        """
        try:
            recent_invoices = self.logic.get_recent_invoices_with_priority(days_threshold=10)
            self.recent_invoices.emit(recent_invoices)
        except Exception as e:
            self.error_occurred.emit("خطای بارگذاری", f"خطا در بارگذاری فاکتورها: {str(e)}")
        return self.logic.get_recent_invoices_with_priority()

    def invoice_data_for_context_menu(self, invoice_number: int):

        try:
            invoice = self.logic.get_invoice_for_context_menu(invoice_number)
            self.context_menu_data.emit(invoice)
        except Exception as e:
            self.error_occurred.emit("خطای دریافت اطلاعات", f"خطا در دریافت اطلاعات فاکتور: {str(e)}")
        return self.logic.get_invoice_for_context_menu(invoice_number)

    def update_invoice_table(self):
        """Update invoice table data."""
        try:
            table_data = self.logic.get_invoice_table_data()
            self.table_updated.emit(table_data)
        except Exception as e:
            self.error_occurred.emit("خطای جدول", f"خطا در بارگذاری فاکتورها: {str(e)}")

    def handle_ready_delivery_request(self, invoice_number: int, parent_widget):
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
                lambda: self._show_notification_dialog(str(invoice_number), parent_widget),
                button2
            )

        except Exception as e:
            self.error_occurred.emit("خطای اطلاع‌رسانی", f"خطا در پردازش درخواست: {str(e)}")

    def handle_delivery_confirmation_request(self, invoice_number: int, parent_widget):
        """Handle delivery confirmation request."""
        try:
            # Validate that invoice can be marked as delivered
            if not self.logic.validate_delivery_confirmation(invoice_number):
                self.error_occurred.emit("خطا", "فاکتور مورد نظر یافت نشد یا قبلاً تحویل داده شده است.")
                return

            # Show confirmation dialog
            title = "تأیید تحویل"
            message = "آیا مشتری فاکتور خود را دریافت کرده است؟"
            button1 = "بله"
            button2 = "خیر"

            def _is_delivered():
                success = self.logic.mark_invoice_delivered(str(invoice_number))
                if success:
                    self.success_occurred.emit("موفقیت", "فاکتور به عنوان تحویل شده علامت‌گذاری شد.")
                    # Refresh data to show updated status
                    self.refresh_data()
                else:
                    self.error_occurred.emit("خطا", "خطا در به‌روزرسانی وضعیت تحویل.")

            show_question_message_box(parent_widget, title, message, button1, _is_delivered, button2)

        except Exception as e:
            self.error_occurred.emit("خطای تحویل", f"خطا در پردازش تحویل: {str(e)}")

    def handle_view_pdf_request(self, pdf_path: str):
        """Handle PDF viewing request."""
        try:
            from shared import open_file
            open_file(pdf_path)
        except Exception as e:
            self.error_occurred.emit("خطای نمایش", f"خطا در نمایش فایل PDF: {str(e)}")

    def handle_change_invoice_status_request(
            self,
            invoice_number: int,
            StatusChangeDialogClass,
            parent: QWidget = None
    ):
        """
        Handle the status change dialog request.
        Accepts the dialog class to avoid circular imports.
        """
        try:
            # Get current invoice information
            invoice = self.logic.repository.get_invoice_by_number(invoice_number)

            if not invoice:
                show_error_message_box(parent, "خطا", "فاکتور یافت نشد")
                return

            # Check if invoice can be advanced
            next_status, step_text = self.logic.get_available_next_step(invoice_number)

            if next_status is None:
                show_information_message_box(parent, "موفقیت", str(step_text))
                return

            # Instantiate and show the injected dialog class
            dialog = StatusChangeDialogClass(
                invoice=invoice,
                next_status=next_status,
                step_text=step_text,
                parent=parent
            )

            # Connect dialog signals
            dialog.status_change_requested.connect(
                lambda request: self._handle_status_change_request(request, parent)
            )

            dialog.exec()

        except Exception as e:
            show_error_message_box(parent, "خطا", f"خطا در باز کردن پنجره تغییر وضعیت: {str(e)}")

        finally:
            self.refresh_data()

    def _handle_status_change_request(self, request: StatusChangeRequest, parent: QWidget = None):
        """Handle the actual status change request from the dialog."""
        try:
            success = False
            message = ""

            if request.target_status == DeliveryStatus.ASSIGNED:
                # Step 1: Assign translator
                success, message = self.logic.change_status_to_assigned(request)

            elif request.target_status == DeliveryStatus.TRANSLATED:
                # Step 2: Mark as translated
                success, message = self.logic.change_status_to_translated(request)

            elif request.target_status == DeliveryStatus.READY:
                # Step 3: Mark as ready (call existing controller method)
                success, message = self.logic.change_status_to_ready(request)
                if success:
                    # Call the existing method
                    self.handle_ready_delivery_request(request.invoice_number, parent)
                    message = "فاکتور آماده تحویل شد"

            elif request.target_status == DeliveryStatus.COLLECTED:
                # Step 4: Mark as collected (call existing controller method)
                success, message = self.logic.change_status_to_collected(request)
                if success:
                    # Call the existing method
                    self.handle_delivery_confirmation_request(request.invoice_number, parent)
                    message = "فاکتور تحویل داده شد"

            if success:
                show_information_message_box(parent, "موفقیت", message)
            else:
                show_error_message_box(parent, "خطا", message)

        except Exception as e:
            show_error_message_box(parent, "خطا", f"خطا در تغییر وضعیت:\n {str(e)}")

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
        from home_repo import HomePageRepository

        # Create repository
        repository = HomePageRepository(customers_db_path=customers_database,
                                        invoices_db_path=invoices_database,
                                        services_db_path=services_database)

        # Create business logic
        logic = HomePageLogic(repository)

        # Create controller
        controller = HomePageController(logic)

        return controller
