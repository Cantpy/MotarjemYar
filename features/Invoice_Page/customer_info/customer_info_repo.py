# features/Invoice_Pag/customer_info/customer_info_repo.py

from sqlalchemy.orm import Session

from features.Invoice_Page.customer_info.customer_info_models import Customer, Companion
from shared.orm_models.customer_models import CustomerModel, CompanionModel


class CustomerRepository:
    """
    Stateless repository for customer data operations.
    Requires a session to be passed into each method.
    """

    def save_customer(self, session: Session, customer: Customer) -> None:
        """Saves (adds or updates) a customer and their companions."""
        session.query(CompanionModel).filter_by(customer_national_id=customer.national_id).delete(synchronize_session=False)

        customer_model_data = customer.__dict__.copy()
        customer_model_data.pop('companions', None)
        customer_model = CustomerModel(**customer_model_data)

        companion_models = [
            CompanionModel(name=c.name, national_id=c.national_id, customer_national_id=customer.national_id)
            for c in customer.companions
        ]
        customer_model.companions = companion_models

        session.merge(customer_model)
        session.commit()

    def get_customer(self, session: Session, national_id: str) -> Customer | None:
        """Retrieves a single customer by their national ID."""
        customer_model = session.query(CustomerModel).filter_by(national_id=national_id).first()

        if not customer_model:
            return None

        companions_list = [
            Companion(id=c.id, name=c.name, national_id=c.national_id)
            for c in customer_model.companions
        ]
        return Customer(
            national_id=customer_model.national_id,
            name=customer_model.name,
            phone=customer_model.phone,
            telegram_id=customer_model.telegram_id,
            email=customer_model.email,
            address=customer_model.address,
            passport_image=customer_model.passport_image,
            companions=companions_list
        )

    def get_all_customers(self, session: Session) -> list[Customer]:
        """Retrieves all customers from the database."""
        customers_models = session.query(CustomerModel).all()
        return [
            Customer(
                national_id=cm.national_id,
                name=cm.name,
                phone=cm.phone,
                companions=[Companion(id=c.id, name=c.name, national_id=c.national_id) for c in cm.companions]
            ) for cm in customers_models
        ]

    def get_all_customers_for_completer(self, session: Session) -> list[dict]:
        """Fetches just the name and NID of all main customers."""
        results = session.query(CustomerModel.name, CustomerModel.national_id).all()
        return [{"name": name, "national_id": nid} for name, nid in results]

    def get_all_companions_for_completer(self, session: Session) -> list[dict]:
        """Fetches name and NID of all companions, plus their main customer's NID."""
        results = session.query(
            CompanionModel.name,
            CompanionModel.national_id,
            CompanionModel.customer_national_id
        ).all()
        return [{"name": name, "national_id": nid, "main_customer_nid": main_nid} for name, nid, main_nid in results]
