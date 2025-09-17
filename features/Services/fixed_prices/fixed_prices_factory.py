# features/Services/fixed_prices/fixed_prices_factory.py

from features.Services.fixed_prices.fixed_prices_view import FixedPricesView
from features.Services.fixed_prices.fixed_prices_controller import FixedPricesController
from features.Services.fixed_prices.fixed_prices_logic import FixedPricesLogic
from features.Services.fixed_prices.fixed_prices_repo import FixedPricesRepository

from shared.session_provider import SessionProvider


class FixedPricesFactory:
    """Factory class to create and wire the Fixed Prices module components."""
    @staticmethod
    def create(session_provider: SessionProvider, parent=None) -> FixedPricesController:
        """Creates and wires the complete Fixed Prices module."""
        repo = FixedPricesRepository()
        logic = FixedPricesLogic(repo, session_provider)
        view = FixedPricesView(parent)
        controller = FixedPricesController(view, logic)

        controller.load_initial_data()

        return controller


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    from core.database_init import DatabaseInitializer
    from core.database_seeder import DatabaseSeeder
    from config.config import DATABASE_PATHS

    app = QApplication(sys.argv)

    # 1. Initialize databases
    initializer = DatabaseInitializer()
    session_provider = initializer.setup_file_databases(DATABASE_PATHS)

    # 2. Seed (optional – dev/test mode)
    seeder = DatabaseSeeder(session_provider)
    seeder.seed_initial_data()

    # 3. Use factory
    controller = FixedPricesFactory.create(session_provider=session_provider)

    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
