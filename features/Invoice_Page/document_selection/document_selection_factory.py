# features/Invoice_Page/document_selection/document_selection_factory.py

import sys
from typing import Dict

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from faker import Faker

# --- Import Your Refactored MVC Components ---
from features.Invoice_Page.document_selection.document_selection_view import DocumentSelectionWidget
from features.Invoice_Page.document_selection.document_selection_controller import DocumentSelectionController
from features.Invoice_Page.document_selection.document_selection_logic import DocumentSelectionLogic
from features.Invoice_Page.document_selection.document_selection_repo import DocumentSelectionRepository
from features.Invoice_Page.customer_info.customer_info_models import Customer as CustomerDTO

from shared.orm_models.services_models import ServicesModel, OtherServicesModel, FixedPricesModel, BaseServices
from shared.assets import SERVICES_DB_URL


fake = Faker('fa_IR')


# --- 2. Mock State Manager (Reused) ---
class MockStateManager:
    def __init__(self):
        self._current_customer = None

    def set_customer(self, customer: CustomerDTO):
        print(f"[StateManager] Customer set to: {customer.name} ({customer.national_id})")
        self._current_customer = customer


# --- 3. The UNCHANGED Application-Wide Session Provider ---
class SessionProvider:
    def __init__(self, engines: Dict[str, Engine]):
        self._engines = engines
        self.invoices = self._create_session_maker('invoices')
        self.customers = self._create_session_maker('customers')
        self.services = self._create_session_maker('services')

    def _create_session_maker(self, name: str) -> sessionmaker:
        engine = self._engines.get(name)
        if engine:
            return sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return None


# --- 4. The Clean Document Selection Factory ---
class DocumentSelectionFactory:
    """
    Factory for creating and wiring the DocumentSelection package.
    It receives its dependencies and does not create them.
    """
    @staticmethod
    def create(session_provider: SessionProvider, state_manager=None) -> DocumentSelectionController:
        """
        Creates a fully configured DocumentSelection module.

        Args:
            session_provider: The pre-configured, application-wide SessionProvider.
            state_manager: An optional state manager. If None, a mock one is created.
        """
        # 1. Instantiate the layers, injecting dependencies
        repo = DocumentSelectionRepository()
        logic = DocumentSelectionLogic(repo, session_provider)
        view = DocumentSelectionWidget()
        manager = state_manager if state_manager is not None else MockStateManager()

        # 2. Instantiate the Controller, which connects everything
        controller = DocumentSelectionController(view, logic, manager)

        return controller


# --- 5. Mock Data Population (Helper Function) ---
def populate_database_for_testing(provider: SessionProvider):
    """
    Helper function to populate the services database.
    This is called by the application's entry point, not the factory.
    """
    if not provider.services:
        print("Cannot populate data: 'services' session is not available in the provider.")
        return

    with provider.services() as session:
        if session.query(ServicesModel).first():
            return  # Data already exists

        print("Populating Services.db with mock data...")
        # Add some regular services
        session.add_all([
            ServicesModel(name="شناسنامه", base_price=100000),
            ServicesModel(name="کارت ملی", base_price=80000),
            ServicesModel(name="گواهی تحصیلی", base_price=120000),
        ])
        # Add some "other" services
        session.add_all([
            OtherServicesModel(name="کپی برابر اصل", price=50000),
            OtherServicesModel(name="اسکن مدارک", price=10000),
        ])
        # Add the calculation fees
        session.add_all([
            FixedPricesModel(name="MHR_DADGSTRI", label_name="مهر دادگستری", price=70000, is_default=True),
            FixedPricesModel(name="MHR_AMORKHARJH", label_name="مهر امور خارجه", price=30000, is_default=True),
        ])
        session.commit()
        print("Database population complete.")


# --- 6. Main Execution Block (The Application Entry Point) ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Application Setup Phase ---
    # 1. Create the database Engine for this package
    services_engine = create_engine(f"sqlite:///{SERVICES_DB_URL}")

    # 2. Create the tables in the database
    BaseServices.metadata.create_all(services_engine)

    # 3. Create the application-wide SessionProvider instance
    # The key 'services' MUST match what SessionProvider expects.
    app_engines = {
        'services': services_engine
    }
    session_provider = SessionProvider(app_engines)

    # 4. (Optional) Populate the database with mock data
    populate_database_for_testing(session_provider)

    # 5. Create any other shared services
    mock_state_manager = MockStateManager()

    # --- Factory Usage Phase ---
    # The factory is now clean. We just pass it the services it needs.
    doc_selection_controller = DocumentSelectionFactory.create(
        session_provider=session_provider,
        state_manager=mock_state_manager
    )

    # --- Run the UI ---
    main_widget = doc_selection_controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
