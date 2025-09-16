# features/Services/fixed_prices/fixed_prices_logic.py

from typing import Any
from features.Services.fixed_prices.fixed_prices_repo import FixedPricesRepository
from features.Services.fixed_prices.fixed_prices_models import FixedPriceDTO

from shared.session_provider import SessionProvider


def _to_dto(model: "FixedPricesModel") -> FixedPriceDTO:
    """Helper function to convert an ORM model to a DTO."""
    return FixedPriceDTO(
        id=model.id,
        name=model.name,
        price=model.price,
        is_default=model.is_default,
        label_name=model.label_name
    )


class FixedPricesLogic:
    """Business logic for managing fixed prices."""

    def __init__(self, repository: FixedPricesRepository, session_provider: SessionProvider):
        self._repo = repository
        self._session_provider = session_provider

    def _validate_data(self, data: dict[str, Any]):
        """Validates input data for creation or update."""
        name = data.get('name', '').strip()
        if not name:
            raise ValueError("نام هزینه ثابت نمی‌تواند خالی باشد.")

        try:
            # Ensure price is a valid integer
            price = int(data.get('price', 0))
            data['price'] = price  # Store the cleaned integer value
        except (ValueError, TypeError):
            raise ValueError("مقدار هزینه نامعتبر است. لطفا فقط عدد وارد کنید.")

        data['name'] = name  # Store the cleaned name

    def get_all_fixed_prices(self) -> list[FixedPriceDTO]:
        """Get all fixed prices."""
        with self._session_provider.services() as session:
            models = self._repo.get_all(session)
            return [_to_dto(model) for model in models]

    def create_fixed_price(self, data: dict[str, Any]) -> FixedPriceDTO:
        """Create a new fixed price after validation."""
        self._validate_data(data)
        with self._session_provider.services() as session:
            if self._repo.exists_by_name(session, data['name']):
                raise ValueError(f"هزینه‌ای با نام '{data['name']}' از قبل وجود دارد.")

            new_model = self._repo.create(session, data)
            return _to_dto(new_model)

    def update_fixed_price(self, cost_id: int, data: dict[str, Any]) -> FixedPriceDTO | None:
        """Update an existing fixed price after validation."""
        self._validate_data(data)
        with self._session_provider.services() as session:
            if self._repo.exists_by_name(session, data['name'], exclude_id=cost_id):
                raise ValueError(f"هزینه‌ای با نام '{data['name']}' از قبل وجود دارد.")

            updated_model = self._repo.update(session, cost_id, data)
            return _to_dto(updated_model) if updated_model else None

    def delete_fixed_price(self, cost_id: int) -> bool:
        """Delete a single fixed price. The repo handles the 'is_default' rule."""
        with self._session_provider.services() as session:
            return self._repo.delete(session, cost_id)

    def delete_multiple_prices(self, cost_ids: list[int]) -> int:
        """Delete multiple fixed prices."""
        with self._session_provider.services() as session:
            return self._repo.delete_multiple(session, cost_ids)
