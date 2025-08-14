# test_repo.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database_models.invoices_models import BaseInvoices, IssuedInvoiceModel
from shared.database_models.customer_models import BaseCustomers, CustomerModel, CompanionModel
from features.Reports.reports_repo import ReportsRepo
from datetime import date


@pytest.fixture(scope="module")
def session():
    """Setup a test database session."""
    engine = create_engine('sqlite:///:memory:')
    BaseInvoices.metadata.create_all(engine)
    BaseCustomers.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    # Add Test Data
    customer1 = CustomerModel(national_id="123", name="John Doe", phone="555-0101")
    customer2 = CustomerModel(national_id="456", name="Jane Smith", phone="555-0102")
    db_session.add_all([customer1, customer2])
    db_session.commit()

    invoice1 = IssuedInvoiceModel(invoice_number=1, name="John Doe", national_id="123", phone="555-0101",
                                  issue_date=date(2023, 1, 15), delivery_date=date(2023, 1, 20), translator="Alice",
                                  total_amount=100, total_translation_price=90, final_amount=100, payment_status=1)
    invoice2 = IssuedInvoiceModel(invoice_number=2, name="Jane Smith", national_id="456", phone="555-0102",
                                  issue_date=date(2023, 1, 20), delivery_date=date(2023, 1, 25), translator="Bob",
                                  total_amount=200, total_translation_price=180, final_amount=180, payment_status=0,
                                  discount_amount=20)
    invoice3 = IssuedInvoiceModel(invoice_number=3, name="John Doe", national_id="123", phone="555-0101",
                                  issue_date=date(2023, 2, 10), delivery_date=date(2023, 2, 15), translator="Alice",
                                  total_amount=150, total_translation_price=150, final_amount=150, payment_status=1)

    db_session.add_all([invoice1, invoice2, invoice3])
    db_session.commit()

    yield db_session
    db_session.close()


def test_get_financial_summary(session):
    repo = ReportsRepo(session)
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)

    summary = repo.get_financial_summary(start_date, end_date)

    assert summary['total_revenue'] == 300
    assert summary['net_income'] == 280
    assert summary['fully_paid_invoices'] == 1
    assert summary['unpaid_invoices'] == 1
