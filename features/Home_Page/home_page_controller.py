# features/Home_Page/home_page_controller.py

from PySide6.QtCore import QObject, Slot, QPoint
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtGui import QAction
from pathlib import Path

from features.Home_Page.home_page_logic import HomePageLogic
from features.Home_Page.home_page_view import HomePageView
from features.Home_Page.home_page_settings.hom_page_settings_factory import HomepageSettingsFactory
from features.Home_Page.home_page_models import StatusChangeRequest
from features.Home_Page.home_page_settings.home_page_settings_models import Settings
from shared import (
    show_question_message_box, show_information_message_box, show_error_message_box, show_warning_message_box,
    NotificationDialog, StatusChangeDialog
)
from shared.enums import DeliveryStatus
from shared.dtos.notification_dialog_dtos import SmsRequestDTO, EmailRequestDTO


class HomePageController(QObject):
    """
    Controller for home page operations.
    Connects the View to the business _logic and settings manager.
    """

    def __init__(self, view: HomePageView, logic: HomePageLogic):
        super().__init__()
        self._view = view
        self._logic = logic
        self._settings_controller = HomepageSettingsFactory.create()
        self._settings_manager = self._settings_controller._logic

        self._connect_signals()
        self.initialize_view()

    def get_view(self) -> QWidget:
        """
        Returns the _view instance managed by this controller.
        This fulfills one of your specific requests.
        """
        return self._view

    def _connect_signals(self):
        """Connect signals from the _view to controller slots."""
        self._view.refresh_requested.connect(self.refresh_data)
        self._view.operations_menu_requested.connect(self._on_operations_menu_requested)
        self._view.settings_requested.connect(self._on_settings_requested)
        self._settings_manager.settings_changed.connect(self._on_settings_changed)

    def initialize_view(self):
        """Load initial data and apply settings to the _view."""
        settings_controller = HomepageSettingsFactory.create()
        settings_logic = settings_controller._logic
        current_settings = settings_logic.get_current_settings()
        self._view.apply_settings(current_settings)
        self.refresh_data()

    # NEW SLOT to handle menu requests from the _view
    @Slot(int, QPoint)
    def _on_operations_menu_requested(self, invoice_number: str, global_pos: QPoint):
        """
        Creates and shows the operations services menu for a given invoice.
        This _logic now resides ENTIRELY in the controller.
        """
        # 1. Get the necessary data from the _logic layer
        invoice_details = self._logic.get_invoice_for_menu(invoice_number)
        print(f'invoice details for invoice number {invoice_number}: {invoice_details}')

        if not invoice_details:
            show_error_message_box(self._view, "خطا", "اطلاعات فاکتور یافت نشد.")
            return

        # 2. Create the menu
        menu = QMenu(self._view)

        # 3. Create actions and connect them to controller methods
        view_action = QAction("مشاهده فاکتور", menu)
        # Use a lambda to pass the specific PDF path to the handler
        view_action.triggered.connect(
            lambda: self.handle_view_pdf_request(invoice_details.pdf_file_path)
        )
        menu.addAction(view_action)

        status_action = QAction("تغییر وضعیت", menu)
        # Use a lambda to pass the invoice number to the handler
        status_action.triggered.connect(
            lambda: self.handle_change_invoice_status_request(invoice_number)
        )
        menu.addAction(status_action)

        # 4. Show the menu at the position the _view provided
        menu.exec(global_pos)

    @Slot()
    def refresh_data(self):
        """Refresh all data displayed on the home page."""
        try:
            # This now correctly uses the single source of truth for settings
            current_settings = self._settings_manager.get_current_settings()
            print(f'no error in getting current settings')
            stats = self._logic.get_dashboard_statistics()
            print(f'no errors in getting stats')
            invoices = self._logic.get_recent_invoices_with_priority(
                days_threshold=current_settings.threshold_days
            )
            print('no errors in getting invoices')
            self._view.update_stats_display(stats)
            self._view.populate_invoices_table(invoices)
        except Exception as e:
            print(f'[WARNING]: Exception in showing home data: {e}')
            show_error_message_box(self._view, "خطای بروزرسانی", f"خطا در بروزرسانی اطلاعات: {str(e)}")

    @Slot()
    def _on_settings_requested(self):
        """Handle the _view's request to open the settings dialog."""
        dialog = self._settings_controller.show_dialog(parent=self._view)
        dialog.exec()

    @Slot(Settings)
    def _on_settings_changed(self, new_settings: Settings):
        """
        Slot to handle when settings have been successfully changed and saved
        by the separate settings package.
        """
        # 1. Apply the new settings directly to the view (e.g., update titles).
        self._view.apply_settings(new_settings)

        # 2. Give the user feedback.
        show_information_message_box(self._view, "موفقیت", "تنظیمات با موفقیت بروزرسانی شد.")

        # 3. Refresh the entire page data to reflect the changes (e.g., new date thresholds).
        self.refresh_data()

    def handle_view_pdf_request(self, pdf_path: str):
        """Handles the request to open a PDF file."""
        if not pdf_path or not Path(pdf_path).exists():
            show_error_message_box(self._view, "خطا", "فایل PDF فاکتور یافت نشد.")
            return
        try:
            from shared import open_file
            open_file(pdf_path)
        except Exception as e:
            show_error_message_box(self._view, "خطای نمایش", f"خطا در نمایش فایل PDF: {str(e)}")

    def handle_change_invoice_status_request(self, invoice_number: str):
        """Handles the request to open the status change dialog."""

        # 1. Ask the _logic layer for the next step info
        next_step_info = self._logic.get_available_next_step(invoice_number)

        if next_step_info is None:
            show_information_message_box(self._view, "اتمام فرآیند", "این فاکتور در مرحله نهایی قرار دارد.")
            return

        next_status, step_text = next_step_info

        # --- MODIFICATION START ---
        # 2. Get current invoice data to show in the dialog
        invoice_dto = self._logic.get_invoice_for_menu(invoice_number)

        # 3. If the next step is assigning a translator, fetch the translator list
        translators = []
        if next_status == DeliveryStatus.ASSIGNED:
            try:
                translators = self._logic.get_all_translators()
                if not translators:
                    # Optional: Show a warning if no translators are found in the system
                    show_warning_message_box(self._view, "هشدار", "هیچ مترجمی در سیستم ثبت نشده است.")
            except Exception as e:
                show_error_message_box(self._view, "خطا", f"خطا در دریافت لیست مترجمین: {e}")
                return

        # 4. Show the dialog, passing it the clean data and the translator list
        dialog = StatusChangeDialog(
            invoice=invoice_dto,
            next_status=next_status,
            step_text=step_text,
            translators=translators,
            parent=self._view
        )
        # --- MODIFICATION END ---

        # Connect dialog signals
        dialog.status_change_requested.connect(self._on_status_change_confirmed)

        dialog.exec()

    @Slot(object)  # The object is a StatusChangeRequest DTO from the dialog
    def _on_status_change_confirmed(self, request: StatusChangeRequest):
        """
        Handles the actual status change after the user confirms in the dialog.
        This is the single point of action.
        """
        # --- MODIFICATION START ---
        # If the target status is the final 'COLLECTED' step, ask for payment confirmation.
        if request.target_status == DeliveryStatus.COLLECTED:
            show_question_message_box(
                parent=self._view,
                title="تایید پرداخت",
                message="آیا مشتری هزینه فاکتور را به طور کامل پرداخت کرده است؟",
                button_1="بله، پرداخت شده",
                yes_func=lambda: self._execute_status_change(request, paid=True),
                button_2="انصراف",
                button_3="خیر، ولی تحویل داده شد",
                action_func=lambda: self._execute_status_change(request, paid=False)
            )
        else:
            # For all other status changes, payment status is not relevant.
            self._execute_status_change(request, paid=False)
        # --- MODIFICATION END ---

    def _execute_status_change(self, request: StatusChangeRequest, paid: bool):
        """
        Private helper to perform the status change after all user choices are made.

        Args:
            request: The original StatusChangeRequest DTO from the dialog.
            paid: A boolean indicating if the invoice was paid, only relevant for the final step.
        """
        try:
            # Set the flag on the request DTO based on the user's input
            request.set_payment_as_paid = paid

            # A single call to the _logic layer's unit of work.
            success, message = self._logic.change_invoice_status(request)

            if success:
                show_information_message_box(self._view, "موفقیت", message)
                self.refresh_data()

                # Business Flow: If the new status is READY, trigger the notification dialog.
                if request.target_status == DeliveryStatus.READY:
                    show_question_message_box(parent=self._view,
                                              title="اطلاع رسانی",
                                              message="آیا می‌خواهید آماه بودن فاکتور را به مشتری اطلاع‌رسانی کنید؟",
                                              button_1="بله",
                                              button_2="خیر",
                                              yes_func=lambda: self._show_notification_dialog(request.invoice_number))
            else:
                show_error_message_box(self._view, "خطا", message)

        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطا در پردازش تغییر وضعیت:\n {str(e)}")

    def _show_notification_dialog(self, invoice_number: str):
        """
        Shows the SMS/Email notification dialog.
        It gets all required data from the logic layer in a single DTO.
        """
        try:
            # A single call now gets ALL the data we need.
            notification_data = self._logic.get_data_for_notification(invoice_number)
            if not notification_data:
                show_error_message_box(self._view, "خطا", "اطلاعات مورد نیاز برای اطلاع‌رسانی یافت نشد.")
                return

            print(f'sending notification to customer with national id: {notification_data.customer_national_id}')

            # 1. Create the dialog with the complete DTO
            dialog = NotificationDialog(notification_data, self._view)

            # 2. Connect to its signals
            dialog.send_sms_requested.connect(self._on_send_sms_requested)

            # --- THIS IS THE KEY CHANGE ---
            dialog.send_email_requested.connect(
                lambda req: self._on_send_email_requested(req, notification_data.customer_national_id)
            )

            # 3. Show the dialog
            dialog.exec()

        except Exception as e:
            print(f'show notifications dialog error: {e}')
            show_error_message_box(self._view,
                                   "خطای اطلاع‌رسانی", f"خطا در نمایش پنجره اطلاع‌رسانی: {str(e)}")

    @Slot(SmsRequestDTO)
    def _on_send_sms_requested(self, request: SmsRequestDTO):
        """Slot to handle the dialog's request to send an SMS."""
        success, message = self._logic.send_sms_notification(request)
        if success:
            show_information_message_box(self._view, "موفقیت", message)
            # Find the dialog and accept it to close it
            dialog = self._view.findChild(NotificationDialog)
            if dialog:
                dialog.accept()
        else:
            show_error_message_box(self._view, "خطا", message)

    @Slot(EmailRequestDTO, str)
    def _on_send_email_requested(self, request: EmailRequestDTO, national_id: str):
        """Slot to handle the dialog's request to send an Email."""
        success, message = self._logic.send_email_notification(request, national_id)
        if success:
            show_information_message_box(self._view, "موفقیت", message)
            dialog = self._view.findChild(NotificationDialog)
            if dialog:
                dialog.accept()
        else:
            show_error_message_box(self._view, "خطا", message)
