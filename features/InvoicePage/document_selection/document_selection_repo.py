from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from features.InvoicePage.document_selection.document_selection_models import Service, OtherService, FixedPrice

Base = declarative_base()


class ServiceEntity(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    base_price = Column(Integer)
    dynamic_price_name_1 = Column(Text)
    dynamic_price_1 = Column(Integer)
    dynamic_price_name_2 = Column(Text)
    dynamic_price_2 = Column(Integer)


class OtherServiceEntity(Base):
    __tablename__ = 'other_services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False)


class FixedPriceEntity(Base):
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    price = Column(Integer, nullable=False)
    is_default = Column(Boolean, nullable=False)
    label_name = Column(Text)


class DatabaseRepository:
    """Repository for database operations"""

    def __init__(self, database_url: str = "sqlite:///services.db"):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def get_all_services(self) -> List[Service]:
        """Get all services from database"""
        with self.get_session() as session:
            entities = session.query(ServiceEntity).all()
            return [
                Service(
                    id=entity.id,
                    name=entity.name,
                    base_price=entity.base_price,
                    dynamic_price_name_1=entity.dynamic_price_name_1,
                    dynamic_price_1=entity.dynamic_price_1,
                    dynamic_price_name_2=entity.dynamic_price_name_2,
                    dynamic_price_2=entity.dynamic_price_2
                )
                for entity in entities
            ]

    def get_all_other_services(self) -> List[OtherService]:
        """Get all other services from database"""
        with self.get_session() as session:
            entities = session.query(OtherServiceEntity).all()
            return [
                OtherService(
                    id=entity.id,
                    name=entity.name,
                    price=entity.price
                )
                for entity in entities
            ]

    def get_service_by_name(self, name: str) -> Optional[Service]:
        """Get service by name"""
        with self.get_session() as session:
            entity = session.query(ServiceEntity).filter(ServiceEntity.name == name).first()
            if entity:
                return Service(
                    id=entity.id,
                    name=entity.name,
                    base_price=entity.base_price,
                    dynamic_price_name_1=entity.dynamic_price_name_1,
                    dynamic_price_1=entity.dynamic_price_1,
                    dynamic_price_name_2=entity.dynamic_price_name_2,
                    dynamic_price_2=entity.dynamic_price_2
                )
            return None

    def get_other_service_by_name(self, name: str) -> Optional[OtherService]:
        """Get other service by name"""
        with self.get_session() as session:
            entity = session.query(OtherServiceEntity).filter(OtherServiceEntity.name == name).first()
            if entity:
                return OtherService(
                    id=entity.id,
                    name=entity.name,
                    price=entity.price
                )
            return None

    def get_all_fixed_prices(self) -> List[FixedPrice]:
        """Get all fixed prices"""
        with self.get_session() as session:
            entities = session.query(FixedPriceEntity).all()
            return [
                FixedPrice(
                    id=entity.id,
                    name=entity.name,
                    price=entity.price,
                    is_default=entity.is_default,
                    label_name=entity.label_name
                )
                for entity in entities
            ]

    def get_fixed_price_by_name(self, name: str) -> Optional[FixedPrice]:
        """Get fixed price by name"""
        with self.get_session() as session:
            entity = session.query(FixedPriceEntity).filter(FixedPriceEntity.name == name).first()
            if entity:
                return FixedPrice(
                    id=entity.id,
                    name=entity.name,
                    price=entity.price,
                    is_default=entity.is_default,
                    label_name=entity.label_name
                )
            return None

    def get_all_document_names(self) -> List[str]:
        """Get all available document names for autocomplete"""
        services = self.get_all_services()
        other_services = self.get_all_other_services()

        names = [service.name for service in services]
        names.extend([service.name for service in other_services])

        return sorted(names)

    def document_exists(self, name: str) -> bool:
        """Check if document exists in either services or other_services"""
        service = self.get_service_by_name(name)
        other_service = self.get_other_service_by_name(name)
        return service is not None or other_service is not None
