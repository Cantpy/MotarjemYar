# features/Invoice_Page/invoice_details/invoice_details_factory.py

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
    def create(users_engine: Engine, invoices_engine, parent=None) -> InvoiceDetailsController:
        """
        Creates and wires the complete Invoice Details module.
        """
        users_session = ManagedSessionProvider(engine=users_engine)
        invoices_session = ManagedSessionProvider(engine=invoices_engine)
        repository = InvoiceDetailsRepository()
        settings_manager = SettingsManager()

        logic = InvoiceDetailsLogic(repo=repository, users_engine=users_session, invoices_engine=invoices_session,
                                    settings_manager=settings_manager)
        view = InvoiceDetailsWidget(parent=parent, settings_manager=settings_manager)
        state_manager = WorkflowStateManager()
        controller = InvoiceDetailsController(view=view, logic=logic, state_manager=state_manager,
                                              settings_manager=settings_manager)

        return controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoiceDetailsFactory,
        required_engines={'users': 'users_engine', 'invoices': 'invoices_engine'},
        use_memory_db=True
    )
