# -*- coding: utf-8 -*-
"""
Repository Layer - Data Access with SQLAlchemy ORM
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

from features.InvoicePage.customer_info.customer_info_models import (
    CustomerData, CompanionData, CustomerInfoData, CustomerSearchCriteria
)
from shared.models.sqlalchemy_models import CustomerModel, CompanionModel


class ICustomerRepository:
    """Interface for customer repository."""

    def get_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        raise NotImplementedError

    def get_customer_with_companions(self, national_id: str) -> Optional[CustomerInfoData]:
        raise NotImplementedError

    def get_by_phone(self, phone: str) -> Optional[CustomerData]:
        raise NotImplementedError

    def search_customers(self, criteria: CustomerSearchCriteria) -> List[CustomerData]:
        raise NotImplementedError

    def create_customer(self, customer_data: CustomerData) -> bool:
        raise NotImplementedError

    def save_customer_with_companions(self, customer_info: CustomerInfoData) -> bool:
        raise NotImplementedError

    def update_customer(self, customer_data: CustomerData) -> bool:
        raise NotImplementedError

    def delete_customer(self, national_id: str) -> bool:
        raise NotImplementedError

    def customer_exists(self, national_id: str) -> bool:
        raise NotImplementedError

    def phone_exists(self, phone: str, exclude_national_id: str = None) -> bool:
        """Check if phone number exists (optionally excluding a specific customer)."""
        try:
            query = self.db_session.query(CustomerModel).filter(CustomerModel.phone == phone)
            if exclude_national_id:
                query = query.filter(CustomerModel.national_id != exclude_national_id)
            return query.first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in phone_exists: {e}")
            return False

    def companion_national_id_exists(self, national_id: str, exclude_companion_id: int = None) -> bool:
        """Check if companion national ID exists (optionally excluding a specific companion)."""
        try:
            query = self.db_session.query(CompanionModel).filter(CompanionModel.national_id == national_id)
            if exclude_companion_id:
                query = query.filter(CompanionModel.id != exclude_companion_id)
            return query.first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in companion_national_id_exists: {e}")
            return False

    def customer_national_id_exists_as_companion(self, national_id: str) -> bool:
        """Check if a national ID is already used as a companion."""
        try:
            return self.db_session.query(CompanionModel).filter(
                CompanionModel.national_id == national_id
            ).first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in customer_national_id_exists_as_companion: {e}")
            return False

    def _convert_to_customer_data(self, customer) -> CustomerData:
        """Convert SQLAlchemy CustomerModel model to CustomerData dataclass."""
        return CustomerData(
            national_id=customer.national_id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email or "",
            address=customer.address or "",
            telegram_id=customer.telegram_id or "",
            passport_image=customer.passport_image or ""
        )

    def _convert_to_companion_data(self, companion) -> CompanionData:
        """Convert SQLAlchemy CompanionModel to CompanionData dataclass."""
        return CompanionData(
            id=companion.id,
            name=companion.name,
            national_id=companion.national_id,
            customer_national_id=companion.customer_national_id,
            ui_number=0  # Will be set by logic layer when loading
        )


class CustomerRepository(ICustomerRepository):
    """Repository for customer data access."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db_session = db_session

    def get_all_customers(self, limit: int = 100) -> List[CustomerData]:
        """Get all customers with optional limit."""
        try:
            customers = self.db_session.query(CustomerModel).limit(limit).all()
            return [self._convert_to_customer_data(customer) for customer in customers]
        except SQLAlchemyError as e:
            print(f"Database error in get_all_customers: {e}")
            return []

    def get_customer_count(self) -> int:
        """Get total number of customers."""
        try:
            return self.db_session.query(CustomerModel).count()
        except SQLAlchemyError as e:
            print(f"Database error in get_customer_count: {e}")
            return 0

    def get_companions_by_customer(self, customer_national_id: str) -> List[CompanionData]:
        """Get all companions for a specific customer."""
        try:
            companions = self.db_session.query(CompanionModel).filter(
                CompanionModel.customer_national_id == customer_national_id
            ).all()
            return [self._convert_to_companion_data(comp) for comp in companions]
        except SQLAlchemyError as e:
            print(f"Database error in get_companions_by_customer: {e}")
            return []

    def get_all_companions(self, limit: int = 1000) -> List[CompanionData]:
        """Get all companions across all customers."""
        try:
            companions = self.db_session.query(CompanionModel).limit(limit).all()
            return [self._convert_to_companion_data(comp) for comp in companions]
        except SQLAlchemyError as e:
            print(f"Database error in get_all_companions: {e}")
            return []

    def search_customers_by_partial_match(self, field: str, value: str, limit: int = 10) -> List[CustomerData]:
        """Search customers by partial match on specific field."""
        try:
            query = self.db_session.query(CustomerModel)

            if field == 'national_id':
                query = query.filter(CustomerModel.national_id.like(f"{value}%"))
            elif field == 'name':
                query = query.filter(CustomerModel.name.like(f"%{value}%"))
            elif field == 'phone':
                query = query.filter(CustomerModel.phone.like(f"{value}%"))
            elif field == 'email':
                query = query.filter(CustomerModel.email.like(f"%{value}%"))
            else:
                return []

            customers = query.limit(limit).all()
            return [self._convert_to_customer_data(customer) for customer in customers]

        except SQLAlchemyError as e:
            print(f"Database error in search_customers_by_partial_match: {e}")
            return []

    def search_companions_by_partial_match(self, field: str, value: str, limit: int = 10) -> List[CompanionData]:
        """Search companions by partial match on specific field."""
        try:
            query = self.db_session.query(CompanionModel)

            if field == 'national_id':
                query = query.filter(CompanionModel.national_id.like(f"{value}%"))
            elif field == 'name':
                query = query.filter(CompanionModel.name.like(f"%{value}%"))
            else:
                return []

            companions = query.limit(limit).all()
            return [self._convert_to_companion_data(comp) for comp in companions]

        except SQLAlchemyError as e:
            print(f"Database error in search_companions_by_partial_match: {e}")
            return []

    def get_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        """Get customer by national ID."""
        try:
            customer = self.db_session.query(CustomerModel).filter(
                CustomerModel.national_id == national_id
            ).first()

            if customer:
                return self._convert_to_customer_data(customer)

        except SQLAlchemyError as e:
            print(f"Database error in get_by_national_id: {e}")
            return None

    def get_customer_with_companions(self, national_id: str) -> Optional[CustomerInfoData]:
        """Get customer with all companions."""
        try:
            customer = self.db_session.query(CustomerModel).filter(
                CustomerModel.national_id == national_id
            ).first()

            if not customer:
                return None

            # Get companions
            companions_query = self.db_session.query(CompanionModel).filter(
                CompanionModel.customer_national_id == national_id
            ).all()

            customer_data = self._convert_to_customer_data(customer)
            companions_data = [self._convert_to_companion_data(comp) for comp in companions_query]

            return CustomerInfoData(
                customer=customer_data,
                has_companions=len(companions_data) > 0,
                companions=companions_data
            )

        except SQLAlchemyError as e:
            print(f"Database error in get_customer_with_companions: {e}")
            return None

    def get_by_phone(self, phone: str) -> Optional[CustomerData]:
        """Get customer by phone number."""
        try:
            customer = self.db_session.query(CustomerModel).filter(
                CustomerModel.phone == phone
            ).first()

            if customer:
                return self._convert_to_customer_data(customer)

        except SQLAlchemyError as e:
            print(f"Database error in get_by_phone: {e}")
            return None

    def search_customers(self, criteria: CustomerSearchCriteria) -> List[CustomerData]:
        """Search customers based on criteria."""
        try:
            query = self.db_session.query(CustomerModel)
            filters = []

            if criteria.national_id:
                filters.append(CustomerModel.national_id.like(f"%{criteria.national_id}%"))
            if criteria.name:
                filters.append(CustomerModel.name.like(f"%{criteria.name}%"))
            if criteria.phone:
                filters.append(CustomerModel.phone.like(f"%{criteria.phone}%"))
            if criteria.email:
                filters.append(CustomerModel.email.like(f"%{criteria.email}%"))

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
            customer = CustomerModel(
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

    def save_customer_with_companions(self, customer_info: CustomerInfoData) -> bool:
        """Save customer along with companions."""
        try:
            # Prepare companions with customer reference
            customer_info.prepare_for_save()

            # Create or update customer
            existing_customer = self.db_session.query(CustomerModel).filter(
                CustomerModel.national_id == customer_info.customer.national_id
            ).first()

            if existing_customer:
                # Update existing customer
                existing_customer.name = customer_info.customer.name
                existing_customer.phone = customer_info.customer.phone
                existing_customer.email = customer_info.customer.email if customer_info.customer.email else None
                existing_customer.address = customer_info.customer.address if customer_info.customer.address else None
                existing_customer.telegram_id = customer_info.customer.telegram_id if customer_info.customer.telegram_id else None
                existing_customer.passport_image = customer_info.customer.passport_image if customer_info.customer.passport_image else None
            else:
                # Create new customer
                customer = CustomerModel(
                    national_id=customer_info.customer.national_id,
                    name=customer_info.customer.name,
                    phone=customer_info.customer.phone,
                    email=customer_info.customer.email if customer_info.customer.email else None,
                    address=customer_info.customer.address if customer_info.customer.address else None,
                    telegram_id=customer_info.customer.telegram_id if customer_info.customer.telegram_id else None,
                    passport_image=customer_info.customer.passport_image if customer_info.customer.passport_image else None
                )
                self.db_session.add(customer)

            # Handle companions
            if customer_info.has_companions:
                # Delete existing companions for this customer
                self.db_session.query(CompanionModel).filter(
                    CompanionModel.customer_national_id == customer_info.customer.national_id
                ).delete()

                # Add new companions
                for companion_data in customer_info.companions:
                    if companion_data.name.strip() and companion_data.national_id.strip():
                        companion = CompanionModel(
                            name=companion_data.name,
                            national_id=companion_data.national_id,
                            customer_national_id=companion_data.customer_national_id
                        )
                        self.db_session.add(companion)
            else:
                # Remove all companions if has_companions is False
                self.db_session.query(CompanionModel).filter(
                    CompanionModel.customer_national_id == customer_info.customer.national_id
                ).delete()

            self.db_session.commit()
            return True

        except SQLAlchemyError as e:
            print(f"Database error in save_customer_with_companions: {e}")
            self.db_session.rollback()
            return False

    def update_customer(self, customer_data: CustomerData) -> bool:
        """Update existing customer."""
        try:
            customer = self.db_session.query(CustomerModel).filter(
                CustomerModel.national_id == customer_data.national_id
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
        """Delete customer by national ID. Companions will be deleted automatically via CASCADE."""
        try:
            customer = self.db_session.query(CustomerModel).filter(
                CustomerModel.national_id == national_id
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
            return self.db_session.query(CustomerModel).filter(
                CustomerModel.national_id == national_id
            ).first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in customer_exists: {e}")
            return False

    def phone_exists(self, phone: str, exclude_national_id: str = None) -> bool:
        """Check if phone number exists (optionally excluding a specific customer)."""
        try:
            query = self.db_session.query(CustomerModel).filter(CustomerModel.phone == phone)
            if exclude_national_id:
                query = query.filter(CustomerModel.national_id != exclude_national_id)
            return query.first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in phone_exists: {e}")
            return False

    def companion_national_id_exists(self, national_id: str, exclude_companion_id: int = None) -> bool:
        """Check if companion national ID exists (optionally excluding a specific companion)."""
        try:
            query = self.db_session.query(CompanionModel).filter(CompanionModel.national_id == national_id)
            if exclude_companion_id:
                query = query.filter(CompanionModel.id != exclude_companion_id)
            return query.first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in companion_national_id_exists: {e}")
            return False

    def customer_national_id_exists_as_companion(self, national_id: str) -> bool:
        """Check if a national ID is already used as a companion."""
        try:
            return self.db_session.query(CompanionModel).filter(
                CompanionModel.national_id == national_id
            ).first() is not None

        except SQLAlchemyError as e:
            print(f"Database error in customer_national_id_exists_as_companion: {e}")
            return False

    def get_all_customers(self, limit: int = 100) -> List[CustomerData]:
        """Get all customers with optional limit."""
        try:
            customers = self.db_session.query(CustomerModel).limit(limit).all()
            return [self._convert_to_customer_data(customer) for customer in customers]

        except SQLAlchemyError as e:
            print(f"Database error in get_all_customers: {e}")
            return []

    def get_customer_count(self) -> int:
        """Get total number of customers."""
        try:
            return self.db_session.query(CustomerModel).count()

        except SQLAlchemyError as e:
            print(f"Database error in get_customer_count: {e}")
            return 0

    def get_companions_by_customer(self, customer_national_id: str) -> List[CompanionData]:
        """Get all companions for a specific customer."""
        try:
            companions = self.db_session.query(CompanionModel).filter(
                CompanionModel.customer_national_id == customer_national_id
            ).all()
            return [self._convert_to_companion_data(comp) for comp in companions]

        except SQLAlchemyError as e:
            print(f"Database error in get_companions_by_customer: {e}")
            return []

    def _convert_to_customer_data(self, customer) -> CustomerData:
        """Convert SQLAlchemy CustomerModel model to CustomerData dataclass."""
        return CustomerData(
            national_id=customer.national_id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email or "",
            address=customer.address or "",
            telegram_id=customer.telegram_id or "",
            passport_image=customer.passport_image or ""
        )

    def _convert_to_companion_data(self, companion) -> CompanionData:
        """Convert SQLAlchemy CompanionModel to CompanionData dataclass."""
        return CompanionData(
            id=companion.id,
            name=companion.name,
            national_id=companion.national_id,
            customer_national_id=companion.customer_national_id,
            ui_number=0  # Will be set by logic layer when loading
        )


class InMemoryCustomerRepository(ICustomerRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        self._customers: Dict[str, CustomerData] = {}
        self._companions: Dict[int, CompanionData] = {}
        self._companion_counter = 1

    def get_by_national_id(self, national_id: str) -> Optional[CustomerData]:
        return self._customers.get(national_id)

    def get_customer_with_companions(self, national_id: str) -> Optional[CustomerInfoData]:
        customer = self._customers.get(national_id)
        if not customer:
            return None

        companions = [comp for comp in self._companions.values()
                     if comp.customer_national_id == national_id]

        return CustomerInfoData(
            customer=customer,
            has_companions=len(companions) > 0,
            companions=companions
        )

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

    def save_customer_with_companions(self, customer_info: CustomerInfoData) -> bool:
        # Save customer
        self._customers[customer_info.customer.national_id] = customer_info.customer

        # Remove existing companions for this customer
        to_remove = [comp_id for comp_id, comp in self._companions.items()
                    if comp.customer_national_id == customer_info.customer.national_id]
        for comp_id in to_remove:
            del self._companions[comp_id]

        # Add new companions
        if customer_info.has_companions:
            customer_info.prepare_for_save()
            for companion in customer_info.companions:
                if companion.name.strip() and companion.national_id.strip():
                    companion.id = self._companion_counter
                    self._companions[self._companion_counter] = companion
                    self._companion_counter += 1

        return True

    def update_customer(self, customer_data: CustomerData) -> bool:
        if customer_data.national_id not in self._customers:
            return False
        self._customers[customer_data.national_id] = customer_data
        return True

    def delete_customer(self, national_id: str) -> bool:
        if national_id in self._customers:
            del self._customers[national_id]
            # Remove companions
            to_remove = [comp_id for comp_id, comp in self._companions.items()
                        if comp.customer_national_id == national_id]
            for comp_id in to_remove:
                del self._companions[comp_id]
            return True
        return False

    def customer_exists(self, national_id: str) -> bool:
        return national_id in self._customers

    def phone_exists(self, phone: str, exclude_national_id: str = None) -> bool:
        for customer in self._customers.values():
            if customer.phone == phone and customer.national_id != exclude_national_id:
                return True
        return False

    def companion_national_id_exists(self, national_id: str, exclude_companion_id: int = None) -> bool:
        for companion in self._companions.values():
            if companion.national_id == national_id and companion.id != exclude_companion_id:
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
