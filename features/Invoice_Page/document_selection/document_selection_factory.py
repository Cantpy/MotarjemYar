# features/Invoice_Page/document_selection/document_selection_factory.py

from sqlalchemy import Engine

from features.Invoice_Page.document_selection.document_selection_view import DocumentSelectionWidget
from features.Invoice_Page.document_selection.document_selection_controller import DocumentSelectionController
from features.Invoice_Page.document_selection.document_selection_logic import DocumentSelectionLogic
from features.Invoice_Page.document_selection.document_selection_repo import DocumentSelectionRepository
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

from shared.session_provider import ManagedSessionProvider


class DocumentSelectionFactory:
    """
    Factory for creating and wiring the DocumentSelection package.
    It receives its dependencies and does not create them.
    """
    @staticmethod
    def create(services_engine: Engine,
               state_manager: WorkflowStateManager,
               parent=None) -> DocumentSelectionController:
        """
        Creates a fully configured DocumentSelection module.

        Args:
            services_engine: The pre-configured, application-wide SessionProvider.
            state_manager: The shared state manager for the entire invoice workflow.
            parent: An optional state manager. If None, a mock one is created.
        """
        services_session = ManagedSessionProvider(engine=services_engine)

        repo = DocumentSelectionRepository()
        logic = DocumentSelectionLogic(repo=repo, services_engine=services_session)
        view = DocumentSelectionWidget(parent=parent)

        controller = DocumentSelectionController(view, logic, state_manager)

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=DocumentSelectionFactory,
        required_engines={'services': 'services_engine'},
        use_memory_db=True
    )
