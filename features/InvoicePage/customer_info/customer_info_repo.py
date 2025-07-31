# -*- coding: utf-8 -*-
"""
Repository Layer - Data Access with SQLAlchemy ORM
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from features.InvoicePage.customer_info.customer_info_models import CustomerData, CustomerSearchCriteria


from shared.entities.entities import Customer


class CustomerRepository:
    """Repository for customer data access."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def get_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        """Get customer by national ID."""
        try:
            customer = self.db_session.query(Customer).filter(
                Customer.national_id == national_id
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

        except SQLAlchemyError as e:
            print(f"Database error in get_by_national_id: {e}")
            return None

    def get_by_phone(self, phone: str) -> Optional[CustomerData]:
        """Get customer by phone number."""
        try:
            customer = self.db_session.query(Customer).filter(
                Customer.phone == phone
            ).first()

            if customer:
                return self._convert_to_customer_data(customer)

        except SQLAlchemyError as e:
            print(f"Database error in get_by_phone: {e}")
            return None

    def search_customers(self, criteria: CustomerSearchCriteria) -> List[CustomerData]:
        """Search customers based on criteria."""
        try:
            query = self.db_session.query(Customer)
            filters = []

            if criteria.national_id:
                filters.append(Customer.national_id.like(f"%{criteria.national_id}%"))
            if criteria.name:
                filters.append(Customer.name.like(f"%{criteria.name}%"))
            if criteria.phone:
                filters.append(Customer.phone.like(f"%{criteria.phone}%"))
            if criteria.email:
                filters.append(Customer.email.like(f"%{criteria.email}%"))

            if filters:
                query = query.filter(or_(*filters))

            customers = query.limit(50).all()  # Limit results
            return [self._convert_to_customer_data(customer) for customer in customers]

        except SQLAlchemyError as e:
            print(f"Database error in search_customers: {e}")
            return []

    def create_customer(self, customer_data: CustomerData) -> bool:
        """Create a new customer."""
        try:
            customer = Customer(
                national_id=customer_data.national_id,
                name=customer_data.name,
                phone=customer_data.phone,
                email=customer_data.email if customer_data.email else None,
                address=customer_data.address if customer_data.address else None,
                telegram_id=customer_data.telegram_id if customer_data.telegram_id else None,
                passport_image=customer_data.passport_image if customer_data.passport_image else None
            )

            self.db_session.add(customer)
            self.db_session.commit()
            return True

        except SQLAlchemyError as e:
            print(f"Database error in create_customer: {e}")
            self.db_session.rollback()
            return False

    def update_customer(self, customer_data: CustomerData) -> bool:
        """Update existing customer."""
        try:
            customer = self.db_session.query(Customer).filter(
                Customer.national_id == customer_data.national_id
            ).first()

            if customer:
                customer.name = customer_data.name
                customer.phone = customer_data.phone
                customer.email = customer_data.email if customer_data.email else None
                customer.address = customer_data.address if customer_data.address else None
                customer.telegram_id = customer_data.telegram_id if customer_data.telegram_id else None
                customer.passport_image = customer_data.passport_image if customer_data.passport_image else None

                self.db_session.commit()
                return True

        except SQLAlchemyError as e:
            print(f"Database error in update_customer: {e}")
            self.db_session.rollback()
            return False

    def delete_customer(self, national_id: str) -> bool:
        """Delete customer by national ID."""
        try:
            customer = self.db_session.query(Customer).filter(
                Customer.national_id == national_id
            ).first()

            if customer:
                self.db_session.delete(customer)
                self.db_session.commit()
                return True

        except SQLAlchemyError as e:
            print(f"Database error in delete_customer: {e}")
            self.db_session.rollback()
            return False

    def customer_exists(self, national_id: str) -> bool:
        """Check if customer exists by national ID."""
        try:
            return self.db_session.query(Customer).filter(
                Customer.national_id == national_id
            ).first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in customer_exists: {e}")
            return False

    def phone_exists(self, phone: str, exclude_national_id: str = None) -> bool:
        """Check if phone number exists (optionally excluding a specific customer)."""
        try:
            query = self.db_session.query(Customer).filter(Customer.phone == phone)
            if exclude_national_id:
                query = query.filter(Customer.national_id != exclude_national_id)
            return query.first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in phone_exists: {e}")
            return False

    def get_all_customers(self, limit: int = 100) -> List[CustomerData]:
        """Get all customers with optional limit."""
        try:
            customers = self.db_session.query(Customer).limit(limit).all()
            return [self._convert_to_customer_data(customer) for customer in customers]

        except SQLAlchemyError as e:
            print(f"Database error in get_all_customers: {e}")
            return []

    def get_customer_count(self) -> int:
        """Get total number of customers."""
        try:
            return self.db_session.query(Customer).count()

        except SQLAlchemyError as e:
            print(f"Database error in get_customer_count: {e}")
            return 0

    def _convert_to_customer_data(self, customer) -> CustomerData:
        """Convert SQLAlchemy Customer model to CustomerData dataclass."""
        return CustomerData(
            national_id=customer.national_id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email or "",
            address=customer.address or "",
            telegram_id=customer.telegram_id or "",
            passport_image=customer.passport_image or ""
        )


class CustomerRepositoryFactory:
    """Factory for creating customer repositories."""

    @staticmethod
    def create(db_session: Session) -> CustomerRepository:
        """Create a customer repository instance."""
        return CustomerRepository(db_session)


# Usage example and interface for dependency injection
class ICustomerRepository:
    """Interface for customer repository."""

    def get_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        raise NotImplementedError

    def get_by_phone(self, phone: str) -> Optional[CustomerData]:
        raise NotImplementedError

    def search_customers(self, criteria: CustomerSearchCriteria) -> List[CustomerData]:
        raise NotImplementedError

    def create_customer(self, customer_data: CustomerData) -> bool:
        raise NotImplementedError

    def update_customer(self, customer_data: CustomerData) -> bool:
        raise NotImplementedError

    def delete_customer(self, national_id: str) -> bool:
        raise NotImplementedError

    def customer_exists(self, national_id: str) -> bool:
        raise NotImplementedError

    def phone_exists(self, phone: str, exclude_national_id: str = None) -> bool:
        raise NotImplementedError


class InMemoryCustomerRepository(ICustomerRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        self._customers: Dict[str, CustomerData] = {}

    def get_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        return self._customers.get(national_id)

    def get_by_phone(self, phone: str) -> Optional[CustomerData]:
        for customer in self._customers.values():
            if customer.phone == phone:
                return customer
        return None

    def search_customers(self, criteria: CustomerSearchCriteria) -> List[CustomerData]:
        results = []
        for customer in self._customers.values():
            if self._customer_matches_criteria(customer, criteria):
                results.append(customer)
        return results[:50]  # Limit results

    def create_customer(self, customer_data: CustomerData) -> bool:
        if customer_data.national_id in self._customers:
            return False
        self._customers[customer_data.national_id] = customer_data
        return True

    def update_customer(self, customer_data: CustomerData) -> bool:
        if customer_data.national_id not in self._customers:
            return False
        self._customers[customer_data.national_id] = customer_data
        return True

    def delete_customer(self, national_id: str) -> bool:
        if national_id in self._customers:
            del self._customers[national_id]
            return True
        return False

    def customer_exists(self, national_id: str) -> bool:
        return national_id in self._customers

    def phone_exists(self, phone: str, exclude_national_id: str = None) -> bool:
        for customer in self._customers.values():
            if customer.phone == phone and customer.national_id != exclude_national_id:
                return True
        return False

    def _customer_matches_criteria(self, customer: CustomerData, criteria: CustomerSearchCriteria) -> bool:
        """Check if customer matches search criteria."""
        if criteria.national_id and criteria.national_id not in customer.national_id:
            return False
        if criteria.name and criteria.name.lower() not in customer.name.lower():
            return False
        if criteria.phone and criteria.phone not in customer.phone:
            return False
        if criteria.email and criteria.email.lower() not in customer.email.lower():
            return False
        return True
