# features/Admin_Panel/users_management/users_management_logic.py

import bcrypt
import uuid
from datetime import date
from shared.session_provider import ManagedSessionProvider
from features.Admin_Panel.employee_management import employee_management_validator as validator
from features.Admin_Panel.users_management.users_management_models import UserData
from features.Admin_Panel.users_management.users_management_repo import UserManagementRepository
from shared.orm_models.users_models import UsersModel, EditedUsersLogModel


class UserManagementLogic:
    def __init__(self, repository: UserManagementRepository, users_engine: ManagedSessionProvider):
        self._repo = repository
        self._users_session = users_engine

    def _validate_user_data(self, data: UserData, is_edit: bool):
        """Validates user data and raises a ValueError on failure."""
        errors = []
        # MODIFIED: Use display_name and remove national_id validation
        checks = {
            "نام نمایشی": validator.validate_required_field(data.display_name, "نام نمایشی"),
            "نام کاربری": validator.validate_username(data.username),
            "رمز عبور": validator.validate_password(data.password, is_edit)
        }
        for field, (is_valid, error_message) in checks.items():
            if not is_valid:
                errors.append(error_message)

        if errors:
            raise ValueError("لطفا خطاهای زیر را اصلاح کنید:\n\n" + "\n".join(f"• {e}" for e in errors))

    def get_all_users(self) -> list[UserData]:
        """Fetches all users and converts them to DTOs."""
        with self._users_session() as session:
            users_orm = self._repo.get_all_users(session)
            user_list = []
            for u in users_orm:
                # MODIFIED: Adapt DTO creation to the new UsersModel schema
                user_list.append(UserData(
                    user_id=u.id,
                    username=u.username,
                    role=u.role,
                    is_active=bool(u.active),
                    start_date=date.fromisoformat(str(u.start_date)) if u.start_date else None,
                    employee_id=u.employee_id,
                    display_name=u.display_name
                ))
            return user_list

    def save_user(self, data: dict, editor_username: str) -> UserData:
        """Creates or updates a user record and returns the resulting DTO."""
        is_edit = data.get("user_id") is not None

        # MODIFIED: Convert dict to a UserData DTO without national_id and with display_name
        user_dto = UserData(
            user_id=data.get("user_id"),
            username=data.get("username"),
            password=data.get("password"),
            role=data.get("role"),
            is_active=data.get("is_active"),
            display_name=data.get("display_name", "").strip()
        )

        self._validate_user_data(user_dto, is_edit)

        if is_edit:
            return self._update_user(user_dto, editor_username)
        else:
            return self._create_user(user_dto)

    def _create_user(self, data: UserData) -> UserData:
        """Logic for creating a new user."""
        hashed_password = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())
        new_employee_id = str(uuid.uuid4())

        # MODIFIED: Create UsersModel directly with display_name
        user_orm = UsersModel(
            username=data.username,
            password_hash=hashed_password,
            role=data.role,
            active=1 if data.is_active else 0,
            start_date=date.today().isoformat(),
            employee_id=new_employee_id,
            display_name=data.display_name
        )

        with self._users_session() as session:
            if self._repo.get_user_by_username(session, data.username):
                raise ValueError(f"نام کاربری '{data.username}' قبلا استفاده شده است.")
            # MODIFIED: Removed national_id check and UserProfileModel creation
            saved_user_orm = self._repo.save_new_user(session, user_orm)

            # Return a DTO representing the newly created user
            data.user_id = saved_user_orm.id
            data.employee_id = saved_user_orm.employee_id
            data.password = ""  # Clear password
            return data

    def _update_user(self, data: UserData, editor_username: str):
        """Logic for updating an existing user."""
        with self._users_session() as session:
            current_user = self._repo.get_user_by_id(session, data.user_id)
            if not current_user:
                raise ValueError("کاربر برای بروزرسانی یافت نشد.")

            edit_logs = []
            user_changes = {}
            # MODIFIED: Removed profile_changes dictionary

            if current_user.display_name != data.display_name:
                edit_logs.append(EditedUsersLogModel(user_id=data.user_id, editor_username=editor_username,
                                                     field_name='display_name', old_value=current_user.display_name,
                                                     new_value=data.display_name))
                user_changes['display_name'] = data.display_name

            if current_user.role != data.role:
                edit_logs.append(EditedUsersLogModel(user_id=data.user_id, editor_username=editor_username,
                                                     field_name='role', old_value=current_user.role,
                                                     new_value=data.role))
                user_changes['role'] = data.role

            if bool(current_user.active) != data.is_active:
                edit_logs.append(EditedUsersLogModel(user_id=data.user_id, editor_username=editor_username,
                                                     field_name='active', old_value=str(current_user.active),
                                                     new_value=str(1 if data.is_active else 0)))
                user_changes['active'] = 1 if data.is_active else 0

            if data.password:
                new_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())
                edit_logs.append(EditedUsersLogModel(user_id=data.user_id, editor_username=editor_username,
                                                     field_name='password', old_value='********', new_value='********'))
                user_changes['password_hash'] = new_hash

            if user_changes:
                # MODIFIED: Removed profile_changes from the repo call
                self._repo.update_user(session, data.user_id, user_changes, edit_logs)

    def delete_user(self, user_id: int, deleted_by_username: str):
        """Deletes a user and archives their data."""
        with self._users_session() as session:
            user_to_delete = self._repo.get_user_by_id(session, user_id)
            if not user_to_delete:
                raise ValueError("کاربر مورد نظر برای حذف یافت نشد.")
            if user_to_delete.username == deleted_by_username:
                raise ValueError("شما نمی‌توانید حساب کاربری خود را حذف کنید.")

            # Note: The repository's archive_user method must also be updated
            # to read from user_to_delete.display_name instead of a user_profile.
            self._repo.archive_user(session, user_to_delete, deleted_by_username)
