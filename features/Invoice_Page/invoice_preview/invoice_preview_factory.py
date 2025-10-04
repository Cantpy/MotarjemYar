# features/Invoice_Page/invoice_preview/invoice_preview_factory.py

from sqlalchemy import Engine

from features.Invoice_Page.invoice_preview.invoice_preview_view import MainInvoicePreviewWidget
from features.Invoice_Page.invoice_preview.invoice_preview_controller import InvoicePreviewController
from features.Invoice_Page.invoice_preview.invoice_preview_logic import InvoicePreviewLogic
from features.Invoice_Page.invoice_preview.invoice_preview_repo import InvoicePreviewRepository
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page.invoice_preview.invoice_preview_settings_manager import PreviewSettingsManager

from shared.session_provider import ManagedSessionProvider


class InvoicePreviewFactory:
    """

    """
    @staticmethod
    def create(invoices_engine: Engine,
               state_manager: WorkflowStateManager,
               parent=None) -> InvoicePreviewController:
        """

        """
        invoices_session = ManagedSessionProvider(engine=invoices_engine)

        settings_manager = PreviewSettingsManager()

        repo = InvoicePreviewRepository()
        logic = InvoicePreviewLogic(repo=repo, invoices_engine=invoices_session, settings_manager=settings_manager)
        view = MainInvoicePreviewWidget(parent=parent)

        controller = InvoicePreviewController(view, logic, state_manager)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoicePreviewFactory,
        required_engines={'invoices': 'invoices_engine'},
        use_memory_db=True
    )
