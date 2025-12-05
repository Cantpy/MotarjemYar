# features/Services/documents/documents_logic.py

from typing import Any
from dataclasses import asdict

from features.Services.documents.documents_repo import ServiceRepository
from features.Services.documents.documents_models import (ServicesDTO, ServiceDynamicFeeDTO, NormalizedServiceDTO,
                                                          NormalizedDynamicPriceDTO)
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

    def __init__(self, repo: ServiceRepository, business_engine: ManagedSessionProvider):
        self._repo = repo
        self._business_engine = business_engine
        self.test_database_connection()

    def get_all_services(self) -> list[ServicesDTO]:
        with self._business_engine() as session:
            service_models = self._repo.get_all(session)
            return [_to_dto(model) for model in service_models]

    def get_service_with_aliases(self, service_id: int) -> ServicesDTO | None:
        """Fetches a single service with all its related aliases."""
        with self._business_engine() as session:
            service_model = self._repo.get_by_id_with_aliases(session, service_id)
            return _to_dto(service_model) if service_model else None

    def update_aliases(self, service_id: int, aliases_data: dict) -> bool:
        """Updates the aliases for a service and its dynamic prices."""
        with self._business_engine() as session:
            return self._repo.update_aliases(session, service_id, aliases_data)

    def update_service_properties(self, service_id: int, properties_data: dict) -> ServicesDTO | None:
        """Updates the properties for a service (aliases, page count, etc.)."""
        with self._business_engine() as session:
            updated_model = self._repo.update_service_properties(session, service_id, properties_data)
            return _to_dto(updated_model) if updated_model else None

    def create_service(self, service_data: dict[str, Any]) -> ServicesDTO:
        """Create a new service. The input dict is now correctly structured."""
        # 1. Normalize (Returns a nice DTO now)
        normalized_dto = self._normalize_service_data(service_data)

        # Debugging is now easy:
        print(f"Creating Service Normalized Data: {normalized_dto}")

        # 2. Validate
        self._validate_service_data(normalized_dto)

        with self._business_engine() as session:
            if self._repo.exists_by_name(session, normalized_dto.name):
                raise ValueError(f"مدرکی با نام '{normalized_dto.name}' از قبل وجود دارد.")

            # 3. Convert DTO back to dict for the Repo (or update Repo to accept DTOs)
            new_model = self._repo.create_service_with_prices(session, normalized_dto.to_dict())
            return _to_dto(new_model)

    def update_service(self, service_id: int, service_data: dict[str, Any]) -> ServicesDTO | None:
        """"""
        normalized_dto = self._normalize_service_data(service_data)
        self._validate_service_data(normalized_dto)

        with self._business_engine() as session:
            if self._repo.exists_by_name(session, normalized_dto.name, exclude_id=service_id):
                raise ValueError(f"مدرکی با نام '{normalized_dto.name}' از قبل وجود دارد.")

            updated_model = self._repo.update(session, service_id, normalized_dto.to_dict())
            return _to_dto(updated_model) if updated_model else None

    def delete_service(self, service_id: int) -> bool:
        with self._business_engine() as session:
            return self._repo.delete(session, service_id)

    def delete_multiple_services(self, service_ids: list[int]) -> int:
        with self._business_engine() as session:
            return self._repo.delete_multiple(session, service_ids)

    def bulk_create_services(self, services_data: list[dict[str, Any]]) -> int:
        if not services_data:
            return 0

        # Normalize to List[NormalizedServiceDTO]
        normalized_dtos = []
        for raw_data in services_data:
            dto = self._normalize_service_data(raw_data)
            self._validate_service_data(dto)
            normalized_dtos.append(dto)

        with self._business_engine() as session:
            # Check duplicates
            for dto in normalized_dtos:
                if self._repo.exists_by_name(session, dto.name):
                    raise ValueError(f"مدرکی با نام '{dto.name}' از قبل وجود دارد.")

            # Convert to dicts for bulk_create
            dicts_data = [dto.to_dict() for dto in normalized_dtos]
            created_count = self._repo.bulk_create(session, dicts_data)
            return created_count

    # --- Helpers ---
    def _validate_service_data(self, data: NormalizedServiceDTO) -> None:
        """Now validates the DTO object instead of a dict."""
        if not data.name:
            raise ValueError("نام سرویس نمی‌تواند خالی باشد.")

        # Ensure it's not negative (optional check)
        if data.base_price < 0:
            raise ValueError("هزینه پایه نمیتواند منفی باشد.")

        for fee in data.dynamic_prices:
            if not fee.name:
                raise ValueError(f"نام تعرفه پویا نامعتبر است: {fee}")

    def _normalize_service_data(self, data: dict[str, Any]) -> NormalizedServiceDTO:
        """
        Converts raw dictionary input into a strictly typed NormalizedServiceDTO.
        Safely handles string numbers with commas.
        """

        def safe_int(val: Any) -> int:
            """Safely converts strings with commas to int."""
            if val is None:
                return 0
            if isinstance(val, int):
                return val
            if isinstance(val, float):
                return int(val)
            if isinstance(val, str):
                clean = val.replace(',', '').strip()
                return int(clean) if clean else 0
            return 0

        # 1. Base Price (Strictly look for base_price)
        # Note: We do NOT fallback to 'base_cost' anymore as requested.
        base_price_val = safe_int(data.get('base_price'))

        # 2. Dynamic Prices
        normalized_fees = []
        for fee_data in data.get('dynamic_prices', []):
            f_name = str(fee_data.get('name', '')).strip()
            if not f_name:
                continue

            # Handle price/unit_price ambiguity if needed, or strictly use 'price'
            # Assuming 'price' comes from UI dialog, 'unit_price' might come from DB models
            raw_price = fee_data.get('price')
            if raw_price is None:
                raw_price = fee_data.get('unit_price')

            f_aliases = []
            for alias_d in fee_data.get('aliases', []):
                a_str = str(alias_d.get('alias', '')).strip()
                if a_str:
                    f_aliases.append({'alias': a_str})

            normalized_fees.append(NormalizedDynamicPriceDTO(
                name=f_name,
                unit_price=safe_int(raw_price),
                aliases=f_aliases
            ))

        # 3. Service Aliases
        s_aliases = []
        for alias_d in data.get('aliases', []):
            a_str = str(alias_d.get('alias', '')).strip()
            if a_str:
                s_aliases.append({'alias': a_str})

        print(f'Normalized Service data : name={data.get("name")}, base_price={base_price_val}, ')

        # 4. Construct DTO
        return NormalizedServiceDTO(
            name=str(data.get('name', '')).strip(),
            base_price=base_price_val,
            default_page_count=safe_int(data.get('default_page_count') or 1),
            aliases=s_aliases,
            dynamic_prices=normalized_fees
        )

    def test_database_connection(self):
        with self._business_engine() as session:
            self._repo.get_all(session)
            print("Database connection test successful.")
