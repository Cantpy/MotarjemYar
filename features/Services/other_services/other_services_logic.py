# features/Services/other_services/other_services_logic.py

from typing import Any
from features.Services.other_services.other_services_repo import OtherServicesRepository
from features.Services.other_services.other_services_models import OtherServiceDTO
from shared.session_provider import SessionProvider


def _to_dto(model: "OtherServicesModel") -> OtherServiceDTO:
    """Helper to convert an ORM model to a DTO."""
    return OtherServiceDTO(id=model.id, name=model.name, price=model.price)


class OtherServicesLogic:
    """Business _logic for managing other services."""

    def __init__(self, repository: OtherServicesRepository, session_provider: "SessionProvider"):
        self._repo = repository
        self._session_provider = session_provider

    def _validate_data(self, data: dict[str, Any]):
        """Validates input data for creation or update."""
        name = data.get('name', '').strip()
        if not name:
            raise ValueError("نام خدمت نمی‌تواند خالی باشد.")

        try:
            price = int(data.get('price', 0))
            data['price'] = price
        except (ValueError, TypeError):
            raise ValueError("مقدار هزینه نامعتبر است. لطفا فقط عدد وارد کنید.")

        data['name'] = name

    def get_all_services(self) -> list[OtherServiceDTO]:
        with self._session_provider.services() as session:
            models = self._repo.get_all(session)
            return [_to_dto(model) for model in models]

    def create_service(self, data: dict[str, Any]) -> OtherServiceDTO:
        self._validate_data(data)
        with self._session_provider.services() as session:
            if self._repo.exists_by_name(session, data['name']):
                raise ValueError(f"خدمتی با نام '{data['name']}' از قبل وجود دارد.")
            new_model = self._repo.create(session, data)
            return _to_dto(new_model)

    def update_service(self, service_id: int, data: dict[str, Any]) -> OtherServiceDTO | None:
        self._validate_data(data)
        with self._session_provider.services() as session:
            if self._repo.exists_by_name(session, data['name'], exclude_id=service_id):
                raise ValueError(f"خدمتی با نام '{data['name']}' از قبل وجود دارد.")
            updated_model = self._repo.update(session, service_id, data)
            return _to_dto(updated_model) if updated_model else None

    def delete_service(self, service_id: int) -> bool:
        with self._session_provider.services() as session:
            return self._repo.delete(session, service_id)

    def delete_multiple_services(self, service_ids: list[int]) -> int:
        with self._session_provider.services() as session:
            return self._repo.delete_multiple(session, service_ids)
