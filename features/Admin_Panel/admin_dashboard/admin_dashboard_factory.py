# features/Admin_Panel/admin_dashboard/admin_dashboard_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.admin_dashboard.admin_dashboard_controller import AdminDashboardController
from features.Admin_Panel.admin_dashboard.admin_dashboard_view import AdminDashboardView
from features.Admin_Panel.admin_dashboard.admin_dashboard_logic import AdminDashboardLogic
from features.Admin_Panel.admin_dashboard.admin_dashboard_repo import AdminDashboardRepository

from shared.session_provider import ManagedSessionProvider


class AdminDashboardFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(business_engine: Engine, parent=None) -> AdminDashboardController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            business_engine: The SQLAlchemy engine for the business database.
            parent: The parent QWidget for the view.
        Returns:
            AdminDashboardController: The fully wired controller instance.
        """

        business_session = ManagedSessionProvider(engine=business_engine)

        repo = AdminDashboardRepository()
        logic = AdminDashboardLogic(repository=repo,
                                    business_engine=business_session)
        view = AdminDashboardView(parent=parent)

        # 2. Instantiate the Controller, which connects everything
        controller = AdminDashboardController(view, logic)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=AdminDashboardFactory,
        required_engines={'business': 'business_engine'},
        use_memory_db=True
    )
