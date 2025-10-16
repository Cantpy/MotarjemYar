# features/Admin_Panel/admin_panel/admin_panel_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.admin_panel.admin_panel_controller import AdminPanelController
from features.Admin_Panel.admin_panel.admin_panel_view import AdminPanelView


class AdminPanelFactory:
    """
    Factory for creating the main Admin Panel container.
    """
    @staticmethod
    def create(invoices_engine: Engine, customers_engine: Engine,
               services_engine: Engine, expenses_engine: Engine,
               payroll_engine: Engine, users_engine: Engine,
               parent=None) -> AdminPanelController:
        """
        Creates a fully configured Admin Panel by assembling all its sub-features.
        This method requires all engines needed by its children.
        """
        # A dictionary of engines to pass to the controller for clean access
        engines = {
            'invoices': invoices_engine,
            'customers': customers_engine,
            'services': services_engine,
            'expenses': expenses_engine,
            'payroll': payroll_engine,
            'users': users_engine,
        }

        view = AdminPanelView(parent=parent)
        controller = AdminPanelController(view=view, engines=engines)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test

    launch_feature_for_ui_test(
        factory_class=AdminPanelFactory,
        required_engines={
            'invoices': 'invoices_engine',
            'customers': 'customers_engine',
            'services': 'services_engine',
            'expenses': 'expenses_engine',
            'payroll': 'payroll_engine',
            'users': 'users_engine'
        },
        use_memory_db=True
    )
