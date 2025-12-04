# features/Admin_Panel/admin_panel/admin_panel_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.admin_panel.admin_panel_controller import AdminPanelController
from features.Admin_Panel.admin_panel.admin_panel_view import AdminPanelView


class AdminPanelFactory:
    """
    Factory for creating the main Admin Panel container.
    """
    @staticmethod
    def create(business_engine: Engine, payroll_engine: Engine, parent=None) -> AdminPanelController:
        """
        Creates a fully configured Admin Panel by assembling all its sub-features.
        This method requires all engines needed by its children.
        """
        # A dictionary of engines to pass to the controller for clean access
        engines = {
            'business': business_engine,
            'payroll': payroll_engine
        }

        view = AdminPanelView(parent=parent)
        controller = AdminPanelController(view=view, engines=engines)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test

    launch_feature_for_ui_test(
        factory_class=AdminPanelFactory,
        required_engines={
            'business': 'business_engine',
            'payroll': 'payroll_engine'
        },
        use_memory_db=True
    )
