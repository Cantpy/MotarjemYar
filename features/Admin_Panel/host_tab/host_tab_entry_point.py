# main.py

import sys
import os
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

# --- Component Imports ---
from features.Admin_Panel.host_tab.host_tab_view import AdminMainWindow
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

# --- Robust Path Handling for resources ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def setup_database_sessions(is_demo: bool, urls: dict):
    """
    Creates engines and sessionmakers for all application databases.
    Handles both in-memory (demo) and file-based (production) modes.
    """
    engines = {}
    connect_args = {"check_same_thread": False}
    all_bases = {
        'invoices': BaseInvoices, 'customers': BaseCustomers, 'services': BaseServices,
        'expenses': BaseExpenses, 'users': BaseUsers, 'payroll': BasePayroll  # <-- Add payroll
    }

    for key, url in urls.items():
        if is_demo:
            engines[key] = create_engine(f"sqlite:///{url}", connect_args=connect_args, poolclass=StaticPool)
        else:
            engines[key] = create_engine(f"sqlite:///{url}")

        if key in all_bases:
            # This will now create the 'employees' table on the payroll engine
            all_bases[key].metadata.create_all(engines[key])

    sessions = {key: sessionmaker(bind=engine) for key, engine in engines.items()}
    return (
        sessions.get('invoices'), sessions.get('customers'), sessions.get('services'),
        sessions.get('expenses'), sessions.get('users'), sessions.get('payroll')
    )


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
    is_demo_mode = "--demo" in sys.argv
    db_urls = {}

    if is_demo_mode:
        print("--- Running in In-Memory DEMO Mode ---")
        # --- FIX: Add 'users' to the in-memory dictionary ---
        db_urls['invoices'] = ":memory:"
        db_urls['customers'] = ":memory:"
        db_urls['services'] = ":memory:"
        db_urls['expenses'] = ":memory:"
        db_urls['users'] = ":memory:"
        db_urls['payroll'] = ":memory:"
    else:
        print("--- Running in Production Mode (using file-based databases) ---")
        db_urls['invoices'] = os.path.join(BASE_DIR, INVOICES_DB_URL)
        db_urls['customers'] = os.path.join(BASE_DIR, CUSTOMERS_DB_URL)
        db_urls['services'] = os.path.join(BASE_DIR, SERVICES_DB_URL)
        db_urls['expenses'] = os.path.join(BASE_DIR, EXPENSES_DB_URL)
        db_urls['users'] = os.path.join(BASE_DIR, USERS_DB_URL)
        db_urls['payroll'] = os.path.join(BASE_DIR, PAYROLL_DB_URL)

    # --- Setup Databases and Get Session Factories ---
    (InvoicesSession, CustomersSession, ServicesSession, ExpensesSession, UsersSession, PayrollSession) = \
        setup_database_sessions(is_demo_mode, db_urls)

    # --- Populate Databases with Mock Data ---
    # The mock data function needs sessions for each database it populates.
    with InvoicesSession() as inv_session, \
            CustomersSession() as cust_session, \
            ServicesSession() as srv_session, \
            ExpensesSession() as exp_session, \
            UsersSession() as usr_session, \
            PayrollSession() as prl_session:

        # --- FIX: Pass all required sessions to the mock data function ---
        create_mock_data(
            invoices_session_factory=InvoicesSession,
            customers_session_factory=CustomersSession,
            services_session_factory=ServicesSession,
            expenses_session_factory=ExpensesSession,
            users_session_factory=UsersSession,
            payroll_session_factory=PayrollSession
        )

    # --- Create and Show the Main Window ---
    # Pass all four session factories to the main window, which will distribute them.
    window = AdminMainWindow(
        invoices_session_factory=InvoicesSession,
        customers_session_factory=CustomersSession,
        services_session_factory=ServicesSession,
        expenses_session_factory=ExpensesSession,
        users_session_factory=UsersSession,
        payroll_session_factory=PayrollSession
    )
    window.show()

    sys.exit(app.exec())
