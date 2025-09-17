
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from shared.orm_models.services_models import ServicesModel
from features.Services.documents.documents_models import ServicesDTO


class ServiceRepository:
    """Repository for ServicesModel model operations"""

    def get_all(self, session: Session) -> list[ServicesDTO]:
        """Get all services"""
        return session.query(ServicesModel).order_by(ServicesModel.name).all()

    def get_by_id(self, session: Session, service_id: int) -> ServicesDTO | None:
        """Get service by ID"""

        return session.query(ServicesModel).filter(ServicesModel.id == service_id).first()

    def get_by_name(self, session: Session, name: str) -> ServicesDTO | None:
        """Get service by name"""
        return session.query(ServicesModel).filter(ServicesModel.name == name).first()

    def create(self, session: Session, service_data: dict[str, object]) -> ServicesDTO:
        """Create new service"""
        service = ServicesModel.from_dict(service_data)
        session.add(service)
        session.flush()  # Get the ID without committing
        return service

    def update(self, session: Session, service_id: int, service_data: dict[str, object]) -> ServicesDTO | None:
        """Update existing service"""
        service = session.query(ServicesModel).filter(ServicesModel.id == service_id).first()
        if not service:
            return None

        for key, value in service_data.items():
            if hasattr(service, key):
                setattr(service, key, value)

        return service

    def delete(self, session: Session, service_id: int) -> bool:
        """Delete service by ID"""
        service = session.query(ServicesModel).filter(ServicesModel.id == service_id).first()
        if not service:
            return False
        session.delete(service)
        return True

    def delete_multiple(self, session: Session, service_ids: list[int]) -> int:
        """Delete multiple services by IDs"""
        deleted_count = session.query(ServicesModel).filter(ServicesModel.id.in_(service_ids)).delete(synchronize_session=False)
        return deleted_count

    def delete_all(self, session: Session) -> int:
        """Delete all services"""
        deleted_count = session.query(ServicesModel).delete()
        return deleted_count

    def search(self, session: Session, search_term: str) -> list[ServicesDTO]:
        """Search services by name"""
        return session.query(ServicesModel).filter(
                    ServicesModel.name.ilike(f'%{search_term}%')
                    ).order_by(ServicesModel.name).all()

    def exists_by_name(self, session: Session, name: str, exclude_id: int | None = None) -> bool:
        """Check if service with name exists"""
        query = session.query(ServicesModel).filter(ServicesModel.name == name)
        if exclude_id:
            query = query.filter(ServicesModel.id != exclude_id)
        return query.first() is not None

    def bulk_create(self, session: Session, services_data: list[dict[str, object]]) -> int:
        """
        Bulk inserts multiple services from a list of dictionaries.
        This is much more efficient than one-by-one creation.
        """
        if not services_data:
            return 0

        try:
            # We map dictionaries to the ServicesModel objects
            service_objects = [ServicesModel(**data) for data in services_data]
            session.bulk_save_objects(service_objects)
            return len(service_objects)
        except SQLAlchemyError as e:
            # The _logic layer will catch this and report the error.
            raise Exception(f"Database bulk insert failed: {e}")
