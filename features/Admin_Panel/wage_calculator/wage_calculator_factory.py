# features/Admin_Panel/wage_calculator/wage_calculator.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.wage_calculator.wage_calculator_controller import WageCalculatorController
from features.Admin_Panel.wage_calculator.wage_calculator_view import WageCalculatorView
from features.Admin_Panel.wage_calculator.wage_calculator_logic import WageCalculatorLogic
from features.Admin_Panel.wage_calculator.wage_calculator_repo import WageCalculatorRepository

from shared.session_provider import ManagedSessionProvider


class WageCalculatorFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(payroll_engine: Engine, invoices_engine: Engine, parent=None) -> WageCalculatorController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            payroll_engine: The SQLAlchemy engine for the payroll database.
            invoices_engine: The SQLAlchemy engine for the invoices database.
            parent: The parent QWidget for the view.
        Returns:
            AdminDashboardController: The fully wired controller instance.
        """
        payroll_session = ManagedSessionProvider(payroll_engine)
        invoices_session = ManagedSessionProvider(invoices_engine)
        # 1. Instantiate the layers, injecting dependencies
        repo = WageCalculatorRepository()
        logic = WageCalculatorLogic(repository=repo,
                                    payroll_engine=payroll_session,
                                    invoices_engine=invoices_session)
        view = WageCalculatorView(parent=parent)

        # 2. Instantiate the Controller, which connects everything
        controller = WageCalculatorController(view, logic)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=WageCalculatorFactory,
        required_engines={'payroll': 'payroll_engine', 'invoices': 'invoices_engine'},
        use_memory_db=True
    )
