# features/Services/fixed_prices/fixed_prices_repo.py

from typing import Any
from sqlalchemy.orm import Session
from shared.orm_models.services_models import FixedPricesModel


class FixedPricesRepository:
    """Repository for FixedPricesModel operations using SQLAlchemy."""

    def get_all(self, session: Session) -> list[FixedPricesModel]:
        """Get all fixed prices, ordered by default status then name."""
        return session.query(FixedPricesModel).order_by(
            FixedPricesModel.is_default.desc(),
            FixedPricesModel.name
        ).all()

    def get_by_id(self, session: Session, cost_id: int) -> FixedPricesModel | None:
        """Get a single fixed price by its primary key."""
        return session.get(FixedPricesModel, cost_id)

    def exists_by_name(self, session: Session, name: str, exclude_id: int | None = None) -> bool:
        """Check if a fixed price with the given name exists."""
        query = session.query(FixedPricesModel).filter(FixedPricesModel.name == name)
        if exclude_id:
            query = query.filter(FixedPricesModel.id != exclude_id)
        return query.first() is not None

    def create(self, session: Session, data: dict[str, Any]) -> FixedPricesModel:
        """Create a new fixed price."""
        # is_default is false for all user-created prices
        new_price = FixedPricesModel(name=data['name'], price=data['price'], is_default=False)
        session.add(new_price)
        session.flush() # To get the ID before committing
        return new_price

    def update(self, session: Session, cost_id: int, data: dict[str, Any]) -> FixedPricesModel | None:
        """Update an existing fixed price."""
        price_to_update = self.get_by_id(session, cost_id)
        if price_to_update:
            price_to_update.name = data['name']
            price_to_update.price = data['price']
            session.flush()
        return price_to_update

    def delete(self, session: Session, cost_id: int) -> bool:
        """Delete a non-default fixed price by its ID."""
        # The business rule (is_default=False) is enforced here at the query level
        result = session.query(FixedPricesModel).filter(
            FixedPricesModel.id == cost_id,
            FixedPricesModel.is_default == False
        ).delete()
        return result > 0 # Returns the number of rows deleted

    def delete_multiple(self, session: Session, cost_ids: list[int]) -> int:
        """Delete multiple non-default fixed prices by their IDs."""
        deleted_count = session.query(FixedPricesModel).filter(
            FixedPricesModel.id.in_(cost_ids),
            FixedPricesModel.is_default == False
        ).delete(synchronize_session=False)
        return deleted_count
