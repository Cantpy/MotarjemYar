# shared/orm_models/license_model.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

BaseLicense = declarative_base()


class LicenseModel(BaseLicense):
    __tablename__ = 'licenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    license_key = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    app_version = Column(String, nullable=False, default='freelancer')

    max_admins = Column(Integer, nullable=False, default=1)
    max_translators = Column(Integer, nullable=False, default=1)
    max_clerks = Column(Integer, nullable=False, default=0)
    max_accountants = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("app_version IN ('freelancer', 'office', 'enterprise')", name='check_app_version'),
    )

    def __repr__(self):
        return f"<LicenseModel(id={self.id}, license_key='{self.license_key}', version='{self.app_version}')>"
