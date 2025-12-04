# features/Admin_Panel/admin_reports/admin_reports_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.admin_reports.admin_reports_controller import AdminReportsController
from features.Admin_Panel.admin_reports.admin_reports_view import AdminReportsView
from features.Admin_Panel.admin_reports.admin_reports_logic import AdminReportsLogic
from features.Admin_Panel.admin_reports.admin_reports_repo import AdminReportsRepository

from shared.session_provider import ManagedSessionProvider


class AdminReportsFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(business_engine: Engine,
               parent=None) -> AdminReportsController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            business_engine:
            parent:
        Returns:
            AdminDashboardController: The fully wired controller instance.
        """
        business_session = ManagedSessionProvider(business_engine)

        # 1. Instantiate the layers, injecting dependencies
        repo = AdminReportsRepository()
        logic = AdminReportsLogic(repository=repo,
                                  business_engine=business_session)
        view = AdminReportsView(parent=parent)

        # 2. Instantiate the Controller, which connects everything
        controller = AdminReportsController(view, logic)

        controller.load_data()

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=AdminReportsFactory,
        required_engines={'business': 'business_engine'},
        use_memory_db=False
    )
