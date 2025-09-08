# test_repository.py
import pytest
from features.Invoice_Page.customer_info.customer_info_repo import CustomerRepository
from features.Invoice_Page.customer_info.customer_info_models import Customer, Companion


@pytest.fixture
def repo():
    """Creates an in-memory database repository for each test."""
    return CustomerRepository(db_file=":memory:")


def test_add_and_get_customer(repo):
    """Tests adding a customer with companions and retrieving them."""
    customer = Customer(
        name="John Doe",
        national_id=12345,
        phone="555-1234",
        companions=[Companion(name="Jane Doe", national_id=67890)]
    )
    repo.add_customer(customer)

    retrieved = repo.get_customer(12345)
    assert retrieved is not None
    assert retrieved.name == "John Doe"
    assert len(retrieved.companions) == 1
    assert retrieved.companions[0].name == "Jane Doe"
