"""services_management_models.py - Database orm_models for services management"""

from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional

Base = declarative_base()


class ServicesModel(Base):
    """Model for services/documents table"""
    __tablename__ = 'Services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    base_price = Column(Integer, nullable=False, default=0)
    dynamic_price_name_1 = Column(String, nullable=True)
    dynamic_price_1 = Column(Integer, nullable=False, default=0)
    dynamic_price_name_2 = Column(String, nullable=True)
    dynamic_price_2 = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<ServicesModel(id={self.id}, name='{self.name}', base_price={self.base_price})>"

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'base_price': self.base_price,
            'dynamic_price_name_1': self.dynamic_price_name_1,
            'dynamic_price_1': self.dynamic_price_1,
            'dynamic_price_name_2': self.dynamic_price_name_2,
            'dynamic_price_2': self.dynamic_price_2
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from dictionary"""
        return cls(
            name=data.get('name', ''),
            base_price=data.get('base_price', 0),
            dynamic_price_name_1=data.get('dynamic_price_name_1'),
            dynamic_price_1=data.get('dynamic_price_1', 0),
            dynamic_price_name_2=data.get('dynamic_price_name_2'),
            dynamic_price_2=data.get('dynamic_price_2', 0)
        )


class FixedPricesModel(Base):
    """Model for fixed prices table"""
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    price = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<FixedPricesModel(id={self.id}, name='{self.name}', price={self.price}, is_default={self.is_default})>"

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'is_default': self.is_default
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from dictionary"""
        return cls(
            name=data.get('name', ''),
            price=data.get('price', 0),
            is_default=data.get('is_default', False)
        )


class OtherServicesModel(Base):
    """Model for other services table"""
    __tablename__ = 'other_services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    price = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<OtherServicesModel(id={self.id}, name='{self.name}', price={self.price}, is_default={self.is_default})>"

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'is_default': self.is_default
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create model instance from dictionary"""
        return cls(
            name=data.get('name', ''),
            price=data.get('price', 0),
            is_default=data.get('is_default', False)
        )


class DatabaseManager:
    """Database connection and session management"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()

    def close_session(self, session):
        """Close database session"""
        session.close()
