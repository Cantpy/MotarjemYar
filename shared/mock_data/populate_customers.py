# shared/mock_data/populate_customers.py

from sqlalchemy.orm import Session
from faker import Faker
from ..database_models.customer_models import CustomerModel, CompanionModel

# Use Persian locale for realistic names
fake = Faker('fa_IR')


def populate_customers_db(customers_session: Session):
    """Populates the Customers.db with mock customers and companions."""
    if customers_session.query(CustomerModel).first():
        return  # Data already exists

    print("Populating Customers.db with mock customers...")

    customers = []
    for _ in range(50):
        customer = CustomerModel(
            name=fake.name(),
            national_id=fake.unique.ssn().replace("-", ""),
            phone=fake.phone_number()
        )
        customers.append(customer)
    customers_session.add_all(customers)
    customers_session.commit()

    # Add some companions linked to the first 10 customers
    companions = [
        CompanionModel(
            name=fake.name(),
            national_id=fake.unique.ssn().replace("-", ""),
            customer_national_id=customers[i].national_id
        ) for i in range(10)
    ]
    customers_session.add_all(companions)
    customers_session.commit()
