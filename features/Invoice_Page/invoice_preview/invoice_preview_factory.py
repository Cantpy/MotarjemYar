# features/Invoice_Page/invoice_preview/invoice_preview_factory.py

"""
Factory for creating and wiring the InvoicePreview module components.
"""

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
    Factory for creating and wiring the InvoicePreview package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(business_engine: Engine,
               state_manager: WorkflowStateManager,
               parent=None) -> InvoicePreviewController:
        """
        Creates a fully configured InvoicePreview module.
        Args:
            business_engine: The SQLAlchemy engine for the business database.
            state_manager: The shared state manager for the entire invoice workflow.
            parent: The parent QWidget for the view.
        Returns:
            InvoicePreviewController: The fully wired controller instance.
        """
        business_session = ManagedSessionProvider(engine=business_engine)

        settings_manager = PreviewSettingsManager()

        repo = InvoicePreviewRepository()
        logic = InvoicePreviewLogic(repo=repo, business_engine=business_session, settings_manager=settings_manager)
        view = MainInvoicePreviewWidget(parent=parent)

        controller = InvoicePreviewController(view, logic, state_manager)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoicePreviewFactory,
        required_engines={'business': 'business_engine'},
        use_memory_db=True
    )
