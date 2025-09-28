# features/Services/documents/documents_factory.py

from sqlalchemy import Engine

from features.Services.documents.documents_view import ServicesDocumentsView
from features.Services.documents.documents_controller import ServicesController
from features.Services.documents.documents_logic import ServicesLogic
from features.Services.documents.documents_repo import ServiceRepository

from shared.session_provider import ManagedSessionProvider


class ServicesDocumentFactory:
    """Factory to create and wire up the Services/Documents module components."""
    @staticmethod
    def create(services_engine: Engine, parent=None) -> ServicesController:
        """
        Builds the module, creating its own session provider from the given engine.
        """
        services_session = ManagedSessionProvider(engine=services_engine)
        repo = ServiceRepository()
        logic = ServicesLogic(repo=repo, services_engine=services_session)
        view = ServicesDocumentsView(parent)

        controller = ServicesController(view=view, logic=logic)
        controller.load_initial_data()

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=ServicesDocumentFactory,
        required_engines={'services': 'services_engine'},
        use_memory_db=True
    )

