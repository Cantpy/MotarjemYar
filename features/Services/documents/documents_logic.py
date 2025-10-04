# features/Services/documents/documents_logic.py

from typing import Any

from features.Services.documents.documents_repo import ServiceRepository
from features.Services.documents.documents_models import ServicesDTO, ServiceDynamicFeeDTO
from shared.session_provider import ManagedSessionProvider
from shared.orm_models.services_models import ServicesModel


def _to_dto(model: ServicesModel) -> ServicesDTO:
    return ServicesDTO(
        id=model.id,
        name=model.name,
        base_price=model.base_price,
        default_page_count=model.default_page_count,
        aliases=[alias.alias for alias in model.aliases],
        dynamic_prices=[
            ServiceDynamicFeeDTO(
                id=df.id,
                service_id=df.service_id,
                name=df.name if df.name else "",
                unit_price=df.unit_price,
                aliases=[alias.alias for alias in df.aliases]
            )
            for df in model.dynamic_prices
        ]
    )


class ServicesLogic:
    """
    Business logic for services management.
    """

    def __init__(self, repo: ServiceRepository, services_engine: ManagedSessionProvider):
        self._repo = repo
        self._services_session = services_engine
        self.test_database_connection()

    def get_all_services(self) -> list[ServicesDTO]:
        with self._services_session() as session:
            service_models = self._repo.get_all(session)
            return [_to_dto(model) for model in service_models]

    def get_service_with_aliases(self, service_id: int) -> ServicesDTO | None:
        """Fetches a single service with all its related aliases."""
        with self._services_session() as session:
            service_model = self._repo.get_by_id_with_aliases(session, service_id)
            return _to_dto(service_model) if service_model else None

    def update_aliases(self, service_id: int, aliases_data: dict) -> bool:
        """Updates the aliases for a service and its dynamic prices."""
        with self._services_session() as session:
            return self._repo.update_aliases(session, service_id, aliases_data)

    def update_service_properties(self, service_id: int, properties_data: dict) -> ServicesDTO | None:
        """Updates the properties for a service (aliases, page count, etc.)."""
        with self._services_session() as session:
            updated_model = self._repo.update_service_properties(session, service_id, properties_data)
            return _to_dto(updated_model) if updated_model else None

    def create_service(self, service_data: dict[str, Any]) -> ServicesDTO:
        """Create a new service. The input dict is now correctly structured."""
        normalized_data = self._normalize_service_data(service_data)
        self._validate_service_data(normalized_data)

        with self._services_session() as session:
            if self._repo.exists_by_name(session, normalized_data['name']):
                raise ValueError(f"مدرکی با نام '{normalized_data['name']}' از قبل وجود دارد.")

            new_model = self._repo.create_service_with_prices(session, normalized_data)
            return _to_dto(new_model)

    def update_service(self, service_id: int, service_data: dict[str, Any]) -> ServicesDTO | None:
        normalized_data = self._normalize_service_data(service_data)
        self._validate_service_data(normalized_data)

        with self._services_session() as session:
            if self._repo.exists_by_name(session, normalized_data['name'], exclude_id=service_id):
                raise ValueError(f"مدرکی با نام '{normalized_data['name']}' از قبل وجود دارد.")

            updated_model = self._repo.update(session, service_id, normalized_data)
            return _to_dto(updated_model) if updated_model else None

    def delete_service(self, service_id: int) -> bool:
        with self._services_session() as session:
            return self._repo.delete(session, service_id)

    def delete_multiple_services(self, service_ids: list[int]) -> int:
        with self._services_session() as session:
            return self._repo.delete_multiple(session, service_ids)

    # --- Helpers ---
    def _validate_service_data(self, data: dict[str, Any]) -> None:
        if not data.get('name', '').strip():
            raise ValueError("نام سرویس نمی‌تواند خالی باشد.")
        if data.get('base_price') is None or not isinstance(data.get('base_price'), int):
            raise ValueError("هزینه پایه باید یک عدد معتبر باشد.")
        for fee in data.get('dynamic_prices', []):
            if not fee['name'] or not isinstance(fee['unit_price'], int):
                raise ValueError(f"تعرفه پویا نامعتبر: {fee}")

    def _normalize_service_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Takes a structured dictionary and cleans/converts all its values,
        including the new 'default_page_count' field.
        """
        normalized = {}

        # --- Normalize Parent Fields ---
        normalized['name'] = str(data.get('name', '')).strip()

        try:
            base_price_str = str(data.get('base_price', '0')).strip()
            normalized['base_price'] = int(float(base_price_str)) if base_price_str else ""
        except (ValueError, TypeError):
            raise ValueError(f"مقدار نامعتبر برای هزینه پایه: '{data.get('base_price')}'")

        # --- FIX: Add the default_page_count ---
        try:
            page_count_str = str(data.get('default_page_count', '1')).strip()
            page_count = int(float(page_count_str)) if page_count_str else 1
            # Ensure the page count is at least 1, as per your model's logic.
            normalized['default_page_count'] = page_count if page_count > 0 else 1
        except (ValueError, TypeError):
            raise ValueError(f"مقدار نامعتبر برای تعداد صفحات پیشفرض: '{data.get('default_page_count')}'")

        # --- Normalize Nested Dynamic Prices ---
        normalized['dynamic_prices'] = []
        for fee_data in data.get('dynamic_prices', []):
            try:
                name = str(fee_data.get('name', '')).strip()
                price_str = str(fee_data.get('unit_price', '0')).strip()

                if not name:
                    continue

                normalized['dynamic_prices'].append({
                    'name': name,
                    'unit_price': int(float(price_str))
                })
            except (ValueError, TypeError):
                raise ValueError(f"مقدار نامعتبر برای هزینه متغیر: '{fee_data.get('price')}'")

        return normalized

    def test_database_connection(self):
        with self._services_session() as session:
            self._repo.get_all(session)
            print("Database connection test successful.")

    def bulk_create_services(self, services_data: list[dict[str, Any]]) -> int:
        """
        Bulk create multiple services with their dynamic prices.
        Returns the number of successfully created services.
        """
        if not services_data:
            return 0

        # Normalize and validate each service
        normalized_services = []
        for raw_data in services_data:
            normalized = self._normalize_service_data(raw_data)
            self._validate_service_data(normalized)
            normalized_services.append(normalized)

        with self._services_session() as session:
            # Check for duplicates within the database
            for service in normalized_services:
                if self._repo.exists_by_name(session, service['name']):
                    raise ValueError(
                        f"مدرکی با نام '{service['name']}' از قبل وجود دارد."
                    )

            # Perform the bulk insert
            created_count = self._repo.bulk_create(session, normalized_services)
            return created_count
