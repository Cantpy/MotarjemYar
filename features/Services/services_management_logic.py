"""services_management_logic.py - Business logic layer for services management"""

import pandas as pd
import os
from typing import List, Dict, Any, Optional, Tuple
from services_management_repo import ServiceRepository, FixedPriceRepository, OtherServiceRepository
from services_management_models import DatabaseManager


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ServicesLogic:
    """Business logic for services management"""

    def __init__(self, db_path: str, excel_path: str = None):
        self.db_manager = DatabaseManager(db_path)
        self.service_repo = ServiceRepository(self.db_manager)
        self.excel_path = excel_path

    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all services as dictionaries"""
        services = self.service_repo.get_all()
        return [service.to_dict() for service in services]

    def create_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new service with validation"""
        self._validate_service_data(service_data)

        # Check for duplicates
        if self.service_repo.exists_by_name(service_data['name']):
            raise ValidationError(f"ServicesModel with name '{service_data['name']}' already exists")

        # Convert string prices to integers
        service_data = self._normalize_service_data(service_data)

        service = self.service_repo.create(service_data)
        return service.to_dict()

    def update_service(self, service_id: int, service_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing service with validation"""
        self._validate_service_data(service_data)

        # Check for duplicates (excluding current service)
        if self.service_repo.exists_by_name(service_data['name'], exclude_id=service_id):
            raise ValidationError(f"ServicesModel with name '{service_data['name']}' already exists")

        # Convert string prices to integers
        service_data = self._normalize_service_data(service_data)

        service = self.service_repo.update(service_id, service_data)
        return service.to_dict() if service else None

    def delete_service(self, service_id: int) -> bool:
        """Delete service by ID"""
        return self.service_repo.delete(service_id)

    def delete_multiple_services(self, service_ids: List[int]) -> int:
        """Delete multiple services"""
        return self.service_repo.delete_multiple(service_ids)

    def search_services(self, search_term: str) -> List[Dict[str, Any]]:
        """Search services by name"""
        services = self.service_repo.search(search_term)
        return [service.to_dict() for service in services]

    def import_from_excel(self) -> Tuple[int, List[str]]:
        """Import services from Excel file"""
        if not self.excel_path or not os.path.exists(self.excel_path):
            raise ValidationError(f"Excel file not found: {self.excel_path}")

        # Clear existing services
        self.service_repo.delete_all()

        # Read Excel file
        df = pd.read_excel(self.excel_path, sheet_name='Sheet1')

        expected_columns = ['name', 'base_price', 'dynamic_price_name_1', 'dynamic_price_1',
                            'dynamic_price_name_2', 'dynamic_price_2']

        if len(df.columns) < 6:
            raise ValidationError("Excel file must have at least 6 columns")

        # Rename columns
        df = df.iloc[:, :6].copy()
        df.columns = expected_columns

        # Clean data
        df = df.dropna(subset=['name'])

        # Convert prices to integers
        for col in ['base_price', 'dynamic_price_1', 'dynamic_price_2']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Nullify dynamic price names if price is 0
        df.loc[df['dynamic_price_1'] == 0, 'dynamic_price_name_1'] = None
        df.loc[df['dynamic_price_2'] == 0, 'dynamic_price_name_2'] = None

        # Remove duplicates
        df_unique = df.drop_duplicates(subset=['name'], keep='first')

        imported_count = 0
        errors = []

        for _, row in df_unique.iterrows():
            try:
                service_data = {
                    'name': str(row['name']),
                    'base_price': int(row['base_price']),
                    'dynamic_price_name_1': row['dynamic_price_name_1'],
                    'dynamic_price_1': int(row['dynamic_price_1']),
                    'dynamic_price_name_2': row['dynamic_price_name_2'],
                    'dynamic_price_2': int(row['dynamic_price_2'])
                }

                self.service_repo.create(service_data)
                imported_count += 1

            except Exception as e:
                errors.append(f"Error importing '{row['name']}': {str(e)}")

        return imported_count, errors

    def _validate_service_data(self, data: Dict[str, Any]) -> None:
        """Validate service data"""
        if not data.get('name', '').strip():
            raise ValidationError("ServicesModel name is required")

        base_price = data.get('base_price', 0)
        if not isinstance(base_price, (int, str)) or (isinstance(base_price, str) and not base_price.strip()):
            raise ValidationError("Base price is required")

    def _normalize_service_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize service data types"""
        normalized = data.copy()

        # Convert price fields to integers
        for field in ['base_price', 'dynamic_price_1', 'dynamic_price_2']:
            value = normalized.get(field, 0)
            if isinstance(value, str):
                try:
                    normalized[field] = int(value) if value.strip() else 0
                except ValueError:
                    raise ValidationError(f"Invalid price value: {value}")
            else:
                normalized[field] = int(value) if value else 0

        return normalized


class FixedPricesLogic:
    """Business logic for fixed prices management"""

    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.fixed_price_repo = FixedPriceRepository(self.db_manager)

    def get_all_fixed_prices(self) -> List[Dict[str, Any]]:
        """Get all fixed prices as dictionaries"""
        fixed_prices = self.fixed_price_repo.get_all()
        return [price.to_dict() for price in fixed_prices]

    def create_fixed_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new fixed price with validation"""
        self._validate_fixed_price_data(price_data)

        # Check for duplicates
        if self.fixed_price_repo.exists_by_name(price_data['name']):
            raise ValidationError(f"Fixed price with name '{price_data['name']}' already exists")

        # Convert string price to integer
        price_data = self._normalize_fixed_price_data(price_data)

        fixed_price = self.fixed_price_repo.create(price_data)
        return fixed_price.to_dict()

    def update_fixed_price(self, price_id: int, price_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing fixed price with validation"""
        self._validate_fixed_price_data(price_data)

        # Check for duplicates (excluding current price)
        if self.fixed_price_repo.exists_by_name(price_data['name'], exclude_id=price_id):
            raise ValidationError(f"Fixed price with name '{price_data['name']}' already exists")

        # Convert string price to integer
        price_data = self._normalize_fixed_price_data(price_data)

        fixed_price = self.fixed_price_repo.update(price_id, price_data)
        return fixed_price.to_dict() if fixed_price else None

    def delete_fixed_price(self, price_id: int) -> bool:
        """Delete fixed price by ID (only non-default)"""
        return self.fixed_price_repo.delete(price_id)

    def delete_multiple_fixed_prices(self, price_ids: List[int]) -> int:
        """Delete multiple fixed prices (only non-default)"""
        return self.fixed_price_repo.delete_multiple(price_ids)

    def search_fixed_prices(self, search_term: str) -> List[Dict[str, Any]]:
        """Search fixed prices by name"""
        fixed_prices = self.fixed_price_repo.search(search_term)
        return [price.to_dict() for price in fixed_prices]

    def _validate_fixed_price_data(self, data: Dict[str, Any]) -> None:
        """Validate fixed price data"""
        if not data.get('name', '').strip():
            raise ValidationError("Fixed price name is required")

        price = data.get('price', 0)
        if not isinstance(price, (int, str)) or (isinstance(price, str) and not price.strip()):
            raise ValidationError("Price is required")

    def _normalize_fixed_price_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize fixed price data types"""
        normalized = data.copy()

        # Convert price to integer
        price = normalized.get('price', 0)
        if isinstance(price, str):
            try:
                normalized['price'] = int(price) if price.strip() else 0
            except ValueError:
                raise ValidationError(f"Invalid price value: {price}")
        else:
            normalized['price'] = int(price) if price else 0

        return normalized


class OtherServicesLogic:
    """Business logic for other services management"""

    def __init__(self, db_path: str):
        self.db_manager = DatabaseManager(db_path)
        self.other_service_repo = OtherServiceRepository(self.db_manager)

    def get_all_other_services(self) -> List[Dict[str, Any]]:
        """Get all other services as dictionaries"""
        other_services = self.other_service_repo.get_all()
        return [service.to_dict() for service in other_services]

    def create_other_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new other service with validation"""
        self._validate_other_service_data(service_data)

        # Check for duplicates
        if self.other_service_repo.exists_by_name(service_data['name']):
            raise ValidationError(f"Other service with name '{service_data['name']}' already exists")

        # Convert string price to integer
        service_data = self._normalize_other_service_data(service_data)

        other_service = self.other_service_repo.create(service_data)
        return other_service.to_dict()

    def update_other_service(self, service_id: int, service_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing other service with validation"""
        self._validate_other_service_data(service_data)

        # Check for duplicates (excluding current service)
        if self.other_service_repo.exists_by_name(service_data['name'], exclude_id=service_id):
            raise ValidationError(f"Other service with name '{service_data['name']}' already exists")

        # Convert string price to integer
        service_data = self._normalize_other_service_data(service_data)

        other_service = self.other_service_repo.update(service_id, service_data)
        return other_service.to_dict() if other_service else None

    def delete_other_service(self, service_id: int) -> bool:
        """Delete other service by ID (only non-default)"""
        return self.other_service_repo.delete(service_id)

    def delete_multiple_other_services(self, service_ids: List[int]) -> int:
        """Delete multiple other services (only non-default)"""
        return self.other_service_repo.delete_multiple(service_ids)

    def search_other_services(self, search_term: str) -> List[Dict[str, Any]]:
        """Search other services by name"""
        other_services = self.other_service_repo.search(search_term)
        return [service.to_dict() for service in other_services]

    def _validate_other_service_data(self, data: Dict[str, Any]) -> None:
        """Validate other service data"""
        if not data.get('name', '').strip():
            raise ValidationError("Other service name is required")

        price = data.get('price', 0)
        if not isinstance(price, (int, str)) or (isinstance(price, str) and not price.strip()):
            raise ValidationError("Price is required")

    def _normalize_other_service_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize other service data types"""
        normalized = data.copy()

        # Convert price to integer
        price = normalized.get('price', 0)
        if isinstance(price, str):
            try:
                normalized['price'] = int(price) if price.strip() else 0
            except ValueError:
                raise ValidationError(f"Invalid price value: {price}")
        else:
            normalized['price'] = int(price) if price else 0

        return normalized
