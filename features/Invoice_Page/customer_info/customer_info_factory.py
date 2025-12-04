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
    def create(business_engine: Engine,
               state_manager: WorkflowStateManager,
               parent=None) -> CustomerInfoController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            business_engine: The SQLAlchemy engine for the business database.
            state_manager: The shared state manager for the entire invoice workflow.
            parent: The parent QWidget for the view.

        Returns:
            CustomerInfoController: The fully wired controller instance.
        """
        business_session = ManagedSessionProvider(engine=business_engine)

        repo = CustomerRepository()
        logic = CustomerLogic(repo=repo, business_engine=business_session)
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
