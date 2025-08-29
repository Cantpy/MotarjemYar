# shared/mock_data/mock_data_generator.py

from sqlalchemy.orm import Session
# Import all the new, specialized populator functions
from .populate_users import populate_users_db
from .populate_payroll import populate_payroll_db
from .populate_services import populate_services_db
from .populate_customers import populate_customers_db
from .populate_expenses import populate_expenses_db
from .populate_invoices import populate_invoices_db
from .populate_payroll_records import populate_historical_payroll_records


def create_mock_data(
        invoices_session_factory,
        customers_session_factory,
        services_session_factory,
        expenses_session_factory,
        users_session_factory,
        payroll_session_factory
):
    """
    Orchestrates the population of all databases by calling specialized functions
    in the correct, logical order.
    """
    print("--- Starting Mock Data Generation ---")

    # The order is important to satisfy foreign key constraints and dependencies.
    # For example, we need users and customers before we can create invoices.

    with users_session_factory() as session:
        populate_users_db(session)

    with payroll_session_factory() as session:
        populate_payroll_db(session)

    with services_session_factory() as session:
        populate_services_db(session)

    with customers_session_factory() as session:
        populate_customers_db(session)

    with expenses_session_factory() as session:
        populate_expenses_db(session)

    # Invoices depend on users, customers, and services, so it should run last.
    with invoices_session_factory() as session, customers_session_factory() as cust_session, users_session_factory() as user_session:
        populate_invoices_db(session, cust_session, user_session)

    populate_historical_payroll_records(
        invoices_session_factory,
        payroll_session_factory
    )

    print("--- Mock Data Generation Check Complete ---")