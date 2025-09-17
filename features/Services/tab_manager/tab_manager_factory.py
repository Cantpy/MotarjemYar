# services_management/factory.py


from features.Services.tab_manager.tab_manager_view import ServicesManagementView
from features.Services.tab_manager.tab_manager_controller import ServicesManagementController

# --- IMPORTANT: Import the FACTORIES for each sub-module ---
from features.Services.documents.documents_factory import ServicesDocumentFactory
from features.Services.fixed_prices.fixed_prices_factory import FixedPricesFactory
from features.Services.other_services.other_services_factory import OtherServicesFactory

from shared.session_provider import SessionProvider


class ServicesManagementFactory:
    """
    The main factory for creating the entire Services Management module.
    It builds and returns the main controller, which holds the final _view.
    """

    @staticmethod
    def create(session_provider: "SessionProvider", parent=None) -> ServicesManagementController:
        """
        Builds the complete, interactive Services Management module.
        """
        # 1. Create the main container _view. It's dumb.
        container_view = ServicesManagementView(parent)

        # 2. Use the specialized factories to build each sub-module's CONTROLLER.
        documents_controller = ServicesDocumentFactory.create(session_provider, container_view)
        fixed_prices_controller = FixedPricesFactory.create(session_provider, container_view)
        other_services_controller = OtherServicesFactory.create(session_provider, container_view)

        # 3. Get the VIEW from each sub-controller and add it to the container's tab widget.
        container_view.add_tab(documents_controller.get_view(), "مدارک")
        container_view.add_tab(fixed_prices_controller.get_view(), "هزینه‌های ثابت")
        container_view.add_tab(other_services_controller.get_view(), "خدمات دیگر")

        # 4. Create the main controller, INJECTING the container _view AND all the sub-controllers.
        main_controller = ServicesManagementController(
            view=container_view,
            documents_controller=documents_controller,
            fixed_prices_controller=fixed_prices_controller,
            other_services_controller=other_services_controller
        )

        # 5. Return the final, assembled main controller.
        return main_controller


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    from sqlalchemy import create_engine
    from shared.assets import (
        CUSTOMERS_DB_URL, INVOICES_DB_URL, SERVICES_DB_URL, EXPENSES_DB_URL, USERS_DB_URL, PAYROLL_DB_URL)
    from shared.orm_models.customer_models import BaseCustomers
    from shared.orm_models.invoices_models import BaseInvoices
    from shared.orm_models.services_models import BaseServices
    from shared.orm_models.expenses_models import BaseExpenses
    from shared.orm_models.users_models import BaseUsers
    from shared.orm_models.payroll_models import BasePayroll
    from shared.mock_data.mock_data_generator import create_mock_data

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

    # Create the Services Management widget using the factory
    services_management_controller = ServicesManagementFactory.create(session_provider)
    services_management_widget = services_management_controller.get_view()
    services_management_widget.show()

    sys.exit(app.exec())
