# shared/orm_models/business_models.py

from __future__ import annotations
from sqlalchemy import Integer, Text, Index, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

BaseCustomers = declarative_base()


class CustomerModel(BaseCustomers):
    __tablename__ = 'customers'

    national_id: Mapped[str] = mapped_column(Integer, primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_id: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    passport_image: Mapped[str | None] = mapped_column(Text)

    companions: Mapped[list["CompanionModel"]] = relationship(
        "CompanionModel",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_customers_national_id', 'national_id'),
        Index('idx_customers_phone', 'phone'),
        Index('idx_customers_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<CustomerModel(national_id={self.national_id}, name={self.name!r}, phone={self.phone!r})>"


class CompanionModel(BaseCustomers):
    __tablename__ = 'companions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    national_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    customer_national_id: Mapped[str] = mapped_column(
        Integer,
        ForeignKey('customers.national_id', ondelete="CASCADE"),
        nullable=False
    )

    customer: Mapped[CustomerModel] = relationship(
        "CustomerModel",
        back_populates="companions"
    )

    __table_args__ = (
        Index('idx_companions_national_id', 'national_id'),
        Index('idx_companions_customer_national_id', 'customer_national_id'),
        Index('idx_companions_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<CompanionModel(id={self.id}, name={self.name!r}, national_id={self.national_id!r})>"
