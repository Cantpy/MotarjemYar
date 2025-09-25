# features/Admin_Panel/host_tab/host_tab_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.host_tab.admin_panel_controller import AdminMainWindowController
from features.Admin_Panel.host_tab.admin_panel_view import AdminMainWindowView
from features.Admin_Panel.host_tab.admin_panel_logic import AdminMainWindowService


class AdminPanelFactory:
    """
    The master factory that assembles the entire invoice creation workflow.
    """

    @staticmethod
    def create(users_engine: Engine,
               payroll_engine: Engine,
               expenses_engine: Engine,
               customers_engine: Engine,
               invoices_engine: Engine,
               services_engine: Engine,
               parent=None) -> AdminMainWindowController:
        """
        Creates a fully configured Admin Panel module by assembling its components.
        """

        admin_panel_view = AdminMainWindowView(parent=parent)
        admin_panel_logic = AdminMainWindowService(
            users_engine=users_engine,
            payroll_engine=payroll_engine,
            expenses_engine=expenses_engine,
            customers_engine=customers_engine,
            invoices_engine=invoices_engine,
            services_engine=services_engine
        )
        admin_panel_controller = AdminMainWindowController(
            view=admin_panel_view,
            logic=admin_panel_logic,
        )

        return admin_panel_controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=AdminPanelFactory,
        required_engines={'users': 'users_engine', 'payroll': 'payroll_engine',
                          'expenses': 'expenses_engine', 'customers': 'customers_engine',
                          'invoices': 'invoices_engine', 'services': 'services_engine'},
        use_memory_db=True
    )
