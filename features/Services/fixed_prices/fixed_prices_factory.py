# features/Services/fixed_prices/fixed_prices_factory.py

from sqlalchemy.engine import Engine

from features.Services.fixed_prices.fixed_prices_view import FixedPricesView
from features.Services.fixed_prices.fixed_prices_controller import FixedPricesController
from features.Services.fixed_prices.fixed_prices_logic import FixedPricesLogic
from features.Services.fixed_prices.fixed_prices_repo import FixedPricesRepository

from shared.session_provider import ManagedSessionProvider


class FixedPricesFactory:
    """Factory class to create and wire the Fixed Prices module components."""
    @staticmethod
    def create(services_engine: Engine, parent=None) -> FixedPricesController:
        """Creates and wires the complete Fixed Prices module."""
        services_session = ManagedSessionProvider(services_engine)
        repo = FixedPricesRepository()
        logic = FixedPricesLogic(repo, services_session)
        view = FixedPricesView(parent)
        controller = FixedPricesController(view, logic)

        controller.load_initial_data()

        return controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=FixedPricesFactory,
        required_engines={'services': 'services_engine'},
        use_memory_db=True
    )
