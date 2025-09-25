# features/Services/repositories/services_repo.py

from typing import Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from shared.orm_models.services_models import ServicesModel, ServiceDynamicFee


class ServiceRepository:
    """Repository for ServicesModel model operations."""

    def get_all(self, session: Session) -> list[ServicesModel]:
        """
        Get all services and EAGERLY LOAD their related dynamic fees
        to prevent the N+1 query problem.
        """
        return (
            session.query(ServicesModel)
            .options(joinedload(ServicesModel.dynamic_fees))
            .order_by(ServicesModel.name)
            .all()
        )

    def get_by_id(self, session: Session, service_id: int) -> ServicesModel | None:
        return session.query(ServicesModel).filter(ServicesModel.id == service_id).first()

    def get_by_name(self, session: Session, name: str) -> ServicesModel | None:
        return session.query(ServicesModel).filter(ServicesModel.name == name).first()

    def create_service_with_fees(self, session: Session, data: dict) -> ServicesModel:
        """
        Creates a new service and its associated dynamic fees in one go.
        SQLAlchemy's relationship management handles the foreign keys.
        """
        # Create the list of child ServiceDynamicFee objects
        fee_objects = [
            ServiceDynamicFee(name=fee['name'], unit_price=fee['unit_price'])
            for fee in data.get('dynamic_fees', [])
        ]

        # Create the parent ServicesModel object
        new_service = ServicesModel(
            name=data['name'],
            base_price=data['base_price'],
            dynamic_fees=fee_objects
        )

        session.add(new_service)
        session.flush()
        print(f'new services created in repo: {new_service}')
        return new_service

    def update(self, session: Session, service_id: int, service_data: dict) -> ServicesModel | None:
        """
        Updates a service and its dynamic fees.
        """
        # Use joinedload to efficiently fetch the service and its fees in one query
        service = session.query(ServicesModel).options(joinedload(ServicesModel.dynamic_fees)).filter(
            ServicesModel.id == service_id).first()

        if not service:
            return None

        service.name = service_data.get('name', service.name)
        service.base_price = service_data.get('base_price', service.base_price)

        if "dynamic_fees" in service_data:
            service.dynamic_fees.clear()

            new_fees_data = service_data["dynamic_fees"]
            for fee_data in new_fees_data:
                new_fee = ServiceDynamicFee(
                    name=fee_data['name'],
                    unit_price=fee_data['unit_price']
                )
                service.dynamic_fees.append(new_fee)

        return service

    def delete(self, session: Session, service_id: int) -> bool:
        service = session.query(ServicesModel).filter(ServicesModel.id == service_id).first()
        if not service:
            return False
        session.delete(service)
        return True

    def delete_multiple(self, session: Session, service_ids: list[int]) -> int:
        # 1. Load all the parent objects you intend to delete.
        services_to_delete = session.query(ServicesModel).filter(
            ServicesModel.id.in_(service_ids)
        ).all()

        if not services_to_delete:
            return 0

        # 2. Loop through and delete them. SQLAlchemy will manage the cascade for each.
        for service in services_to_delete:
            session.delete(service)

        return len(services_to_delete)

    def delete_all(self, session: Session) -> int:
        return session.query(ServicesModel).delete()

    def search(self, session: Session, search_term: str) -> list[ServicesModel]:
        return session.query(ServicesModel).filter(
            ServicesModel.name.ilike(f"%{search_term}%")
        ).order_by(ServicesModel.name).all()

    def exists_by_name(self, session: Session, name: str, exclude_id: int | None = None) -> bool:
        query = session.query(ServicesModel).filter(ServicesModel.name == name)
        if exclude_id:
            query = query.filter(ServicesModel.id != exclude_id)
        return query.first() is not None

    def bulk_create(self, session: Session, services_data: list[dict[str, Any]]) -> int:
        if not services_data:
            return 0
        try:
            for data in services_data:
                dynamic_fees_data = data.pop("dynamic_fees", [])
                service = ServicesModel(**data)
                for fee in dynamic_fees_data:
                    service.dynamic_fees.append(ServiceDynamicFee(**fee))
                session.add(service)
            session.flush()
            return len(services_data)
        except SQLAlchemyError as e:
            raise Exception(f"Database bulk insert failed: {e}")
