# tests/test_logic.py

import pytest
from features.InvoicePage.invoice_preview_GAS.invoice_preview_logic_GAS import InvoiceService, create_mock_invoice
from features.InvoicePage.invoice_preview_GAS.invoice_preview_models_GAS import InvoiceItem


@pytest.fixture
def invoice_service():
    """Fixture to provide an instance of InvoiceService with mock data."""
    invoice = create_mock_invoice()
    return InvoiceService(invoice)


def test_get_total_pages(invoice_service):
    """
    Tests the page calculation logic.
    Mock data has 25 items. First page: 10, Others: 18.
    Page 1: 10 items.
    Remaining: 15 items. Needs 1 more page.
    Total should be 2 pages.
    """
    invoice_service.pagination_config = {'first_page_rows': 10, 'other_page_rows': 18}
    assert invoice_service.get_total_pages() == 2

    # Test with different pagination
    invoice_service.pagination_config = {'first_page_rows': 5, 'other_page_rows': 10}
    # Page 1: 5 items. Remaining: 20. Needs 2 more pages. Total: 3
    assert invoice_service.get_total_pages() == 3


def test_get_items_for_page(invoice_service):
    """Tests that the correct items are returned for each page."""
    invoice_service.pagination_config = {'first_page_rows': 10, 'other_page_rows': 18}

    # Test first page
    page_1_items = invoice_service.get_items_for_page(1)
    assert len(page_1_items) == 10
    assert page_1_items[0].row_num == 1
    assert page_1_items[-1].row_num == 10

    # Test second page
    page_2_items = invoice_service.get_items_for_page(2)
    assert len(page_2_items) == 15  # Remaining 15 items
    assert page_2_items[0].row_num == 11
    assert page_2_items[-1].row_num == 25

    # Test invalid page
    assert invoice_service.get_items_for_page(3) == []


#### `tests/test_repo.py`

# This
# test
# requires
# a
# temporary
# database and `pandas` and `openpyxl`.
#
# ```python
# tests/test_repo.py
# Note: This is an integration test and requires a database.

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from features.InvoicePage.invoice_preview_GAS.invoice_preview_repo_GAS import (Base, InvoiceRepository,
                                                                               IssuedInvoiceModel)

# Use an in-memory SQLite database for testing
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def test_db_session():
    """Fixture to set up and tear down a test database session."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def invoice_repo():
    """Fixture to provide an instance of InvoiceRepository."""
    # In a real scenario, you would mock the session or use a test DB
    return InvoiceRepository()


def test_export_to_excel_no_data(invoice_repo, tmp_path):
    """Tests that export returns False when no data is found for the user."""
    # We use the actual repo, which will create an empty DB
    file_path = tmp_path / "output.xlsx"
    assert not invoice_repo.export_to_excel("non_existent_user", str(file_path))


# This is a more complex test and would require populating the test DB first.
# For simplicity, we are showing the structure of how it would be written.
def test_export_to_excel_with_data(test_db_session, invoice_repo, tmp_path):
    """Tests exporting data to Excel. (Conceptual)"""
    # Arrange: Add some test data to the in-memory database
    from datetime import date
    test_invoice = IssuedInvoiceModel(
        invoice_number=1, name="Test Customer", national_id="111",
        phone="123", issue_date=date.today(), delivery_date=date.today(),
        translator="Test Translator", total_amount=100.0, final_amount=100.0,
        username="test_user"
    )
    test_db_session.add(test_invoice)
    test_db_session.commit()

    # We would need to inject this session into the repository for the test
    # This requires refactoring the repo to accept a session, a common practice
    # For now, this test is conceptual to show the intent.

    # Act and Assert would go here
    pass
