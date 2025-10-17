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
    def create(invoices_engine: Engine,
               services_engine: Engine,
               expenses_engine: Engine,
               customers_engine: Engine,
               parent=None) -> AdminReportsController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            invoices_engine:
            services_engine:
            expenses_engine:
            customers_engine:
        Returns:
            AdminDashboardController: The fully wired controller instance.
        """
        invoices_session = ManagedSessionProvider(invoices_engine)
        services_session = ManagedSessionProvider(services_engine)
        expenses_session = ManagedSessionProvider(expenses_engine)
        customers_session = ManagedSessionProvider(customers_engine)

        # 1. Instantiate the layers, injecting dependencies
        repo = AdminReportsRepository()
        logic = AdminReportsLogic(repository=repo,
                                  invoices_engine=invoices_session,
                                  services_engine=services_session,
                                  expenses_engine=expenses_session,
                                  customer_engine=customers_session)
        view = AdminReportsView(parent=parent)

        # 2. Instantiate the Controller, which connects everything
        controller = AdminReportsController(view, logic)

        controller.load_data()

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=AdminReportsFactory,
        required_engines={'invoices': 'invoices_engine', 'services': 'services_engine',
                          'expenses': 'expenses_engine', 'customers': 'customers_engine'},
        use_memory_db=False
    )
