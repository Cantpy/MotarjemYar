# features/Admin_Panel/users_management/users_management_controller.py

from features.Admin_Panel.users_management.users_management_view import UsersManagementView
from features.Admin_Panel.users_management.users_management_logic import UserManagementLogic
from features.Admin_Panel.users_management.users_management_dialog import UserAccountDialog
from features.Admin_Panel.users_management.users_management_models import UserData
from shared import show_error_message_box, show_information_message_box, show_question_message_box


class UsersManagementController:
    """
    Controller for the User Management feature, handling interactions between the view and logic.
    """
    def __init__(self, view: UsersManagementView, logic: UserManagementLogic):
        self._view = view
        self._logic = logic
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
            print(f'Error loading users: {e}')
            show_error_message_box(self._view, "خطا", f"خطا در بارگذاری کاربران: {e}")

    def _add_user(self):
        dialog = UserAccountDialog(parent=self._view)
        dialog.save_requested.connect(
            lambda data: self._handle_user_save(dialog, data)
        )
        dialog.exec()

    def _edit_user(self, user_data: UserData):
        dialog = UserAccountDialog(user_data, parent=self._view)
        dialog.save_requested.connect(
            lambda data: self._handle_user_save(dialog, data, is_edit=True)
        )
        dialog.exec()

    def _handle_user_save(self, dialog: UserAccountDialog, data: dict, is_edit: bool = False):
        try:
            editor_username = "admin"
            self._logic.save_user(data, editor_username)

            dialog.accept()
            self.load_users()
            show_information_message_box(self._view, "موفقیت", "اطلاعات کاربر با موفقیت ذخیره شد.")

        except Exception as e:
            print(f'Error saving user: {e}')
            dialog.show_error(str(e))

    def _delete_user(self, user_id: int):
        def confirm_delete():
            try:
                deleter_username = "admin"
                self._logic.delete_user(user_id, deleter_username)
                self.load_users()
                show_information_message_box(self._view, "موفقیت", "کاربر با موفقیت حذف شد.")
            except Exception as e:
                print(f'Error deleting user: {e}')
                show_error_message_box(self._view, "خطا در حذف", str(e))

        show_question_message_box(self._view, "تایید حذف",
                                  "آیا از حذف این کاربر اطمینان دارید؟",
                                  button_1="بله، حذف شود",
                                  button_2="انصراف",
                                  yes_func=confirm_delete)
