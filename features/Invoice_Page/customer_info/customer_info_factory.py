# features/Invoice_Page/customer_info/customer_info_factory.py

from sqlalchemy.engine import Engine

from features.Invoice_Page.customer_info.customer_info_view import CustomerInfoWidget
from features.Invoice_Page.customer_info.customer_info_controller import CustomerInfoController
from features.Invoice_Page.customer_info.customer_info_logic import CustomerLogic
from features.Invoice_Page.customer_info.customer_info_repo import CustomerRepository
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

from shared.session_provider import ManagedSessionProvider


class CustomerInfoFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(customer_engine: Engine,
               state_manager: WorkflowStateManager,
               parent=None) -> CustomerInfoController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            customer_engine: The SQLAlchemy engine for the customers database.
            state_manager: The shared state manager for the entire invoice workflow.
            parent: The parent QWidget for the view.

        Returns:
            CustomerInfoController: The fully wired controller instance.
        """
        customer_session = ManagedSessionProvider(engine=customer_engine)

        repo = CustomerRepository()
        logic = CustomerLogic(repo=repo, customer_engine=customer_session)
        view = CustomerInfoWidget(parent=parent)

        controller = CustomerInfoController(logic, view, state_manager)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=CustomerInfoFactory,
        required_engines={'customers': 'customer_engine'},
        use_memory_db=True
    )
