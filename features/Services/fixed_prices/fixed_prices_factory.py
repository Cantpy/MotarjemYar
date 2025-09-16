# features/Services/fixed_prices/fixed_prices_factory.py

import sys
from sqlalchemy import create_engine
from PySide6.QtWidgets import QApplication
from features.Services.fixed_prices.fixed_prices_view import FixedPricesView
from features.Services.fixed_prices.fixed_prices_controller import FixedPricesController
from features.Services.fixed_prices.fixed_prices_logic import FixedPricesLogic
from features.Services.fixed_prices.fixed_prices_repo import FixedPricesRepository

from shared.assets import (
    CUSTOMERS_DB_URL, INVOICES_DB_URL, SERVICES_DB_URL, EXPENSES_DB_URL, USERS_DB_URL, PAYROLL_DB_URL)
from shared.orm_models.customer_models import BaseCustomers
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.services_models import BaseServices
from shared.orm_models.expenses_models import BaseExpenses
from shared.orm_models.users_models import BaseUsers
from shared.orm_models.payroll_models import BasePayroll
from shared.mock_data.mock_data_generator import create_mock_data
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
    from core.config import DATABASE_PATHS

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
