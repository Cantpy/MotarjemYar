# features/Services/other_services/other_services_factory.py

from sqlalchemy.engine import Engine

from features.Services.other_services.other_services_view import OtherServicesView
from features.Services.other_services.other_services_controller import OtherServicesController
from features.Services.other_services.other_services_logic import OtherServicesLogic
from features.Services.other_services.other_services_repo import OtherServicesRepository

from shared.session_provider import ManagedSessionProvider


class OtherServicesFactory:
    @staticmethod
    def create(services_engine: Engine, parent=None) -> OtherServicesController:
        """Creates and wires the complete Other Services module."""

        services_session = ManagedSessionProvider(services_engine)
        repo = OtherServicesRepository()
        logic = OtherServicesLogic(repo, services_session)
        view = OtherServicesView(parent)
        controller = OtherServicesController(view, logic)

        controller.load_initial_data()

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=OtherServicesFactory,
        required_engines={'services': 'services_engine'},
        use_memory_db=True
    )
