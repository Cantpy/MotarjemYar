# features/Invoice_Page/invoice_preview/invoice_preview_factory.py

from sqlalchemy import Engine

from features.Invoice_Page.invoice_preview.invoice_preview_view import MainInvoicePreviewWidget
from features.Invoice_Page.invoice_preview.invoice_preview_controller import InvoicePreviewController
from features.Invoice_Page.invoice_preview.invoice_preview_logic import InvoicePreviewLogic
from features.Invoice_Page.invoice_preview.invoice_preview_repo import InvoicePreviewRepository
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

from shared.session_provider import ManagedSessionProvider


class InvoicePreviewFactory:
    """

    """
    @staticmethod
    def create(invoices_engine: Engine, parent=None) -> InvoicePreviewController:
        """

        """
        invoices_session = ManagedSessionProvider(engine=invoices_engine)

        repo = InvoicePreviewRepository()
        logic = InvoicePreviewLogic(repo=repo, invoices_engine=invoices_session)
        view = MainInvoicePreviewWidget(parent=parent)

        state_manager = WorkflowStateManager()
        controller = InvoicePreviewController(view, logic, state_manager)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoicePreviewFactory,
        required_engines={'invoices': 'invoices_engine'},
        use_memory_db=True
    )
