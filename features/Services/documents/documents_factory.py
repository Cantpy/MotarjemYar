# features/Services/documents/documents_factory.py

import sys
from sqlalchemy import create_engine
from PySide6.QtWidgets import QApplication

from features.Services.documents.documents_view import ServicesDocumentsView
from features.Services.documents.documents_controller import ServicesController
from features.Services.documents.documents_logic import ServicesLogic
from features.Services.documents.documents_repo import ServiceRepository

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


class ServicesDocumentFactory:
    """Factory to create and wire up the Services/Documents module components."""
    @staticmethod
    def create(session_provider: SessionProvider, parent=None) -> ServicesController:
        """
        Creates, configures, and connects the entire Services/Documents module.
        """
        # 1. Create the data and _logic layers
        repository = ServiceRepository()
        logic = ServicesLogic(
            repo=repository,
            session_provider=session_provider
        )

        # 2. Create the View (it's now dumb)
        view = ServicesDocumentsView(parent=parent)

        # 3. Create the Controller, injecting the _view and _logic
        controller = ServicesController(
            view=view,
            logic=logic
        )

        # 4. Perform initial data load
        controller.load_initial_data()

        # 5. Return the final widget to be displayed
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
    controller = ServicesDocumentFactory.create(
        session_provider=session_provider,
    )

    # --- Run the UI ---
    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
