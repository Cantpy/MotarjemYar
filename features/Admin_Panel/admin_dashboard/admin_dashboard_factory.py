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
    def create(invoices_engine: Engine, customers_engine: Engine, parent=None) -> AdminDashboardController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            invoices_engine: The SQLAlchemy engine for the invoices database.
            customers_engine: The SQLAlchemy engine for the customers database.
            parent: The parent QWidget for the view.
        Returns:
            AdminDashboardController: The fully wired controller instance.
        """

        customers_session = ManagedSessionProvider(engine=customers_engine)
        invoices_session = ManagedSessionProvider(engine=invoices_engine)

        repo = AdminDashboardRepository()
        logic = AdminDashboardLogic(repository=repo,
                                    invoices_engine=invoices_session,
                                    customers_engine=customers_session)
        view = AdminDashboardView(parent=parent)

        # 2. Instantiate the Controller, which connects everything
        controller = AdminDashboardController(view, logic)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=AdminDashboardFactory,
        required_engines={'customers': 'customer_engine', 'invoices': 'invoices_engine'},
        use_memory_db=True
    )
