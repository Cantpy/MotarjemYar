# features/Admin_Panel/employee_management/employee_management_controller.py

from features.Admin_Panel.employee_management.employee_management_view import UserManagementView, UserEditDialog
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
        self._view.add_employee_requested.connect(self._add_user)
        self._view.edit_employee_requested.connect(self._edit_user)
        self._view.delete_employee_requested.connect(self._delete_user)

    def load_initial_data(self):
        """Fetches all users and populates the main table."""
        try:
            employees = self._logic.get_all_employees_for_display()
            self._view.populate_employee_table(employees)
        except Exception as e:
            print(f"Error loading users: {e}")
            show_error_message_box(self._view, "خطا", "خطایی در بارگذاری لیست کاربران رخ داد.")

    def _add_user(self):
        """Handles the 'Add User' action."""
        dialog = UserEditDialog(parent=self._view)
        if dialog.exec():
            try:
                new_employee_data = dialog.get_data()
                # --- Validation ---
                if not new_employee_data.username or not new_employee_data.password:
                    raise ValueError("نام کاربری و رمز عبور نمی‌توانند خالی باشند.")
                if not new_employee_data.national_id:
                    raise ValueError("کد ملی برای ایجاد لینک کاربری ضروری است.")

                self._logic.save_employee(new_employee_data)
                self.load_initial_data()
                show_information_message_box(self._view, "موفقیت",
                                             f"کارمند {new_employee_data.username} با موفقیت ایجاد شد.")
            except Exception as e:
                show_error_message_box(self._view, "خطا در ایجاد کارمند", str(e))

    def _edit_user(self, user_data: EmployeeFullData):
        """Handles the 'Edit User' action."""
        dialog = UserEditDialog(user_data, parent=self._view)
        if dialog.exec():
            try:
                updated_data = dialog.get_data()
                self._logic.save_employee(updated_data)
                self.load_initial_data()  # Refresh table
                show_information_message_box(self._view, "موفقیت",
                                             f"اطلاعات کارمند {updated_data.username} با موفقیت بروزرسانی شد.")
            except Exception as e:
                show_error_message_box(self._view, "خطا در بروزرسانی", str(e))

    def _delete_user(self, employee_id: str, national_id: str):
        """Handles the 'Delete User' action with confirmation."""

        def confirm_delete_user(emp_id, nat_id):
            try:
                self._logic.delete_employee(emp_id, nat_id)
                self.load_initial_data()  # Refresh table
                show_information_message_box(self._view, "موفقیت", "کاربر با موفقیت حذف شد.")
            except Exception as e:
                show_error_message_box(self._view, "خطا در حذف", str(e))

        show_question_message_box(self._view, title="تایید حذف",
                                  message="آیا از حذف این کاربر اطمینان دارید؟\nاین عمل قابل بازگشت نیست.",
                                  button_1="بله", button_2="خیر",
                                  yes_func=lambda: confirm_delete_user(employee_id, national_id))

    def get_view(self):
        """
        Returns the associated _view for embedding in the main window.
        """
        return self._view
