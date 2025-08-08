from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, and_, or_, func
from features.InvoicePage.customer_management.customer_managemnet_models import (CustomerData, CompanionData,
                                                                                 CustomerDisplayData)
from shared.models.sqlalchemy_models import CustomerModel, IssuedInvoiceModel, CompanionModel


class CustomerRepository:
    """Repository for customer data operations."""

    def __init__(self, invoice_session_factory: sessionmaker, customer_session_factory: sessionmaker):
        self.customer_session_factory = customer_session_factory
        self.invoice_session_factory = invoice_session_factory

    def get_all_customers_with_details(self) -> List[CustomerDisplayData]:
        """Get all customers with their companions and invoice counts."""
        try:
            with self.customer_session_factory() as session:
                with self.invoice_session_factory() as invoice_session:
                    # Query customers with their companions and invoice count
                    customers_query = session.query(CustomerModel).all()

                    customer_display_list = []

                    for customer in customers_query:
                        # Get companions for this customer
                        companions = session.query(CompanionModel).filter(
                            CompanionModel.customer_national_id == customer.national_id
                        ).all()

                        # Convert companions to data objects
                        companion_data_list = [
                            CompanionData(
                                id=comp.id,
                                name=comp.name,
                                national_id=comp.national_id,
                                customer_national_id=comp.customer_national_id,
                                ui_number=0
                            ) for comp in companions
                        ]

                        # Get invoice count
                        invoice_count = invoice_session.query(func.count(IssuedInvoiceModel.id)).filter(
                            IssuedInvoiceModel.national_id == customer.national_id
                        ).scalar() or 0

                        # Create display data
                        customer_display = CustomerDisplayData(
                            national_id=customer.national_id,
                            name=customer.name,
                            phone=customer.phone,
                            email=customer.email or "",
                            address=customer.address or "",
                            telegram_id=customer.telegram_id or "",
                            invoice_count=invoice_count,
                            companions=companion_data_list
                        )

                        customer_display_list.append(customer_display)
                        print('customers to display: ', customer_display_list)

                    return customer_display_list
        except Exception as e:
            print(" ======= repository error in getting all customers with detail: ", e)

    def search_customers_and_companions(self, search_term: str) -> List[CustomerDisplayData]:
        """Search customers and companions by name, national_id, or phone."""
        if not search_term.strip():
            return self.get_all_customers_with_details()

        with self.customer_session_factory() as session:
            with self.invoice_session_factory() as invoice_session:
                search_term = f"%{search_term.strip()}%"

                # Find customers matching the search term
                customer_matches = session.query(CustomerModel).filter(
                    or_(
                        CustomerModel.name.ilike(search_term),
                        CustomerModel.national_id.ilike(search_term),
                        CustomerModel.phone.ilike(search_term),
                        CustomerModel.email.ilike(search_term)
                    )
                ).all()

                # Find companions matching the search term and get their customers
                companion_matches = session.query(CompanionModel).filter(
                    or_(
                        CompanionModel.name.ilike(search_term),
                        CompanionModel.national_id.ilike(search_term)
                    )
                ).all()

                # Get customer national_ids from companion matches
                customer_ids_from_companions = [comp.customer_national_id for comp in companion_matches]

                # Get customers who have matching companions
                customers_with_matching_companions = []
                if customer_ids_from_companions:
                    customers_with_matching_companions = session.query(CustomerModel).filter(
                        CustomerModel.national_id.in_(customer_ids_from_companions)
                    ).all()

                # Combine and deduplicate customers
                all_customers = {customer.national_id: customer for customer in customer_matches}
                for customer in customers_with_matching_companions:
                    all_customers[customer.national_id] = customer

                # Build display data
                customer_display_list = []
                for customer in all_customers.values():
                    # Get all companions for this customer
                    companions = session.query(CompanionModel).filter(
                        CompanionModel.customer_national_id == customer.national_id
                    ).all()

                    companion_data_list = [
                        CompanionData(
                            id=comp.id,
                            name=comp.name,
                            national_id=comp.national_id,
                            customer_national_id=comp.customer_national_id,
                            ui_number=0
                        ) for comp in companions
                    ]

                    # Get invoice count
                    invoice_count = session.query(func.count(IssuedInvoiceModel.id)).filter(
                        IssuedInvoiceModel.national_id == customer.national_id
                    ).scalar() or 0

                    customer_display = CustomerDisplayData(
                        national_id=customer.national_id,
                        name=customer.name,
                        phone=customer.phone,
                        email=customer.email or "",
                        address=customer.address or "",
                        telegram_id=customer.telegram_id or "",
                        invoice_count=invoice_count,
                        companions=companion_data_list
                    )

                    customer_display_list.append(customer_display)

                return customer_display_list

    def get_customer_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        """Get a single customer by national ID."""
        with self.customer_session_factory() as session:
            customer = session.query(CustomerModel).filter(
                CustomerModel.national_id == national_id
            ).first()

            if customer:
                return CustomerData(
                    national_id=customer.national_id,
                    name=customer.name,
                    phone=customer.phone,
                    email=customer.email or "",
                    address=customer.address or "",
                    telegram_id=customer.telegram_id or "",
                    passport_image=customer.passport_image or ""
                )
            return None

    def create_customer(self, customer_data: CustomerData) -> bool:
        """Create a new customer."""
        try:
            with self.customer_session_factory() as session:
                new_customer = CustomerModel()
                new_customer.national_id = customer_data.national_id
                new_customer.name = customer_data.name
                new_customer.phone = customer_data.phone
                new_customer.email = customer_data.email
                new_customer.address = customer_data.address
                new_customer.telegram_id = customer_data.telegram_id
                new_customer.passport_image = customer_data.passport_image

                session.add(new_customer)
                session.commit()
                return True
        except Exception:
            return False

    def update_customer(self, customer_data: CustomerData) -> bool:
        """Update an existing customer."""
        try:
            with self.customer_session_factory() as session:
                customer = session.query(CustomerModel).filter(
                    CustomerModel.national_id == customer_data.national_id
                ).first()

                if customer:
                    customer.name = customer_data.name
                    customer.phone = customer_data.phone
                    customer.email = customer_data.email
                    customer.address = customer_data.address
                    customer.telegram_id = customer_data.telegram_id
                    customer.passport_image = customer_data.passport_image

                    session.commit()
                    return True
                return False
        except Exception:
            return False

    def delete_customer(self, national_id: str) -> bool:
        """Delete a customer and all associated companions."""
        try:
            with self.customer_session_factory() as session:
                # Delete companions first (though CASCADE should handle this)
                session.query(CompanionModel).filter(
                    CompanionModel.customer_national_id == national_id
                ).delete()

                # Delete customer
                customer = session.query(CustomerModel).filter(
                    CustomerModel.national_id == national_id
                ).first()

                if customer:
                    session.delete(customer)
                    session.commit()
                    return True
                return False
        except Exception:
            return False

    def check_customer_has_active_invoices(self, national_id: str) -> Tuple[bool, int]:
        """Check if customer has active invoices (delivery_status != 4)."""
        with self.invoice_session_factory() as session:
            active_invoice_count = session.query(func.count(IssuedInvoiceModel.id)).filter(
                and_(
                    IssuedInvoiceModel.national_id == national_id,
                    IssuedInvoiceModel.delivery_status != 4
                )
            ).scalar() or 0

            return active_invoice_count > 0, active_invoice_count

    def get_companions_by_customer_id(self, customer_national_id: str) -> List[CompanionData]:
        """Get all companions for a customer."""
        with self.customer_session_factory() as session:
            companions = session.query(CompanionModel).filter(
                CompanionModel.customer_national_id == customer_national_id
            ).all()

            return [
                CompanionData(
                    id=comp.id,
                    name=comp.name,
                    national_id=comp.national_id,
                    customer_national_id=comp.customer_national_id,
                    ui_number=0
                ) for comp in companions
            ]

    def create_companion(self, companion_data: CompanionData) -> bool:
        """Create a new companion."""
        try:
            with self.customer_session_factory() as session:
                new_companion = CompanionModel()
                new_companion.name = companion_data.name
                new_companion.national_id = companion_data.national_id
                new_companion.customer_national_id = companion_data.customer_national_id

                session.add(new_companion)
                session.commit()
                return True
        except Exception:
            return False

    def update_companion(self, companion_data: CompanionData) -> bool:
        """Update an existing companion."""
        try:
            with self.customer_session_factory() as session:
                companion = session.query(CompanionModel).filter(
                    CompanionModel.id == companion_data.id
                ).first()

                if companion:
                    companion.name = companion_data.name
                    companion.national_id = companion_data.national_id
                    companion.customer_national_id = companion_data.customer_national_id

                    session.commit()
                    return True
                return False
        except Exception:
            return False

    def delete_companion(self, companion_id: int) -> bool:
        """Delete a companion."""
        try:
            with self.customer_session_factory() as session:
                companion = session.query(CompanionModel).filter(
                    CompanionModel.id == companion_id
                ).first()

                if companion:
                    session.delete(companion)
                    session.commit()
                    return True
                return False
        except Exception:
            return False
