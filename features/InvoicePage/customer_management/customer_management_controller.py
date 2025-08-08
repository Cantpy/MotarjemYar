from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, QTimer
from typing import Optional
from features.InvoicePage.customer_management.customer_management_view import CustomerManagementView
from features.InvoicePage.customer_management.customer_management_logic import CustomerLogic
from features.InvoicePage.customer_management.customer_managemnet_models import CustomerData, CompanionData
from shared import show_question_message_box


class CustomerManagementController(QObject):
    """Controller for customer management dialog."""

    def __init__(self, logic: CustomerLogic, parent=None):
        super().__init__(parent)
        self.logic = logic
        self.view = CustomerManagementView(parent)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.current_search_term = ""

        # Connect signals
        self.connect_signals()

        # Load initial data
        self.refresh_data()

    def connect_signals(self):
        """Connect view signals to controller methods."""
        self.view.search_requested.connect(self.on_search_requested)
        self.view.add_customer_requested.connect(self.on_add_customer_requested)
        self.view.edit_customer_requested.connect(self.on_edit_customer_requested)
        self.view.delete_customer_requested.connect(self.on_delete_customer_requested)
        self.view.refresh_requested.connect(self.refresh_data)

    def show(self):
        """Show the customer management dialog."""
        self.view.show()

    def exec(self) -> int:
        """Execute the dialog modally."""
        return self.view.exec()

    def refresh_data(self):
        """Refresh customer data from database."""
        try:
            self.view.update_status("در حال بارگیری...")
            QApplication.processEvents()

            if self.current_search_term:
                customers = self.logic.search_customers_and_companions(self.current_search_term)
            else:
                customers = self.logic.get_all_customers_with_details()

            self.view.populate_table(customers)
            self.view.update_status(f"تعداد مشتریان: {len(customers)}")

        except Exception as e:
            self.view.show_error("خطا", f"خطا در بارگیری اطلاعات مشتریان:\n{str(e)}")
            print("refresh data error: ", e)
            self.view.update_status("خطا در بارگیری")

    def on_search_requested(self, search_term: str):
        """Handle search request with debouncing."""
        self.current_search_term = search_term.strip()

        # Stop any pending search
        self.search_timer.stop()

        if len(self.current_search_term) >= 2 or self.current_search_term == "":
            # Debounce search requests - wait 300ms after user stops typing
            self.search_timer.start(300)
        else:
            self.view.update_status("حداقل 2 کاراکتر برای جستجو وارد کنید")

    def perform_search(self):
        """Perform the actual search."""
        try:
            self.view.update_status("در حال جستجو...")
            QApplication.processEvents()

            customers = self.logic.search_customers_and_companions(self.current_search_term)
            self.view.populate_table(customers)

            if self.current_search_term:
                self.view.update_status(f"نتایج جستجو برای '{self.current_search_term}': {len(customers)} مشتری")
            else:
                self.view.update_status(f"تعداد مشتریان: {len(customers)}")

        except Exception as e:
            self.view.show_error("خطا", f"خطا در جستجو:\n{str(e)}")
            self.view.update_status("خطا در جستجو")

    def on_add_customer_requested(self):
        """Handle add customer request."""
        try:
            # For now, show a placeholder message
            # In a real implementation, you would open a customer form dialog
            self.view.show_info(
                "افزودن مشتری",
                "فرم افزودن مشتری در اینجا باز خواهد شد.\n"
                "این قابلیت نیاز به پیاده‌سازی فرم مخصوص دارد."
            )

            # Example of how you might create a customer:
            # customer_data = CustomerData(
            #     national_id="1234567890",
            #     name="نام تست",
            #     phone="09123456789",
            #     email="test@example.com",
            #     address="آدرس تست",
            #     telegram_id="@test",
            #     passport_image=""
            # )
            #
            # success, errors = self.logic.create_customer(customer_data)
            # if success:
            #     self.view.show_info("موفقیت", "مشتری با موفقیت اضافه شد")
            #     self.refresh_data()
            # else:
            #     self.view.show_error("خطا", "\n".join(errors))

        except Exception as e:
            self.view.show_error("خطا", f"خطا در افزودن مشتری:\n{str(e)}")

    def on_edit_customer_requested(self, national_id: str):
        """Handle edit customer request."""
        try:
            customer = self.logic.get_customer_by_national_id(national_id)
            if not customer:
                self.view.show_error("خطا", "مشتری یافت نشد")
                return

            # For now, show customer info
            # In a real implementation, you would open a customer form dialog with data pre-filled
            customer_info = f"""
نام: {customer.name}
کد ملی: {customer.national_id}
تلفن: {customer.phone}
ایمیل: {customer.email}
آدرس: {customer.address}
تلگرام: {customer.telegram_id}
            """.strip()

            self.view.show_info(
                "ویرایش مشتری",
                f"فرم ویرایش مشتری در اینجا باز خواهد شد.\n\n"
                f"اطلاعات فعلی مشتری:\n{customer_info}"
            )

            # Example of how you might update a customer:
            # customer.name = "نام جدید"
            # success, errors = self.logic.update_customer(customer)
            # if success:
            #     self.view.show_info("موفقیت", "مشتری با موفقیت بروزرسانی شد")
            #     self.refresh_data()
            # else:
            #     self.view.show_error("خطا", "\n".join(errors))

        except Exception as e:
            self.view.show_error("خطا", f"خطا در ویرایش مشتری:\n{str(e)}")

    def on_delete_customer_requested(self, national_id: str):
        """Handle delete customer request."""
        try:
            customer = self.logic.get_customer_by_national_id(national_id)
            if not customer:
                self.view.show_error("خطا", "مشتری یافت نشد")
                return

            # Check for active invoices first
            success, errors, has_active_invoices, active_count = self.logic.delete_customer(national_id)

            if has_active_invoices:
                # Show warning about active invoices
                warning_message = (
                    f"مشتری '{customer.name}' دارای {active_count} فاکتور فعال (تحویل نشده) است.\n\n"
                    "آیا مطمئن هستید که می‌خواهید این مشتری را حذف کنید؟\n"
                    "این عمل غیرقابل برگشت است و ممکن است بر فاکتورهای مربوطه تأثیر بگذارد."
                )

                def force_delete():
                    success, errors = self.logic.force_delete_customer(national_id)
                    if success:
                        self.view.show_info("موفقیت", f"مشتری '{customer.name}' با موفقیت حذف شد")
                        self.refresh_data()
                        self.view.clear_selection()
                    else:
                        self.view.show_error("خطا", f"خطا در حذف مشتری:\n{chr(10).join(errors)}")

                def cancel_delete():
                    self.view.update_status("حذف مشتری لغو شد")

                # Show custom question box
                show_question_message_box(
                    parent=self.view,  # Assuming self.view is a QWidget
                    title="هشدار - حذف مشتری با فاکتور فعال",
                    message=warning_message,
                    button_1="بله، حذف کن",  # Yes
                    yes_func=force_delete,
                    button_2="خیر، لغو",  # No
                    action_func=cancel_delete  # Will be called only if button_3 is clicked, optional
                )
                return

            if success:
                self.view.show_info("موفقیت", f"مشتری '{customer.name}' با موفقیت حذف شد")
                self.refresh_data()
                self.view.clear_selection()
            else:
                if errors:
                    self.view.show_error("خطا", f"خطا در حذف مشتری:\n{chr(10).join(errors)}")
                else:
                    self.view.show_error("خطا", "خطای نامشخص در حذف مشتری")

        except Exception as e:
            self.view.show_error("خطا", f"خطا در حذف مشتری:\n{str(e)}")

    def get_customer_summary(self, national_id: str) -> Optional[str]:
        """Get a summary of customer information."""
        try:
            customers = self.logic.get_all_customers_with_details()
            for customer in customers:
                if customer.national_id == national_id:
                    return self.logic.get_customer_summary(customer)
            return None
        except Exception:
            return None

    def select_customer_by_national_id(self, national_id: str):
        """Select a customer in the table by national ID."""
        self.view.select_customer_by_national_id(national_id)

    def get_view(self) -> CustomerManagementView:
        """Get the view instance."""
        return self.view
