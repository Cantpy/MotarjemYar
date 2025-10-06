# features/Services/tab_manager/tab_manager_logic.py

import pandas as pd
from features.Services.tab_manager.tab_manager_models import ImportResult
from features.Services.other_services.other_services_logic import OtherServicesLogic
from features.Services.documents.documents_logic import ServicesLogic


class ExcelImportLogic:
    def __init__(self,
                 services_logic: ServicesLogic,
                 other_services_logic: OtherServicesLogic):
        self._services_logic = services_logic
        self._other_services_logic = other_services_logic

        self._sheet_handlers = {
            'Documents': self._import_documents_sheet,
            'Other Services': self._import_other_services_sheet,
        }

    def import_from_excel_file(self, file_path: str) -> dict[str, ImportResult]:
        """
        Parses a multi-sheet Excel file and imports data using registered handlers.
        Returns a dictionary of ImportResult objects, one for each processed sheet.
        """
        results = {}
        try:
            xls = pd.ExcelFile(file_path)

            for sheet_name, handler_method in self._sheet_handlers.items():
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name)
                    result_key = sheet_name.lower().replace(' ', '_')
                    results[result_key] = handler_method(df)

            return results
        except FileNotFoundError:
            raise ValueError(f"The file at path '{file_path}' was not found.")
        except Exception as e:
            raise ValueError(f"Could not read or process the Excel file: {e}")

    def _safe_to_int(self, value: any, default: int) -> int:
        """Safely converts a value to an integer, returning a default on failure."""
        if pd.isna(value):
            return default
        try:
            return int(float(value)) # Convert to float first to handle "10.0"
        except (ValueError, TypeError):
            return default

    def _import_documents_sheet(self, df: pd.DataFrame) -> ImportResult:
        """
        Parses the 'Documents' sheet, including aliases for services and their dynamic fees.
        """
        result = ImportResult(source="Excel (Documents Sheet)")
        services_to_create = []

        for index, row in df.iterrows():
            row_num = index + 2
            try:
                name = str(row.get('Name', '')).strip()
                if not name:
                    # Skip rows that don't have a primary service name
                    continue

                service_data = {
                    'name': name,
                    'base_price': self._safe_to_int(row.get('Base Price'), default=0),
                    'default_page_count': self._safe_to_int(row.get('Default Page Count'), default=1),
                    'aliases': [],
                    'dynamic_prices': []
                }

                # --- 1. Parse main service aliases ---
                j = 1
                while f'Alias {j}' in row:
                    alias_val = row.get(f'Alias {j}')
                    alias = '' if pd.isna(alias_val) else str(alias_val).strip()
                    if alias:
                        service_data['aliases'].append({'alias': alias})
                    j += 1

                # --- 2. Parse dynamic fees and their aliases ---
                i = 1
                while f'Fee {i} Name' in row:
                    fee_name_val = row.get(f'Fee {i} Name')
                    fee_name = '' if pd.isna(fee_name_val) else str(fee_name_val).strip()

                    # If the fee name is empty, we stop processing fees for this row
                    if not fee_name:
                        break

                    fee_data = {
                        'name': fee_name,
                        'price': self._safe_to_int(row.get(f'Fee {i} Price'), default=0),
                        'aliases': []
                    }

                    # --- 3. Parse aliases for THIS specific fee ---
                    k = 1
                    while f'Fee {i} Alias {k}' in row:
                        alias_val = row.get(f'Fee {i} Alias {k}')
                        alias = '' if pd.isna(alias_val) else str(alias_val).strip()
                        if alias:
                            fee_data['aliases'].append({'alias': alias})
                        k += 1

                    service_data['dynamic_prices'].append(fee_data)
                    i += 1

                services_to_create.append(service_data)
                result.added_services_names.append(name)

            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"Unexpected error on row {row_num} for '{row.get('Name', 'N/A')}': {e}")

        if services_to_create:
            try:
                self._services_logic.bulk_create_services(services_to_create)
                result.success_count = len(services_to_create)
            except Exception as e:
                # Handle bulk create failure
                result.failed_count += len(services_to_create)
                result.success_count = 0
                result.added_services_names = []
                result.errors.append(f"Database bulk insert failed for 'Documents': {e}")

        return result

    def _import_other_services_sheet(self, df: pd.DataFrame) -> ImportResult:
        """
        Parses the 'Other Services' sheet, validates, and prepares for bulk insertion.
        """
        result = ImportResult(source="Excel (Other Services Sheet)")
        services_to_create = []
        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]

        required_cols = {'name', 'price'}
        if not required_cols.issubset(df.columns):
            result.errors.append("Sheet 'Other Services' must have 'name' and 'price' columns.")
            result.failed_count = len(df)
            return result

        for index, row in df.iterrows():
            row_num = index + 2 # For user-friendly error messages
            try:
                name = str(row.get('name', '')).strip()
                price_val = row.get('price')

                if not name:
                    raise ValueError("'name' field cannot be empty.")
                if pd.isna(price_val) or str(price_val).strip() == '':
                    raise ValueError("'price' field cannot be empty.")

                price = int(float(price_val))

                services_to_create.append({'name': name, 'price': price})
                result.added_services_names.append(name)

            except (ValueError, TypeError) as e:
                result.failed_count += 1
                result.errors.append(f"Validation error in 'Other Services' on row {row_num}: {e}")

        # --- Bulk Database Insertion ---
        if services_to_create:
            try:
                self._other_services_logic.bulk_create_services(services_to_create)
                result.success_count = len(services_to_create)
            except Exception as e:
                result.failed_count += len(services_to_create)
                result.success_count = 0
                result.added_services_names = []
                result.errors.append(f"Database bulk insert failed for 'Other Services': {e}")

        return result
