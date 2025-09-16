import sys
import os
from typing import Dict

from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Engine
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from faker import Faker

# --- Import Your Refactored MVC Components ---
from features.Invoice_Page.customer_info.customer_info_view import CustomerInfoWidget
from features.Invoice_Page.customer_info.customer_info_controller import CustomerInfoController
from features.Invoice_Page.customer_info.customer_info_logic import CustomerLogic
from features.Invoice_Page.customer_info.customer_info_repo import CustomerRepository
from features.Invoice_Page.customer_info.customer_info_models import Customer as CustomerDTO

# --- 1. ORM Models and Constants (No changes here) ---
from shared.assets import CUSTOMERS_DB_URL
from shared.orm_models.customer_models import BaseCustomers, CustomerModel, CompanionModel

fake = Faker('fa_IR')


# --- 2. Mock State Manager (No changes here) ---
class MockStateManager:
    def __init__(self):
        self._current_customer = None

    def set_customer(self, customer: CustomerDTO):
        print(f"[StateManager] Customer set to: {customer.name} ({customer.national_id})")
        self._current_customer = customer


# --- 3. The UNCHANGED Session Provider (As per your requirement) ---
class SessionProvider:
    """
    This is your application-wide SessionProvider. It is received, not created, by the factories.
    """
    def __init__(self, engines: Dict[str, Engine]):
        self._engines = engines
        # It creates all session makers for the entire application
        self.invoices = self._create_session_maker('invoices')
        self.customers = self._create_session_maker('customers')
        # ... and so on for services, payroll, etc.

    def _create_session_maker(self, name: str) -> sessionmaker:
        engine = self._engines.get(name)
        # We will be careful to only provide engines that are needed
        if engine:
            return sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return None     # Return None if an engine isn't provided


# --- 4. The REFACTORED Customer Info Factory ---
class CustomerInfoFactory:
    """
    Factory for creating and wiring the CustomerInfo package.
    It follows the clean pattern of receiving its dependencies.
    """
    @staticmethod
    def create(session_provider: SessionProvider, state_manager=None) -> CustomerInfoController:
        """
        Creates a fully configured CustomerInfo module by assembling its components.

        Args:
            session_provider: The pre-configured, application-wide SessionProvider.
            state_manager: An optional state manager. If None, a mock one is created.

        Returns:
            CustomerInfoController: The fully wired controller instance.
        """
        # The factory's responsibility is now purely to instantiate and connect.
        # It no longer knows about database modes, files, or data population.

        # 1. Instantiate the layers, injecting dependencies
        repo = CustomerRepository()
        logic = CustomerLogic(repo, session_provider)
        view = CustomerInfoWidget()
        manager = state_manager if state_manager is not None else MockStateManager()

        # 2. Instantiate the Controller, which connects everything
        controller = CustomerInfoController(view, logic, manager)

        return controller


# --- 5. Mock Data Population (Helper Function) ---
def populate_database_for_testing(provider: SessionProvider):
    """
    Helper function to populate the database using the provided session provider.
    This _logic is now outside the factory.
    """
    if not provider.customers:
        print("Cannot populate data: 'customers' session is not available in the provider.")
        return

    # Use the session provider to get a session
    with provider.customers() as session:
        if session.query(CustomerModel).first():
            return  # Data already exists

        print("Populating Customers.db with mock customers...")
        customers = [CustomerModel(name=fake.name(), national_id=fake.unique.ssn().replace("-", ""), phone=fake.phone_number()) for _ in range(50)]
        session.add_all(customers)
        session.commit()
        companions = [CompanionModel(name=fake.name(), national_id=fake.unique.ssn().replace("-", ""), customer_national_id=customers[i].national_id) for i in range(10)]
        session.add_all(companions)
        session.commit()
        print("Database population complete.")


# --- 6. Main Execution Block (The Application Entry Point) ---
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # --- Application Setup Phase ---
    # This is now the ONLY place that knows how to create the database engine and SessionProvider.

    # 1. Create the database Engine(s)
    # We only need the customers engine for this standalone example.
    customers_engine = create_engine(f"sqlite:///{CUSTOMERS_DB_URL}")

    # 2. Create the tables in the database
    BaseCustomers.metadata.create_all(customers_engine)

    # 3. Create the application-wide SessionProvider instance
    app_engines = {
        'customers': customers_engine
    }
    session_provider = SessionProvider(app_engines)

    # 4. (Optional) Populate the database with mock data for this test run
    populate_database_for_testing(session_provider)

    # 5. Create any other shared services, like the state manager
    mock_state_manager = MockStateManager()

    # --- Factory Usage Phase ---
    # Now, we use the clean factory, passing in the dependencies we just created.
    customer_info_controller = CustomerInfoFactory.create(
        session_provider=session_provider,
        state_manager=mock_state_manager
    )

    # --- Run the UI ---
    main_widget = customer_info_controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
