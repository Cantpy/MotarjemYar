# shared/orm_models/services_models.py

from __future__ import annotations
from sqlalchemy import Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base

BaseServices = declarative_base()


class ServicesModel(BaseServices):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    base_price: Mapped[int | None] = mapped_column(Integer)

    # relationship to dynamic fees
    dynamic_fees: Mapped[list["ServiceDynamicFee"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ServicesModel(id={self.id}, name={self.name!r}, base_price={self.base_price})>"


class ServiceDynamicFee(BaseServices):
    __tablename__ = 'service_dynamic_fees'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)

    service: Mapped["ServicesModel"] = relationship(back_populates="dynamic_fees")

    def __repr__(self) -> str:
        return (f"<ServiceDynamicFee(id={self.id}, service_id={self.service_id}, "
                f"name={self.name!r}, unit_price={self.unit_price})>")


class FixedPricesModel(BaseServices):
    __tablename__ = 'fixed_prices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __repr__(self) -> str:
        return f"<FixedPricesModel(id={self.id}, name={self.name!r}, price={self.price})>"


class OtherServicesModel(BaseServices):
    __tablename__ = 'other_services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<OtherServicesModel(id={self.id}, name={self.name!r}, price={self.price})>"
