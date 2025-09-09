# main.py

import sys
import os
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

# --- Component Imports ---
from features.Admin_Panel.host_tab.admin_panel_controller import AdminMainWindowController
from features.Admin_Panel.host_tab.admin_panel_view import AdminMainWindowView
from features.Admin_Panel.host_tab.admin_panel_logic import AdminMainWindowService
from shared.fonts.font_manager import FontManager
from shared.mock_data.mock_data_generator import create_mock_data

# --- Configuration and Model Imports ---
from shared.assets import (
    INVOICES_DB_URL, CUSTOMERS_DB_URL, SERVICES_DB_URL, EXPENSES_DB_URL, USERS_DB_URL, PAYROLL_DB_URL
)
# --- Import ALL Base classes ---
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.customer_models import BaseCustomers
from shared.orm_models.services_models import BaseServices
from shared.orm_models.expenses_models import BaseExpenses
from shared.orm_models.users_models import BaseUsers
from shared.orm_models.payroll_models import BasePayroll
from shared.session_provider import SessionProvider

# --- Robust Path Handling for resources ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class AdminPanelFactory:
    """
    The master factory that assembles the entire invoice creation workflow.
    """

    @staticmethod
    def create(session_provider: SessionProvider,
               parent=None) -> AdminMainWindowController:

        # 3. Create the main wizard components
        admin_panel_view = AdminMainWindowView(parent=parent)
        admin_panel_logic = AdminMainWindowService(session_provider)

        # 4. Create the main wizard controller, injecting all its dependencies
        admin_panel_controller = AdminMainWindowController(
            view=admin_panel_view,
            logic=admin_panel_logic,
        )

        return admin_panel_controller


if __name__ == "__main__":
    app = QApplication(sys.argv)
    FontManager.load_fonts()

    # Load stylesheet with a robust path
    qss_path = os.path.join(BASE_DIR, "styles.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: styles.qss not found at {qss_path}. Using default styles.")

    # --- Determine Mode and Database URLs ---
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

    is_demo_mode = "--demo" in sys.argv
    db_urls = {}

    if is_demo_mode:
        print("--- Running in In-Memory DEMO Mode ---")
        db_urls['invoices'] = ":memory:"
        db_urls['customers'] = ":memory:"
        db_urls['services'] = ":memory:"
        db_urls['expenses'] = ":memory:"
        db_urls['users'] = ":memory:"
        db_urls['payroll'] = ":memory:"
    else:
        print("--- Running in Production Mode (using file-based databases) ---")
        db_urls['invoices'] = INVOICES_DB_URL
        db_urls['customers'] = CUSTOMERS_DB_URL
        db_urls['services'] = SERVICES_DB_URL
        db_urls['expenses'] = EXPENSES_DB_URL
        db_urls['users'] = USERS_DB_URL
        db_urls['payroll'] = PAYROLL_DB_URL

        # --- Pass all required sessions to the mock data function ---
        create_mock_data(
            invoices_session_factory=session_provider.invoices,
            customers_session_factory=session_provider.customers,
            services_session_factory=session_provider.services,
            expenses_session_factory=session_provider.expenses,
            users_session_factory=session_provider.users,
            payroll_session_factory=session_provider.payroll
        )

    # --- Create and Show the Main Window ---
    # Pass all four session factories to the main window, which will distribute them.
    controller = AdminPanelFactory.create(
        session_provider
    )
    view = controller.get_view()
    view.show()

    sys.exit(app.exec())
