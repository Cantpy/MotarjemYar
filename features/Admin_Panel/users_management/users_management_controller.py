# features/Admin_Panel/users_management/users_management_controller.py

# === MODIFIED: Import the necessary components for the new workflow ===
from features.Admin_Panel.users_management.users_management_view import UsersManagementView
from features.Admin_Panel.users_management.users_management_logic import UserManagementLogic
from features.Admin_Panel.users_management.users_management_dialog import UserAccountDialog
from features.Admin_Panel.users_management.users_management_models import UserData
from shared import show_error_message_box, show_information_message_box, show_question_message_box

# +++ ADDED: Import the employee dialog and factory for the linking flow +++
from features.Admin_Panel.employee_management.employee_management_factory import EmployeeManagementFactory
from features.Admin_Panel.employee_management.employee_management_dialog import EmployeeEditDialog as EmployeeEditDialog
from features.Admin_Panel.employee_management.employee_management_models import EmployeeFullData


class UsersManagementController:
    # === MODIFIED: The constructor now accepts the payroll_engine to pass to the employee factory ===
    def __init__(self, view: UsersManagementView, logic: UserManagementLogic, payroll_engine):
        self._view = view
        self._logic = logic
        self._payroll_engine = payroll_engine
        self._connect_signals()
        self.load_users()

    def get_view(self) -> UsersManagementView:
        return self._view

    def _connect_signals(self):
        self._view.add_user_requested.connect(self._add_user)
        self._view.edit_user_requested.connect(self._edit_user)
        self._view.delete_user_requested.connect(self._delete_user)

    def load_users(self):
        try:
            users = self._logic.get_all_users()
            self._view.populate_table(users)
        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطا در بارگذاری کاربران: {e}")

    def _add_user(self):
        dialog = UserAccountDialog(parent=self._view)
        # === MODIFIED: Connect to a new handler that includes the linking flow ===
        dialog.save_requested.connect(
            lambda data: self._handle_user_save(dialog, data)
        )
        dialog.exec()

    def _edit_user(self, user_data: UserData):
        # Editing a user does not need the employee linking flow
        dialog = UserAccountDialog(user_data, parent=self._view)
        dialog.save_requested.connect(
            lambda data: self._handle_user_save(dialog, data, is_edit=True)
        )
        dialog.exec()

    # === REFACTORED: Renamed from _handle_save and logic expanded ===
    def _handle_user_save(self, dialog: UserAccountDialog, data: dict, is_edit: bool = False):
        try:
            editor_username = "admin"  # Placeholder

            # The logic layer now returns the created/updated UserData object
            saved_user_data = self._logic.save_user(data, editor_username)

            dialog.accept()
            self.load_users()
            show_information_message_box(self._view, "موفقیت", "اطلاعات کاربر با موفقیت ذخیره شد.")

            # +++ ADDED: The linking flow starts here, only for new users +++
            if not is_edit:
                self._ask_to_create_employee_profile(saved_user_data)

        except Exception as e:
            dialog.show_error(str(e))

    # +++ ADDED: New method to handle the second step of the workflow +++
    def _ask_to_create_employee_profile(self, user_data: UserData):
        """After a user is created, ask if an employee profile should be created too."""

        def create_employee():
            employee_controller = EmployeeManagementFactory.create(
                payroll_engine=self._payroll_engine,
            )

            # Pre-populate the employee DTO with data from the new user
            employee_data = EmployeeFullData(
                employee_id=user_data.employee_id,
                first_name=user_data.display_name.split()[0] if user_data.display_name else "",
                last_name=" ".join(user_data.display_name.split()[1:]) if user_data.display_name else "",
                national_id=user_data.national_id
            )

            # Use the employee controller's method to show the dialog
            employee_controller._add_employee(initial_data=employee_data)

        show_question_message_box(
            self._view,
            title="ایجاد پروفایل کارمندی",
            message="کاربر با موفقیت ایجاد شد.\nآیا می‌خواهید اکنون برای این کاربر پروفایل کارمندی و قرارداد ثبت کنید؟",
            button_1="بله، ادامه",
            button_2="خیر",
            yes_func=create_employee
        )

    def _delete_user(self, user_id: int):
        def confirm_delete():
            try:
                deleter_username = "admin"
                self._logic.delete_user(user_id, deleter_username)
                self.load_users()
                show_information_message_box(self._view, "موفقیت", "کاربر با موفقیت حذف شد.")
            except Exception as e:
                show_error_message_box(self._view, "خطا در حذف", str(e))

        show_question_message_box(self._view, "تایید حذف",
                                  "آیا از حذف این کاربر اطمینان دارید؟",
                                  button_1="بله، حذف شود",
                                  button_2="انصراف",
                                  yes_func=confirm_delete)
