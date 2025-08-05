from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from modules.helper_functions import return_resource

Base = declarative_base()

# Get database path
documents_database = return_resource('databases', 'documents.db')


class FixedPricesModel(Base):
    """SQLAlchemy model for fixed_prices table."""
    __tablename__ = 'fixed_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    price = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<FixedPricesModel(id={self.id}, name='{self.name}', price={self.price}, is_default={self.is_default})>"

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'is_default': self.is_default
        }


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, database_path: str = None):
        if database_path is None:
            database_path = documents_database

        self.engine = create_engine(f'sqlite:///{database_path}')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()

    def close_session(self, session):
        """Close database session."""
        if session:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()
