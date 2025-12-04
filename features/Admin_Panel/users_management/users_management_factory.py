# features/Admin_Panel/users_management/users_management_factory.py

from sqlalchemy.engine import Engine
from shared.session_provider import ManagedSessionProvider
from features.Admin_Panel.users_management.users_management_controller import UsersManagementController
from features.Admin_Panel.users_management.users_management_view import UsersManagementView
from features.Admin_Panel.users_management.users_management_logic import UserManagementLogic
from features.Admin_Panel.users_management.users_management_repo import UserManagementRepository


class UsersManagementFactory:
    """
    Factory for creating the User Management feature.
    """
    @staticmethod
    def create(business_engine: Engine, parent=None) -> UsersManagementController:
        """
        Creates and wires all components for the User Management feature.
        """
        business_session = ManagedSessionProvider(engine=business_engine)
        repo = UserManagementRepository()
        logic = UserManagementLogic(repository=repo, users_engine=business_session)
        view = UsersManagementView(parent=parent)
        controller = UsersManagementController(view, logic)
        return controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test

    launch_feature_for_ui_test(
        factory_class=UsersManagementFactory,
        required_engines={'business': 'business_engine'},
        use_memory_db=True
    )
