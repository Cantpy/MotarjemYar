# repository.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional

from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer, Companion
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_assets import CUSTOMERS_DB_URL

from shared.database_models.customer_models import CustomerModel, CompanionModel, BaseCustomers


# --- Repository Class for Data Operations ---
class CustomerRepository:
    def __init__(self, db_file=CUSTOMERS_DB_URL):
        self.engine = create_engine(f"sqlite:///{db_file}")
        BaseCustomers.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_customer(self, customer: Customer) -> None:
        """Adds or updates a customer and their companions in the database."""
        with self.Session() as session:
            # First, delete existing companions to handle updates cleanly
            session.query(CompanionModel).filter_by(customer_national_id=customer.national_id).delete()

            customer_model_data = customer.__dict__.copy()
            customer_model_data.pop('companions', None)  # Remove companions from dict for main model

            customer_model = CustomerModel(**customer_model_data)

            # Create new companion database_models from the DTO
            companion_models = [
                CompanionModel(name=c.name, national_id=c.national_id, customer_national_id=customer.national_id) for c
                in customer.companions]
            customer_model.companions = companion_models

            session.merge(customer_model)
            session.commit()

    def get_customer(self, national_id: str) -> Optional[Customer]:
        """
        Retrieves a single customer by their national ID.
        Refactored to have a single, clear return point.
        """
        customer_dto = None  # Initialize return value to None
        with self.Session() as session:
            customer_model = session.query(CustomerModel).filter_by(national_id=national_id).first()
            if customer_model:
                companions_list = [
                    Companion(id=c.id, name=c.name, national_id=c.national_id) 
                    for c in customer_model.companions
                ]
                customer_dto = Customer(
                    national_id=customer_model.national_id,
                    name=customer_model.name,
                    phone=customer_model.phone,
                    telegram_id=customer_model.telegram_id,
                    email=customer_model.email,
                    address=customer_model.address,
                    passport_image=customer_model.passport_image,
                    companions=companions_list
                )
        return customer_dto

    def get_all_customers(self) -> List[Customer]:
        """Retrieves all customers from the database."""
        with self.Session() as session:
            customers_models = session.query(CustomerModel).all()
            customer_list = [
                Customer(
                    national_id=cm.national_id,
                    name=cm.name,
                    phone=cm.phone,
                    telegram_id=cm.telegram_id,
                    email=cm.email,
                    address=cm.address,
                    passport_image=cm.passport_image,
                    companions=[Companion(id=c.id, name=c.name, national_id=c.national_id) for c in cm.companions]
                ) for cm in customers_models
            ]
        return customer_list

    def get_all_customers_for_completer(self) -> list[dict]:
        """Fetches just the name and NID of all main customers."""
        with self.Session() as session:
            results = session.query(CustomerModel.name, CustomerModel.national_id).all()
            return [{"name": name, "national_id": nid} for name, nid in results]

    def get_all_companions_for_completer(self) -> list[dict]:
        """
        NEW: Fetches the name and NID of all companions, along with their
        main customer's NID for lookup purposes.
        """
        with self.Session() as session:
            results = session.query(CompanionModel.name, CompanionModel.national_id,
                                    CompanionModel.customer_national_id).all()
            return [{"name": name, "national_id": nid, "main_customer_nid": main_nid} for name, nid, main_nid in
                    results]
