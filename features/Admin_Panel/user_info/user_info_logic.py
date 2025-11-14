from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from features.Admin_Panel.user_info.users_info_repo import UserInfoRepository
from shared.orm_models.users_models import UsersData


class UserInfoLogic:
    """
    Handles the business logic for the User Info feature.
    """

    def __init__(self, engine: Engine, repository: UserInfoRepository, current_user_id: int):
        self._engine = engine
        self._repository = repository
        self._user_id = current_user_id

    def get_user_data(self) -> UsersData | None:
        """
        Fetches data for the current user and returns it as a DTO.
        """
        try:
            with Session(self._engine) as session:
                user_orm = self._repository.get_user_by_id(session, self._user_id)
                if user_orm:
                    return UsersData(
                        id=user_orm.id,
                        username=user_orm.username,
                        password_hash=user_orm.password_hash,
                        role=user_orm.role,
                        active=user_orm.active,
                        display_name=user_orm.display_name,
                        avatar_path=user_orm.avatar_path,
                        start_date=user_orm.start_date,
                        end_date=user_orm.end_date,
                        token_hash=user_orm.token_hash,
                        expires_at=user_orm.expires_at,
                        created_at=user_orm.created_at,
                        updated_at=user_orm.updated_at,
                        failed_login_attempts=user_orm.failed_login_attempts,
                        lockout_until_utc=user_orm.lockout_until_utc
                    )
        except Exception as e:
            print(f"Error fetching user data: {e}")
        return None

    def save_user_data(self, user_dto: UsersData) -> bool:
        """
        Saves updated user data from a DTO to the database.
        """
        data_to_update = {
            "display_name": user_dto.display_name,
            "role": user_dto.role,
            "active": 1 if user_dto.active else 0,
            "avatar_path": user_dto.avatar_path
        }

        try:
            with Session(self._engine) as session:
                success = self._repository.update_user(session, self._user_id, data_to_update)
                if success:
                    session.commit()
                    return True
                else:
                    session.rollback()
                    return False
        except Exception as e:
            print(f"Error saving user data: {e}")
            return False
