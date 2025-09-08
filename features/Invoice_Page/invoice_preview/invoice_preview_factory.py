# features/Invoice_Page/invoice_preview/invoice_preview_factory.py

import sys
from typing import Dict

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

# --- Import MVC & Model Components ---
from features.Invoice_Page.invoice_preview.invoice_preview_view import MainInvoicePreviewWidget
from features.Invoice_Page.invoice_preview.invoice_preview_controller import InvoicePreviewController
from features.Invoice_Page.invoice_preview.invoice_preview_logic import InvoicePreviewLogic
from features.Invoice_Page.invoice_preview.invoice_preview_repo import InvoicePreviewRepository
# Import DTOs needed for the mock state manager
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails, OfficeInfo
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem, Service

from shared.assets import INVOICES_DB_URL, USERS_DB_URL, CUSTOMERS_DB_URL
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.customer_models import BaseCustomers
from shared.orm_models.users_models import BaseUsers
from shared.mock_data.populate_invoices import populate_invoices_db


# --- 2. Mock State Manager ---
class MockStateManager:
    def __init__(self):
        self._customer = None
        self._details = None
        self._assignments = None

    def get_customer(self): return self._customer

    def get_invoice_details(self): return self._details

    def get_assignments(self): return self._assignments


# --- 3. Application-Wide Session Provider ---
class SessionProvider:
    def __init__(self, engines: Dict[str, Engine]):
        self.invoices = sessionmaker(autocommit=False, bind=engines.get('invoices'))
        self.users = sessionmaker(autocommit=False, bind=engines.get('users'))
        self.customers = sessionmaker(autocommit=False, bind=engines.get('customers'))


# --- 4. The Clean Factory ---
class InvoicePreviewFactory:
    @staticmethod
    def create(session_provider: SessionProvider, state_manager=None) -> InvoicePreviewController:
        repo = InvoicePreviewRepository()
        logic = InvoicePreviewLogic(repo, session_provider)
        view = MainInvoicePreviewWidget()
        manager = state_manager if state_manager is not None else MockStateManager()
        controller = InvoicePreviewController(view, logic, manager)
        return controller


# --- 6. Main Execution Block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Application Setup ---
    invoices_engine = create_engine(f"sqlite:///{INVOICES_DB_URL}")
    users_engine = create_engine(f"sqlite:///{USERS_DB_URL}")
    customers_engine = create_engine(f"sqlite:///{CUSTOMERS_DB_URL}")
    BaseInvoices.metadata.create_all(invoices_engine)
    BaseUsers.metadata.create_all(users_engine)
    BaseCustomers.metadata.create_all(customers_engine)
    session_provider = SessionProvider({'invoices': invoices_engine,
                                        'users': users_engine,
                                        'customers': customers_engine})
    populate_invoices_db(session_provider.invoices(), session_provider.customers(), session_provider.users())

    # --- SIMULATE previous steps providing data ---
    mock_state_manager = MockStateManager()
    mock_state_manager._customer = Customer(name="مشتری آزمایشی")
    mock_state_manager._details = InvoiceDetails(invoice_number=1001, issue_date="2025/09/07", user="Admin",
                                                 office_info=OfficeInfo(name="دفتر نمونه"))
    mock_state_manager._assignments = {
        "مترجم الف": [InvoiceItem(service=Service(name="شناسنامه", type="", base_price=150000), is_official=True,
                                  has_judiciary_seal=True, total_price=150000)],
        "مترجم ب": [InvoiceItem(service=Service(name="کارت ملی", type="", base_price=500000),
                                is_official=False, total_price=80000)]
    }

    # --- Factory Usage ---
    preview_controller = InvoicePreviewFactory.create(session_provider, mock_state_manager)
    preview_controller.prepare_and_display_data()

    # --- Run the UI ---
    main_widget = preview_controller.get_view()
    main_widget.show()
    sys.exit(app.exec())
