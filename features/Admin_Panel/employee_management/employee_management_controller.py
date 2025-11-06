# features/Admin_Panel/employee_management/employee_management_controller.py

from features.Admin_Panel.employee_management.employee_management_dialog import EmployeeEditDialog
from features.Admin_Panel.employee_management.employee_details_dialog import EmployeeDetailsDialog
from features.Admin_Panel.employee_management.employee_management_view import UserManagementView
from features.Admin_Panel.employee_management.employee_management_logic import UserManagementLogic
from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData
from shared import show_error_message_box, show_information_message_box, show_question_message_box


class UserManagementController:
    def __init__(self, view: UserManagementView, logic: UserManagementLogic):
        self._view = view
        self._logic = logic
        self.load_initial_data()
        self._connect_signals()

    def _connect_signals(self):
        """Connects UI signals to controller methods."""
        self._view.add_employee_requested.connect(self._add_employee)
        self._view.edit_employee_requested.connect(self._edit_employee)
        self._view.delete_employee_requested.connect(self._delete_employee)
        self._view.view_employee_details_requested.connect(self._view_employee_details)

    def load_initial_data(self):
        """Fetches all users and populates the main table."""
        try:
            employees = self._logic.get_all_employees_for_display()
            self._view.populate_employee_table(employees)
        except Exception as e:
            print(f"Error loading employees: {e}")
            show_error_message_box(self._view, "خطا", f"خطایی در بارگذاری لیست کارمندان رخ داد: {e}")

    def _add_employee(self):
        """Handles the 'Add User' action."""
        try:
            roles = self._logic.get_all_roles()
            dialog = EmployeeEditDialog(roles=roles, parent=self._view)
            dialog.save_requested.connect(
                lambda data: self._handle_save_request(dialog, data, is_edit=False)
            )
            dialog.exec()
        except Exception as e:
            print(f"Error opening add employee dialog: {e}")
            show_error_message_box(self._view, "خطا", f"امکان باز کردن فرم ثبت کارمند وجود ندارد: {e}")

    def _edit_employee(self, employee_data: EmployeeFullData):
        """Handles the 'Edit User' action."""
        try:
            roles = self._logic.get_all_roles()
            dialog = EmployeeEditDialog(employee_data, roles=roles, parent=self._view)
            dialog.save_requested.connect(
                lambda data: self._handle_save_request(dialog, data, is_edit=True)
            )
            dialog.exec()
        except Exception as e:
            print(f"Error opening edit employee dialog: {e}")
            show_error_message_box(self._view, "خطا", f"امکان باز کردن فرم ویرایش وجود ندارد: {e}")

    def _view_employee_details(self, employee_id: str):
        """Shows the detailed view dialog for an employee."""
        try:
            full_data = self._logic.get_employee_details_for_view(employee_id)
            dialog = EmployeeDetailsDialog(full_data, parent=self._view)
            dialog.exec()
        except Exception as e:
            print(f'Error fetching employee details: {e}')
            show_error_message_box(self._view, "خطا", f"خطا در دریافت جزئیات کارمند: {e}")

    def _handle_save_request(self, dialog: EmployeeEditDialog, data: EmployeeFullData, is_edit: bool):
        """Central method to handle validation and saving."""
        try:
            self._logic.save_employee(data)
            dialog.accept()
            self.load_initial_data()
            action_text = "بروزرسانی" if is_edit else "ایجاد"
            show_information_message_box(self._view, "موفقیت",
                                         f"اطلاعات کارمند {data.first_name} {data.last_name} با موفقیت {action_text} شد.")
        except ValueError as ve:
            dialog.show_error(str(ve))
        except Exception as e:
            print(f"Error saving employee data: {e}")
            show_error_message_box(dialog, "خطای سیستمی", f"خطایی در زمان ذخیره رخ داد: {e}")

    def _delete_employee(self, employee_id: str):
        """Handles the 'Delete User' action with confirmation."""

        def confirm_delete_employee(emp_id):
            try:
                self._logic.delete_employee(emp_id)
                self.load_initial_data()  # Refresh table
                show_information_message_box(self._view, "موفقیت", "کاربر با موفقیت حذف شد.")
            except Exception as e:
                show_error_message_box(self._view, "خطا در حذف", str(e))

        show_question_message_box(self._view, title="تایید حذف",
                                  message="آیا از حذف این کاربر اطمینان دارید؟\nاین عمل قابل بازگشت نیست.",
                                  button_1="بله", button_2="خیر",
                                  yes_func=lambda: confirm_delete_employee(employee_id))

    def get_view(self):
        """
        Returns the associated _view for embedding in the main window.
        """
        return self._view
