# features/Invoice_Page/invoice_details/invoice_details_factory.py

"""
Factory class to create and wire the Invoice Details module components.
"""

from sqlalchemy.engine import Engine

from features.Invoice_Page.invoice_details.invoice_details_view import InvoiceDetailsWidget
from features.Invoice_Page.invoice_details.invoice_details_controller import InvoiceDetailsController
from features.Invoice_Page.invoice_details.invoice_details_logic import InvoiceDetailsLogic
from features.Invoice_Page.invoice_details.invoice_details_repo import InvoiceDetailsRepository
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.invoice_details.invoice_details_settings_dialog import SettingsManager

from shared.session_provider import ManagedSessionProvider


class InvoiceDetailsFactory:
    """
    Factory class to create and wire the Invoice Details module components.
    """
    @staticmethod
    def create(business_engine: Engine,
               state_manager: WorkflowStateManager,
               parent=None) -> InvoiceDetailsController:
        """
        Creates and wires the complete Invoice Details module.
        Args:
            business_engine (Engine): The SQLAlchemy engine for the business database.
            state_manager (WorkflowStateManager): The shared state manager for the invoice workflow.
            parent: The parent QWidget for the view.
        Returns:
            InvoiceDetailsController: The fully configured controller instance.
        """
        business_session = ManagedSessionProvider(engine=business_engine)
        repository = InvoiceDetailsRepository()
        settings_manager = SettingsManager()

        logic = InvoiceDetailsLogic(repo=repository, business_engine=business_session,
                                    settings_manager=settings_manager)
        view = InvoiceDetailsWidget(parent=parent, settings_manager=settings_manager)
        controller = InvoiceDetailsController(view=view, logic=logic, state_manager=state_manager,
                                              settings_manager=settings_manager)

        return controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoiceDetailsFactory,
        required_engines={'business': 'business_engine'},
        use_memory_db=True
    )
