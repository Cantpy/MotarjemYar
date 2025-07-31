"""services_management_repo.py - Repository layer for database operations using SQLAlchemy ORM"""

from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from services_management_models import Service, FixedPrice, OtherService, DatabaseManager


class BaseRepository:
    """Base repository with common database operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def _execute_with_session(self, operation, *args, **kwargs):
        """Execute operation with automatic session management"""
        session = self.db_manager.get_session()
        try:
            result = operation(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.db_manager.close_session(session)


class ServiceRepository(BaseRepository):
    """Repository for Service model operations"""

    def get_all(self) -> List[Service]:
        """Get all services"""

        def operation(session: Session):
            return session.query(Service).order_by(Service.name).all()

        return self._execute_with_session(operation)

    def get_by_id(self, service_id: int) -> Optional[Service]:
        """Get service by ID"""

        def operation(session: Session):
            return session.query(Service).filter(Service.id == service_id).first()

        return self._execute_with_session(operation)

    def get_by_name(self, name: str) -> Optional[Service]:
        """Get service by name"""

        def operation(session: Session):
            return session.query(Service).filter(Service.name == name).first()

        return self._execute_with_session(operation)

    def create(self, service_data: Dict[str, Any]) -> Service:
        """Create new service"""

        def operation(session: Session):
            service = Service.from_dict(service_data)
            session.add(service)
            session.flush()  # Get the ID without committing
            return service

        return self._execute_with_session(operation)

    def update(self, service_id: int, service_data: Dict[str, Any]) -> Optional[Service]:
        """Update existing service"""

        def operation(session: Session):
            service = session.query(Service).filter(Service.id == service_id).first()
            if not service:
                return None

            for key, value in service_data.items():
                if hasattr(service, key):
                    setattr(service, key, value)

            return service

        return self._execute_with_session(operation)

    def delete(self, service_id: int) -> bool:
        """Delete service by ID"""

        def operation(session: Session):
            service = session.query(Service).filter(Service.id == service_id).first()
            if not service:
                return False
            session.delete(service)
            return True

        return self._execute_with_session(operation)

    def delete_multiple(self, service_ids: List[int]) -> int:
        """Delete multiple services by IDs"""

        def operation(session: Session):
            deleted_count = session.query(Service).filter(Service.id.in_(service_ids)).delete(synchronize_session=False)
            return deleted_count

        return self._execute_with_session(operation)

    def delete_all(self) -> int:
        """Delete all services"""

        def operation(session: Session):
            deleted_count = session.query(Service).delete()
            return deleted_count

        return self._execute_with_session(operation)

    def search(self, search_term: str) -> List[Service]:
        """Search services by name"""

        def operation(session: Session):
            return session.query(Service).filter(
                Service.name.ilike(f'%{search_term}%')
            ).order_by(Service.name).all()

        return self._execute_with_session(operation)

    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if service with name exists"""

        def operation(session: Session):
            query = session.query(Service).filter(Service.name == name)
            if exclude_id:
                query = query.filter(Service.id != exclude_id)
            return query.first() is not None

        return self._execute_with_session(operation)


