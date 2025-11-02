# features/Admin_Panel/employee_management/employee_management_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.employee_management.employee_management_controller import UserManagementController
from features.Admin_Panel.employee_management.employee_management_view import UserManagementView
from features.Admin_Panel.employee_management.employee_management_logic import UserManagementLogic
from features.Admin_Panel.employee_management.employee_management_repo import EmployeeManagementRepository

from shared.session_provider import ManagedSessionProvider


class EmployeeManagementFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(payroll_engine: Engine, parent=None) -> UserManagementController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            payroll_engine: The SQLAlchemy engine for the payroll database.
            parent: The parent widget.
        Returns:
            AdminDashboardController: The fully wired controller instance.
        """
        payroll_session_provider = ManagedSessionProvider(engine=payroll_engine)
        # 1. Instantiate the layers, injecting dependencies
        repo = EmployeeManagementRepository()
        logic = UserManagementLogic(repository=repo,
                                    payroll_engine=payroll_session_provider)
        view = UserManagementView(parent=parent)

        # 2. Instantiate the Controller, which connects everything
        controller = UserManagementController(view, logic)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=EmployeeManagementFactory,
        required_engines={'payroll': 'payroll_engine'},
        use_memory_db=True
    )
