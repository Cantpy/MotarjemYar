# features/Invoice_Page/invoice_details/invoice_details_factory.py

import sys
from typing import Dict

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, Column, String, Integer, func, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.future import select

# --- Import Your Refactored MVC Components ---
from features.Invoice_Page.invoice_details.invoice_details_view import InvoiceDetailsWidget
from features.Invoice_Page.invoice_details.invoice_details_controller import InvoiceDetailsController
from features.Invoice_Page.invoice_details.invoice_details_logic import (InvoiceDetailsLogic)
from features.Invoice_Page.invoice_details.invoice_details_repo import InvoiceDetailsRepository
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem, Service
from features.Invoice_Page.customer_info.customer_info_models import Customer
from shared.assets import USERS_DB_URL, INVOICES_DB_URL, CUSTOMERS_DB_URL
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.users_models import BaseUsers
from shared.orm_models.customer_models import BaseCustomers
from shared.mock_data.populate_invoices import populate_invoices_db


# --- 2. Mock State Manager ---
class MockStateManager:
    def set_invoice_details(self, details):
        print(f"[StateManager] Invoice Details updated for Invoice #{details.invoice_number}")


# --- 3. Application-Wide Session Provider ---
class SessionProvider:
    def __init__(self, engines: Dict[str, Engine]):
        self._engines = engines
        self.invoices = self._create_session_maker('invoices')
        self.users = self._create_session_maker('users')
        self.customers = self._create_session_maker('customers')
        # ... other sessions

    def _create_session_maker(self, name: str) -> sessionmaker:
        engine = self._engines.get(name)
        return sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


# --- 4. The Clean Invoice Details Factory ---
class InvoiceDetailsFactory:
    @staticmethod
    def create(session_provider: SessionProvider, state_manager=None) -> InvoiceDetailsController:
        repo = InvoiceDetailsRepository()
        logic = InvoiceDetailsLogic(repo, session_provider)
        view = InvoiceDetailsWidget()
        manager = state_manager if state_manager is not None else MockStateManager()
        controller = InvoiceDetailsController(view, logic, manager)
        return controller


# --- 6. Main Execution Block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Application Setup ---
    users_engine = create_engine(f"sqlite:///{USERS_DB_URL}")
    invoices_engine = create_engine(f"sqlite:///{INVOICES_DB_URL}")
    customers_engine = create_engine(f"sqlite:///{CUSTOMERS_DB_URL}")
    BaseUsers.metadata.create_all(users_engine)
    BaseInvoices.metadata.create_all(invoices_engine)
    BaseCustomers.metadata.create_all(customers_engine)

    app_engines = {'users': users_engine, 'invoices': invoices_engine, 'customers': customers_engine}
    session_provider = SessionProvider(app_engines)
    populate_invoices_db(session_provider.invoices(), session_provider.customers(), session_provider.users())
    mock_state_manager = MockStateManager()

    # --- Factory Usage ---
    details_controller = InvoiceDetailsFactory.create(session_provider, mock_state_manager)

    # --- SIMULATE previous steps providing data ---
    mock_customer = Customer(name="آقای مشتری", national_id="0011223344", phone="09123456789")
    mock_items = [
        InvoiceItem(service=Service(name="شناسنامه", type="ترجمه", base_price=100000), quantity=2,
                    translation_price=200000),
        InvoiceItem(service=Service(name="مهر", type="تاییدات", base_price=0), quantity=1, judiciary_seal_price=70000)
    ]
    # This is the crucial step to kick things off
    details_controller.prepare_and_display_data(mock_customer, mock_items)

    # --- Run the UI ---
    main_widget = details_controller.get_view()
    main_widget.show()
    sys.exit(app.exec())
