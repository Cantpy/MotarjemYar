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
    app = QApplication(sys.argv)

    customers_engine = create_engine(f"sqlite:///{CUSTOMERS_DB_URL}")
    invoices_engine = create_engine(f"sqlite:///{INVOICES_DB_URL}")
    services_engine = create_engine(f"sqlite:///{SERVICES_DB_URL}")
    expenses_engine = create_engine(f"sqlite:///{EXPENSES_DB_URL}")
    users_engine = create_engine(f"sqlite:///{USERS_DB_URL}")
    payroll_engine = create_engine(f"sqlite:///{PAYROLL_DB_URL}")

    # 2. Create the tables in the database
    BaseCustomers.metadata.create_all(customers_engine)
    BaseInvoices.metadata.create_all(invoices_engine)
    BaseServices.metadata.create_all(services_engine)
    BaseExpenses.metadata.create_all(expenses_engine)
    BaseUsers.metadata.create_all(users_engine)
    BasePayroll.metadata.create_all(payroll_engine)

    # 3. Create the application-wide SessionProvider instance
    app_engines = {
        'customers': customers_engine,
        'invoices': invoices_engine,
        'services': services_engine,
        'expenses': expenses_engine,
        'users': users_engine,
        'payroll': payroll_engine,
    }
    session_provider = SessionProvider(app_engines)

    create_mock_data(session_provider.invoices, session_provider.customers,
                     session_provider.services, session_provider.expenses,
                     session_provider.users, session_provider.payroll)

    # --- Factory Usage Phase ---
    # Now, we use the clean factory, passing in the dependencies we just created.
    controller = FixedPricesFactory.create(
        session_provider=session_provider,
    )

    # --- Run the UI ---
    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())

