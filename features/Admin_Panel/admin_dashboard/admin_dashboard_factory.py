# features/Admin_Panel/admin_dashboard/admin_dashboard_factory.py

import sys
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

from features.Admin_Panel.admin_dashboard.admin_dashboard_controller import AdminDashboardController
from features.Admin_Panel.admin_dashboard.admin_dashboard_view import AdminDashboardView
from features.Admin_Panel.admin_dashboard.admin_dashboard_logic import AdminDashboardLogic
from features.Admin_Panel.admin_dashboard.admin_dashboard_repo import AdminDashboardRepository

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


class AdminDashboardFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(session_provider: SessionProvider) -> AdminDashboardController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            session_provider: The pre-configured, application-wide SessionProvider.

        Returns:
            AdminDashboardController: The fully wired controller instance.
        """

        # 1. Instantiate the layers, injecting dependencies
        repo = AdminDashboardRepository()
        logic = AdminDashboardLogic(repository=repo, session_provider=session_provider)
        view = AdminDashboardView()

        # 2. Instantiate the Controller, which connects everything
        controller = AdminDashboardController(view, logic)

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
    admin_dashboard_info_controller = AdminDashboardFactory.create(
        session_provider=session_provider,
    )

    # --- Run the UI ---
    main_widget = admin_dashboard_info_controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
