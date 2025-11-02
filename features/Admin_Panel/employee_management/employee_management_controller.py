# features/Admin_Panel/employee_management/employee_management_controller.py

from features.Admin_Panel.employee_management.employee_management_dialog import EmployeeEditDialog
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

    def load_initial_data(self):
        """Fetches all users and populates the main table."""
        try:
            employees = self._logic.get_all_employees_for_display()
            self._view.populate_employee_table(employees)
        except Exception as e:
            print(f"Error loading users: {e}")
            show_error_message_box(self._view, "خطا", "خطایی در بارگذاری لیست کاربران رخ داد.")

    def _add_employee(self):
        """Handles the 'Add User' action using a signal-based dialog."""
        dialog = EmployeeEditDialog(parent=self._view)
        dialog.save_requested.connect(
            lambda data: self._handle_save_request(dialog, data, is_edit=False)
        )
        dialog.exec()

    def _edit_employee(self, employee_data: EmployeeFullData):
        """Handles the 'Edit User' action using a signal-based dialog."""
        dialog = EmployeeEditDialog(employee_data, parent=self._view)
        # MODIFIED: Connect to the dialog's save signal
        dialog.save_requested.connect(
            lambda data: self._handle_save_request(dialog, data, is_edit=True)
        )
        dialog.exec()

    def _handle_save_request(self, dialog: EmployeeEditDialog, data: EmployeeFullData, is_edit: bool):
        """
        MODIFIED: Central method to handle validation and saving.
        This keeps the dialog open on failure.
        """
        try:
            self._logic.save_employee(data)

            # If logic succeeds, close the dialog and show success message
            dialog.accept()
            self.load_initial_data()

            if is_edit:
                show_information_message_box(self._view, "موفقیت",
                                             f"اطلاعات کارمند {data.username} با موفقیت بروزرسانی شد.")
            else:
                show_information_message_box(self._view, "موفقیت",
                                             f"کارمند {data.first_name} {data.last_name} با موفقیت ایجاد شد.")
        except Exception as e:
            # If logic fails, show the error message INSIDE the dialog
            dialog.show_error(str(e))

    def _delete_employee(self, employee_id: str, national_id: str):
        """Handles the 'Delete User' action with confirmation."""

        def confirm_delete_employee(emp_id, nat_id):
            try:
                self._logic.delete_employee(emp_id, nat_id)
                self.load_initial_data()  # Refresh table
                show_information_message_box(self._view, "موفقیت", "کاربر با موفقیت حذف شد.")
            except Exception as e:
                show_error_message_box(self._view, "خطا در حذف", str(e))

        show_question_message_box(self._view, title="تایید حذف",
                                  message="آیا از حذف این کاربر اطمینان دارید؟\nاین عمل قابل بازگشت نیست.",
                                  button_1="بله", button_2="خیر",
                                  yes_func=lambda: confirm_delete_employee(employee_id, national_id))

    def get_view(self):
        """
        Returns the associated _view for embedding in the main window.
        """
        return self._view