class FixedPriceRepository(BaseRepository):
    """Repository for FixedPrice model operations"""

    def get_all(self) -> List[FixedPrice]:
        """Get all fixed prices"""

        def operation(session: Session):
            return session.query(FixedPrice).order_by(
                FixedPrice.is_default.desc(), FixedPrice.name
            ).all()

        return self._execute_with_session(operation)

    def get_by_id(self, price_id: int) -> Optional[FixedPrice]:
        """Get fixed price by ID"""

        def operation(session: Session):
            return session.query(FixedPrice).filter(FixedPrice.id == price_id).first()

        return self._execute_with_session(operation)

    def get_by_name(self, name: str) -> Optional[FixedPrice]:
        """Get fixed price by name"""

        def operation(session: Session):
            return session.query(FixedPrice).filter(FixedPrice.name == name).first()

        return self._execute_with_session(operation)

    def create(self, price_data: Dict[str, Any]) -> FixedPrice:
        """Create new fixed price"""

        def operation(session: Session):
            fixed_price = FixedPrice.from_dict(price_data)
            session.add(fixed_price)
            session.flush()
            return fixed_price

        return self._execute_with_session(operation)

    def update(self, price_id: int, price_data: Dict[str, Any]) -> Optional[FixedPrice]:
        """Update existing fixed price"""

        def operation(session: Session):
            fixed_price = session.query(FixedPrice).filter(FixedPrice.id == price_id).first()
            if not fixed_price:
                return None

            for key, value in price_data.items():
                if hasattr(fixed_price, key):
                    setattr(fixed_price, key, value)

            return fixed_price

        return self._execute_with_session(operation)

    def delete(self, price_id: int) -> bool:
        """Delete fixed price by ID (only non-default)"""

        def operation(session: Session):
            fixed_price = session.query(FixedPrice).filter(
                FixedPrice.id == price_id,
                FixedPrice.is_default == False
            ).first()
            if not fixed_price:
                return False
            session.delete(fixed_price)
            return True

        return self._execute_with_session(operation)

    def delete_multiple(self, price_ids: List[int]) -> int:
        """Delete multiple fixed prices by IDs (only non-default)"""

        def operation(session: Session):
            deleted_count = session.query(FixedPrice).filter(
                FixedPrice.id.in_(price_ids),
                FixedPrice.is_default == False
            ).delete(synchronize_session=False)
            return deleted_count

        return self._execute_with_session(operation)

    def search(self, search_term: str) -> List[FixedPrice]:
        """Search fixed prices by name"""

        def operation(session: Session):
            return session.query(FixedPrice).filter(
                FixedPrice.name.ilike(f'%{search_term}%')
            ).order_by(FixedPrice.is_default.desc(), FixedPrice.name).all()

        return self._execute_with_session(operation)

    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if fixed price with name exists"""

        def operation(session: Session):
            query = session.query(FixedPrice).filter(FixedPrice.name == name)
            if exclude_id:
                query = query.filter(FixedPrice.id != exclude_id)
            return query.first() is not None

        return self._execute_with_session(operation)


class OtherServiceRepository(BaseRepository):
    """Repository for OtherService model operations"""

    def get_all(self) -> List[OtherService]:
        """Get all other services"""

        def operation(session: Session):
            return session.query(OtherService).order_by(OtherService.name).all()

        return self._execute_with_session(operation)

    def get_by_id(self, service_id: int) -> Optional[OtherService]:
        """Get other service by ID"""

        def operation(session: Session):
            return session.query(OtherService).filter(OtherService.id == service_id).first()

        return self._execute_with_session(operation)

    def get_by_name(self, name: str) -> Optional[OtherService]:
        """Get other service by name"""

        def operation(session: Session):
            return session.query(OtherService).filter(OtherService.name == name).first()

        return self._execute_with_session(operation)

    def create(self, service_data: Dict[str, Any]) -> OtherService:
        """Create new other service"""

        def operation(session: Session):
            other_service = OtherService.from_dict(service_data)
            session.add(other_service)
            session.flush()
            return other_service

        return self._execute_with_session(operation)

    def update(self, service_id: int, service_data: Dict[str, Any]) -> Optional[OtherService]:
        """Update existing other service"""

        def operation(session: Session):
            other_service = session.query(OtherService).filter(OtherService.id == service_id).first()
            if not other_service:
                return None

            for key, value in service_data.items():
                if hasattr(other_service, key):
                    setattr(other_service, key, value)

            return other_service

        return self._execute_with_session(operation)

    def delete(self, service_id: int) -> bool:
        """Delete other service by ID (only non-default)"""

        def operation(session: Session):
            other_service = session.query(OtherService).filter(
                OtherService.id == service_id,
                OtherService.is_default == False
            ).first()
            if not other_service:
                return False
            session.delete(other_service)
            return True

        return self._execute_with_session(operation)

    def delete_multiple(self, service_ids: List[int]) -> int:
        """Delete multiple other services by IDs (only non-default)"""

        def operation(session: Session):
            deleted_count = session.query(OtherService).filter(
                OtherService.id.in_(service_ids),
                OtherService.is_default == False
            ).delete(synchronize_session=False)
            return deleted_count

        return self._execute_with_session(operation)

    def search(self, search_term: str) -> List[OtherService]:
        """Search other services by name"""

        def operation(session: Session):
            return session.query(OtherService).filter(
                OtherService.name.ilike(f'%{search_term}%')
            ).order_by(OtherService.name).all()

        return self._execute_with_session(operation)

    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if other service with name exists"""

        def operation(session: Session):
            query = session.query(OtherService).filter(OtherService.name == name)
            if exclude_id:
                query = query.filter(OtherService.id != exclude_id)
            return query.first() is not None

        return self._execute_with_session(operation)
