# features/Services/other_services/other_services_repo.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from shared.orm_models.services_models import OtherServicesModel


class OtherServicesRepository:
    """Repository for OtherServicesModel operations."""

    def get_all(self, session: Session) -> List["OtherServicesModel"]:
        """Get all 'other services', ordered by name."""
        return session.query(OtherServicesModel).order_by(OtherServicesModel.name).all()

    def get_by_id(self, session: Session, service_id: int) -> Optional["OtherServicesModel"]:
        """Get a single service by its ID."""
        return session.get(OtherServicesModel, service_id)

    def exists_by_name(self, session: Session, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if a service with the given name exists."""
        query = session.query(OtherServicesModel).filter(OtherServicesModel.name == name)
        if exclude_id:
            query = query.filter(OtherServicesModel.id != exclude_id)
        return query.first() is not None

    def create(self, session: Session, data: Dict[str, Any]) -> "OtherServicesModel":
        """Create a new service."""
        new_service = OtherServicesModel(name=data['name'], price=data['price'])
        session.add(new_service)
        session.flush()
        return new_service

    def update(self, session: Session, service_id: int, data: Dict[str, Any]) -> Optional["OtherServicesModel"]:
        """Update an existing service."""
        service_to_update = self.get_by_id(session, service_id)
        if service_to_update:
            service_to_update.name = data['name']
            service_to_update.price = data['price']
            session.flush()
        return service_to_update

    def delete(self, session: Session, service_id: int) -> bool:
        """Delete a service by its ID."""
        result = session.query(OtherServicesModel).filter(OtherServicesModel.id == service_id).delete()
        return result > 0

    def delete_multiple(self, session: Session, service_ids: List[int]) -> int:
        """Delete multiple services by their IDs."""
        deleted_count = session.query(OtherServicesModel).filter(
            OtherServicesModel.id.in_(service_ids)
        ).delete(synchronize_session=False)
        return deleted_count
