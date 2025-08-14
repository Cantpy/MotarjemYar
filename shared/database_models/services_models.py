from __future__ import annotations
from sqlalchemy import Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

BaseServices = declarative_base()


class ServicesModel(BaseServices):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    base_price: Mapped[int | None] = mapped_column(Integer)
    dynamic_price_name_1: Mapped[str | None] = mapped_column(Text)
    dynamic_price_1: Mapped[int | None] = mapped_column(Integer)
    dynamic_price_name_2: Mapped[str | None] = mapped_column(Text)
    dynamic_price_2: Mapped[int | None] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"<ServicesModel(id={self.id}, name={self.name!r}, base_price={self.base_price})>"


class FixedPricesModel(BaseServices):
    __tablename__ = 'fixed_prices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False)
    label_name: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<FixedPricesModel(id={self.id}, name={self.name!r}, price={self.price})>"


class OtherServicesModel(BaseServices):
    __tablename__ = 'other_services'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<OtherServicesModel(id={self.id}, name={self.name!r}, price={self.price})>"
