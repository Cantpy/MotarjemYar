# shared/orm_models/services_models.py

from __future__ import annotations
from sqlalchemy import Integer, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

BaseServices = declarative_base()


class ServicesModel(BaseServices):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    base_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    default_page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    dynamic_prices: Mapped[list["ServiceDynamicPrice"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )

    aliases: Mapped[list["ServiceAlias"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ServicesModel(id={self.id}, name={self.name!r}, type={self.type!r}, "
            f"base_price={self.base_price}, default_page_count={self.default_page_count})>"
        )


class ServiceDynamicPrice(BaseServices):
    __tablename__ = 'service_dynamic_prices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    service: Mapped["ServicesModel"] = relationship(back_populates="dynamic_prices")

    aliases: Mapped[list["ServiceDynamicPriceAlias"]] = relationship(
        back_populates="dynamic_price", cascade="all, delete-orphan"
    )

    def to_dto(self) -> "DynamicPrice":
        """Converts this ORM instance to a DynamicPrice DTO."""
        from features.Invoice_Page.document_selection.document_selection_models import DynamicPrice
        return DynamicPrice(
            id=self.id,
            service_id=self.service_id,
            name=self.name,
            unit_price=self.unit_price,
            aliases=[alias.alias for alias in self.aliases],
        )


class ServiceAlias(BaseServices):
    __tablename__ = 'service_aliases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(Text, nullable=False)

    service: Mapped["ServicesModel"] = relationship(back_populates="aliases")


class ServiceDynamicPriceAlias(BaseServices):
    __tablename__ = 'service_dynamic_price_aliases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dynamic_price_id: Mapped[int] = mapped_column(
        ForeignKey("service_dynamic_prices.id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)

    dynamic_price: Mapped["ServiceDynamicPrice"] = relationship(back_populates="aliases")

    def __repr__(self) -> str:
        return f"<ServiceDynamicPriceAlias(id={self.id}, alias={self.alias!r})>"


class SmartSearchHistoryModel(BaseServices):
    __tablename__ = 'smart_search_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SmartSearchHistoryModel(id={self.id}, entry={self.entry!r})>"


class FixedPricesModel(BaseServices):
    __tablename__ = 'fixed_prices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<FixedPricesModel(id={self.id}, name={self.name!r}, price={self.price})>"


class OtherServicesModel(BaseServices):
    __tablename__ = 'other_services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<OtherServicesModel(id={self.id}, name={self.name!r}, price={self.price})>"
