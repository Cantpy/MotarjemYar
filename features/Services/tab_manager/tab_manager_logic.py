# features/Services/tab_manager/tab_manager_logic.py

import pandas as pd
from features.Services.tab_manager.tab_manager_models import ImportResult
from features.Services.other_services.other_services_logic import OtherServicesLogic
from features.Services.fixed_prices.fixed_prices_logic import FixedPricesLogic
from features.Services.documents.documents_logic import ServicesLogic


class ExcelImportLogic:
    def __init__(self,
                 services_logic: ServicesLogic,
                 fixed_prices_logic: FixedPricesLogic,
                 other_services_logic: OtherServicesLogic):
        self._services_logic = services_logic
        self._fixed_prices_logic = fixed_prices_logic
        self._other_services_logic = other_services_logic

    def import_from_excel_file(self, file_path: str) -> dict[str, ImportResult]:
        """
        Parses a multi-sheet Excel file and imports all data.
        Returns a dictionary of ImportResult objects, one for each sheet.
        """
        results = {}
        try:
            xls = pd.ExcelFile(file_path)

            # Process each sheet if it exists
            if 'Documents' in xls.sheet_names:
                df = pd.read_excel(xls, 'Documents')
                results['documents'] = self._import_documents_sheet(df)

            if 'Fixed Prices' in xls.sheet_names:
                df = pd.read_excel(xls, 'Fixed Prices')
                results['fixed_prices'] = self._import_fixed_prices_sheet(df)

            if 'Other Services' in xls.sheet_names:
                df = pd.read_excel(xls, 'Other Services')
                results['other_services'] = self._import_other_services_sheet(df)

            return results
        except Exception as e:
            raise ValueError(f"Could not read or process the Excel file: {e}")

    def _import_documents_sheet(self, df: pd.DataFrame) -> ImportResult:
        """
        Parses the 'Documents' sheet and bulk imports services with dynamic fees.
        """
        result = ImportResult(source="Excel (Documents Sheet)")
        services_to_create = []

        for _, row in df.iterrows():
            try:
                # --- Handle base price safely ---
                base_price_val = row.get('Base Price')
                base_price = int(base_price_val) if pd.notna(base_price_val) else 0

                service_data = {
                    'name': str(row.get('Name', '')).strip(),
                    'base_price': base_price,
                    'dynamic_fees': []
                }

                # --- Parse dynamic fees ---
                i = 1
                while f'Fee {i} Name' in row and f'Fee {i} Price' in row:
                    fee_name_val = row[f'Fee {i} Name']
                    fee_price_val = row[f'Fee {i} Price']

                    if pd.notna(fee_name_val) and pd.notna(fee_price_val):
                        fee_name = str(fee_name_val).strip()
                        try:
                            unit_price = int(fee_price_val)
                        except Exception:
                            unit_price = 0  # fallback instead of crashing

                        if fee_name:  # only add if non-empty after strip
                            service_data['dynamic_fees'].append({
                                'name': fee_name,
                                'price': unit_price
                            })
                    i += 1

                services_to_create.append(service_data)
                result.added_services_names.append(service_data['name'])
                result.success_count += 1

            except Exception as e:
                result.failed_count += 1
                result.errors.append(f"Error on row for '{row.get('Name', 'N/A')}': {e}")

        if services_to_create:
            self._services_logic.bulk_create_services(services_to_create)

        return result

    def _import_fixed_prices_sheet(self, df: pd.DataFrame) -> ImportResult:
        """
        Parses the 'Fixed Prices' sheet, validates data, and prepares it
        for bulk insertion into the fixed_prices table.
        """
        result = ImportResult(source="Excel (Fixed Prices Sheet)")
        prices_to_create = []

        # Normalize column names for robustness
        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]

        # Check for required columns
        required_cols = {'name', 'price'}
        if not required_cols.issubset(df.columns):
            result.errors.append(f"Sheet 'Fixed Prices' must have 'name' and 'price' columns.")
            result.failed_count = len(df)
            return result

        for index, row in df.iterrows():
            try:
                name = str(row.get('name', '')).strip()
                price_str = str(row.get('price', '')).strip()

                # --- Validation ---
                if not name:
                    raise ValueError("The 'name' field cannot be empty.")
                if not price_str:
                    raise ValueError("The 'price' field cannot be empty.")

                price = int(price_str)

                is_default_raw = str(row.get('is_default', 'false')).strip().lower()
                is_default = is_default_raw in ['true', '1', 'yes', 't']

                # Add the clean, validated data to our list
                prices_to_create.append({
                    'name': name,
                    'price': price,
                    'is_default': is_default,
                })
                result.added_services_names.append(name)

            except (ValueError, TypeError, KeyError) as e:
                result.failed_count += 1
                result.errors.append(f"Error in 'Fixed Prices' sheet on row {index + 2}: {e}")

        # --- Bulk Database Insertion ---
        if prices_to_create:
            try:
                self._fixed_prices_logic.bulk_create_fixed_prices(prices_to_create)
                result.success_count = len(prices_to_create)
            except Exception as e:
                # If the entire bulk insert fails
                result.failed_count += len(prices_to_create)
                result.success_count = 0
                result.added_services_names = []
                result.errors.append(f"Database error during bulk insert for Fixed Prices: {e}")

        return result

    def _import_other_services_sheet(self, df: pd.DataFrame) -> ImportResult:
        """
        Parses the 'Other Services' sheet, validates data, and prepares it
        for bulk insertion into the other_services table.
        """
        result = ImportResult(source="Excel (Other Services Sheet)")
        services_to_create = []

        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]

        required_cols = {'name', 'price'}
        if not required_cols.issubset(df.columns):
            result.errors.append(f"Sheet 'Other Services' must have 'name' and 'price' columns.")
            result.failed_count = len(df)
            return result

        for index, row in df.iterrows():
            try:
                name = str(row.get('name', '')).strip()
                price_str = str(row.get('price', '')).strip()

                # --- Validation ---
                if not name:
                    raise ValueError("The 'name' field cannot be empty.")
                if not price_str:
                    raise ValueError("The 'price' field cannot be empty.")

                price = int(price_str)

                # Add the clean, validated data to our list
                services_to_create.append({
                    'name': name,
                    'price': price
                })
                result.added_services_names.append(name)

            except (ValueError, TypeError, KeyError) as e:
                result.failed_count += 1
                result.errors.append(f"Error in 'Other Services' sheet on row {index + 2}: {e}")

        # --- Bulk Database Insertion ---
        if services_to_create:
            try:
                self._other_services_logic.bulk_create_services(services_to_create)
                result.success_count = len(services_to_create)
            except Exception as e:
                # If the entire bulk insert fails
                result.failed_count += len(services_to_create)
                result.success_count = 0
                result.added_services_names = []
                result.errors.append(f"Database error during bulk insert for Other Services: {e}")

        return result
