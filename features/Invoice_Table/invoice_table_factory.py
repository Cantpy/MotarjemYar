import sys
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from features.Invoice_Table.invoice_table_repo import RepositoryManager
from features.Invoice_Table.invoice_table_view import InvoiceTableView
from features.Invoice_Table.invoice_table_logic import (SearchService, InvoiceService, InvoiceExportService,
                                                        SortService, FileService, ValidationService,
                                                        NumberFormatService, BulkOperationService)
from features.Invoice_Table.invoice_table_controller import MainController
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


class InvoiceTableFactory:
    """

    """
    @staticmethod
    def create(session_provider: SessionProvider, parent=None) -> MainController:
        """

        """
        invoice_table_view = InvoiceTableView(parent=parent)
        repo_manager = RepositoryManager()
        search_service = SearchService()
        invoice_service = InvoiceService(repo_manager, session_provider)
        export_service = InvoiceExportService()
        sort_service = SortService()
        file_service = FileService()
        validation_service = ValidationService()
        formatting_srvice = NumberFormatService()
        operation_srvice = BulkOperationService()

        invoice_table_controller = MainController(view=invoice_table_view,
                                                  invoice_service=invoice_service,
                                                  search_service=search_service,
                                                  export_service=export_service,
                                                  sort_service=sort_service,
                                                  file_service=file_service,
                                                  validation_service=validation_service,
                                                  format_service=formatting_srvice,
                                                  operation_service=operation_srvice)

        return invoice_table_controller


if __name__ == "__main__":

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

    controller = InvoiceTableFactory.create(session_provider=session_provider, parent=None)
    view = controller.get_view()
    view.show()
    sys.exit(app.exec())
