# features/Invoice_Page/wizard_host/invoice_wizard_factory.py

import sys
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

# --- Import all factories and controllers ---
from features.Invoice_Page.wizard_host.invoice_wizard_view import InvoiceWizardWidget
from features.Invoice_Page.wizard_host.invoice_wizard_controller import InvoiceWizardController
from features.Invoice_Page.wizard_host.invoice_page_wizard_logic import InvoiceWizardLogic

from features.Invoice_Page.customer_info.customer_info_factory import CustomerInfoFactory
from features.Invoice_Page.document_selection.document_selection_factory import DocumentSelectionFactory
from features.Invoice_Page.invoice_details.invoice_details_factory import InvoiceDetailsFactory
from features.Invoice_Page.invoice_preview.invoice_preview_factory import InvoicePreviewFactory
from features.Invoice_Page.document_assignment.document_assignment_view import AssignmentWidget
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

from shared.assets import USERS_DB_URL, SERVICES_DB_URL, CUSTOMERS_DB_URL, INVOICES_DB_URL
from shared.orm_models.services_models import BaseServices
from shared.orm_models.users_models import BaseUsers
from shared.orm_models.invoices_models import BaseInvoices
from shared.orm_models.customer_models import BaseCustomers
from shared.mock_data.populate_invoices import populate_invoices_db
from shared.mock_data.populate_customers import populate_customers_db
from shared.mock_data.populate_services import populate_services_db
from shared.mock_data.populate_users import populate_users_db


class SessionProvider:
    """
    A 'dumb' dependency container that holds pre-configured database engines
    and provides session makers on demand.
    """

    def __init__(self, engines: dict[str, Engine]):
        """
        Initializes the provider with a dictionary of fully-created
        SQLAlchemy Engine objects.
        """
        self._engines = engines

        # Create a session maker for each engine
        self.invoices = self._create_session_maker('invoices')
        self.customers = self._create_session_maker('customers')
        self.services = self._create_session_maker('services')
        self.users = self._create_session_maker('users')

    def _create_session_maker(self, name: str) -> sessionmaker:
        """Helper to create a session maker from a stored engine."""
        engine = self._engines.get(name)  # This will now be a REAL Engine object
        if not engine:
            raise ValueError(f"Engine '{name}' was not provided during initialization.")

        return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class InvoiceWizardFactory:
    """
    The master factory that assembles the entire invoice creation workflow.
    """

    @staticmethod
    def create(session_provider: SessionProvider,
               parent=None) -> InvoiceWizardController:

        manager = WorkflowStateManager()

        # 2. Create all the sub-controllers using their respective factories
        sub_controllers = {
            'customer': CustomerInfoFactory.create(session_provider, manager),
            'documents': DocumentSelectionFactory.create(session_provider, manager),
            'assignment': AssignmentWidget(manager),
            'details': InvoiceDetailsFactory.create(session_provider, manager),
            'preview': InvoicePreviewFactory.create(session_provider, manager)
        }

        # 3. Create the main wizard components
        wizard_view = InvoiceWizardWidget(parent=parent)
        wizard_logic = InvoiceWizardLogic()

        # 4. Create the main wizard controller, injecting all its dependencies
        wizard_controller = InvoiceWizardController(
            view=wizard_view,
            logic=wizard_logic,
            state_manager=manager,
            sub_controllers=sub_controllers
        )

        return wizard_controller


# --- Main Execution Block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    services_engine = create_engine(f"sqlite:///{SERVICES_DB_URL}")
    customers_engine = create_engine(f"sqlite:///{CUSTOMERS_DB_URL}")
    users_engine = create_engine(f"sqlite:///{USERS_DB_URL}")
    invoices_engine = create_engine(f"sqlite:///{INVOICES_DB_URL}")

    # 2. Create the tables in the database
    BaseServices.metadata.create_all(services_engine)
    BaseCustomers.metadata.create_all(customers_engine)
    BaseUsers.metadata.create_all(users_engine)
    BaseInvoices.metadata.create_all(invoices_engine)

    # 3. Create the application-wide SessionProvider instance
    # The key 'services' MUST match what SessionProvider expects.
    app_engines = {
        'services': services_engine,
        'customers': customers_engine,
        'users': users_engine,
        'invoices': invoices_engine
    }
    session_provider = SessionProvider(app_engines)

    populate_users_db(session_provider.users())
    populate_services_db(session_provider.services())
    populate_customers_db(session_provider.customers())
    populate_invoices_db(session_provider.invoices(), session_provider.customers(), session_provider.users())

    # --- Factory Usage ---
    state_manager = WorkflowStateManager()
    # Create the entire wizard with one call
    main_controller = InvoiceWizardFactory.create(session_provider, state_manager, parent=None)

    # --- Run the UI ---
    main_widget = main_controller.get_view()
    main_widget.show()
    main_widget.resize(1200, 800)  # Set a reasonable default size
    sys.exit(app.exec())
