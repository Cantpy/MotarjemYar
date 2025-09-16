# features/Services/documents/documents_logic.py

import os
from sqlalchemy import create_engine, text
import pandas as pd
from typing import Any
from features.Services.documents.documents_repo import ServiceRepository
from features.Services.documents.documents_models import ServicesDTO, ImportResult
from shared.session_provider import SessionProvider


class ServicesLogic:
    """Business _logic for services management"""

    def __init__(self, repo: ServiceRepository, session_provider: SessionProvider):
        self._repo = repo
        self._session_provider = session_provider

    def get_all_services(self) -> list[ServicesDTO]:
        """Get all services as dictionaries"""
        with self._session_provider.services() as session:
            services = self._repo.get_all(session)
            return services

    def create_service(self, service_data: dict[str, Any]) -> ServicesDTO:
        """Create new service with validation"""
        self._validate_service_data(service_data)

        with self._session_provider.services() as session:
            # Check for duplicates
            if self._repo.exists_by_name(session, service_data['name']):
                raise Exception(f"ServicesModel with name '{service_data['name']}' already exists")

            # Convert string prices to integers
            service_data = self._normalize_service_data(service_data)

            service = self._repo.create(session, service_data)
            return service

    def update_service(self, service_id: int, service_data: dict[str, Any]) -> ServicesDTO | None:
        """Update existing service with validation"""
        self._validate_service_data(service_data)

        with self._session_provider.services() as session:

            # Check for duplicates (excluding current service)
            if self._repo.exists_by_name(session, service_data['name'], exclude_id=service_id):
                raise Exception(f"ServicesModel with name '{service_data['name']}' already exists")

            # Convert string prices to integers
            service_data = self._normalize_service_data(service_data)

            service = self._repo.update(session, service_id, service_data)
            return service if service else None

    def delete_service(self, service_id: int) -> bool:
        """Delete service by ID"""
        with self._session_provider.services() as session:
            return self._repo.delete(session, service_id)

    def delete_multiple_services(self, service_ids: list[int]) -> int:
        """Delete multiple services"""
        with self._session_provider.services() as session:
            return self._repo.delete_multiple(session, service_ids)

    def search_services(self, search_term: str) -> list[ServicesDTO]:
        """Search services by name"""
        with self._session_provider.services() as session:
            services = self._repo.search(session, search_term)
            return services

    def import_from_excel(self, file_path: str) -> ImportResult:
        """
        Reads an Excel file, validates the data, and bulk-inserts it.
        Returns a detailed summary of the operation.
        """
        result = ImportResult(source="فایل اکسل")
        try:
            df = pd.read_excel(file_path)
            # Normalize column names (lowercase, strip spaces)
            df.columns = [str(c).lower().strip() for c in df.columns]
        except Exception as e:
            result.errors.append(f"فایل اکسل قابل خواندن نیست: {e}")
            result.failed_count = 1
            return result

        required_cols = {'name', 'base_price'}
        if not required_cols.issubset(df.columns):
            result.errors.append(f"فایل اکسل باید حداقل شامل ستون‌های 'name' و 'base_price' باشد.")
            result.failed_count = 1
            return result

        services_to_create = []
        for index, row in df.iterrows():
            try:
                # Basic validation
                if pd.isna(row['name']) or str(row['name']).strip() == '' or pd.isna(row['base_price']):
                    raise ValueError("ستون‌های 'name' و 'base_price' اجباری هستند.")

                service_data = {
                    'name': str(row['name']).strip(),
                    'base_price': int(row['base_price']),
                    'dynamic_price_name_1': str(row.get('dynamic_price_name_1', '')) or None,
                    'dynamic_price_1': int(row.get('dynamic_price_1', 0) or 0),
                    'dynamic_price_name_2': str(row.get('dynamic_price_name_2', '')) or None,
                    'dynamic_price_2': int(row.get('dynamic_price_2', 0) or 0)
                }
                services_to_create.append(service_data)
                result.added_services_names.append(service_data['name'])

            except (ValueError, TypeError) as e:
                result.failed_count += 1
                result.errors.append(f"خطا در ردیف {index + 2}: {e}")

        if services_to_create:
            with self._session_provider.services() as session:
                # Optional: Delete existing data before import
                # self._repo.delete_all(session)

                self._repo.bulk_create(session, services_to_create)
                result.success_count = len(services_to_create)

        return result

    def import_from_database(self, connection_string: str) -> ImportResult:
        """
        Connects to another database, reads services, and imports them.
        Returns a detailed summary.
        """
        result = ImportResult(source="پایگاه داده")
        # This is a placeholder implementation. The actual query would depend
        # on the source database schema.

        # For this example, we assume the source table has the exact same schema.
        query = "SELECT name, base_price, dynamic_price_name_1, dynamic_price_1, dynamic_price_name_2, dynamic_price_2 FROM services"

        try:
            source_engine = create_engine(connection_string)
            with source_engine.connect() as connection:
                rows = connection.execute(text(query)).mappings().all()
        except Exception as e:
            result.errors.append(f"امکان اتصال به پایگاه داده منبع وجود ندارد: {e}")
            result.failed_count = 1
            return result

        services_to_create = [dict(row) for row in rows]

        if services_to_create:
            with self._session_provider.services() as session:
                self._repo.bulk_create(session, services_to_create)
                result.success_count = len(services_to_create)
                result.added_services_names = [s['name'] for s in services_to_create]

        return result

    def _validate_service_data(self, data: ServicesDTO) -> None:
        """Validate service data"""
        if not data.name:
            raise Exception("ServicesModel name is required")

        base_price = data.base_price
        if not isinstance(base_price, (int, str)) or (isinstance(base_price, str) and not base_price.strip()):
            raise Exception("Base price is required")

    def _normalize_service_data(self, data: dict[str, Any]) -> ServicesDTO:
        """Normalize service data types"""
        normalized = data.copy()

        # Convert price fields to integers
        for field in ['base_price', 'dynamic_price_1', 'dynamic_price_2']:
            value = normalized.get(field, 0)
            if isinstance(value, str):
                try:
                    normalized[field] = int(value) if value.strip() else 0
                except ValueError:
                    raise Exception(f"Invalid price value: {value}")
            else:
                normalized[field] = int(value) if value else 0

        return normalized
