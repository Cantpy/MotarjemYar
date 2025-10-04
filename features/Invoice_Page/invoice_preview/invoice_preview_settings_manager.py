# features/Invoice_Page/invoice_preview/invoice_preview_settings_manager.py

import copy
import json
from shared.utils.path_utils import get_user_data_path

SETTINGS_FILE_PATH = get_user_data_path("config", "invoice_preview_settings.json")


class PreviewSettingsManager:
    """Handles loading and saving of UI settings for the invoice preview."""
    def __init__(self):
        self._settings = self._load_settings()

    def _get_default_settings(self) -> dict:
        """Provides the hardcoded default settings with granular controls."""
        return {
            "header_visibility": {
                "show_representative": True,
                "show_address": True,
                "show_phone": True,
                "show_email": True,
                "show_telegram": True,
                "show_whatsapp": True,
                "show_website": True,
                "show_issuer": True,
                "show_logo": True
            },
            "customer_visibility": {
                "show_national_id": True,
                "show_phone": True,
                "show_address": True
            },
            "footer_visibility": {
                "show_subtotal": True,
                "show_emergency_cost": True,
                "show_discount": True,
                "show_advance_payment": True,
                "show_remarks": True,
                "show_signature": True,
                "show_page_number": True
            },
            "pagination": {
                'one_page_max_rows': 12,
                'first_page_max_rows': 24,
                'other_page_max_rows': 28,
                'last_page_max_rows': 22
            }
        }

    def _load_settings(self) -> dict:
        """
        Loads settings from the JSON file, intelligently merging them with
        defaults to ensure all keys exist.
        """
        settings = copy.deepcopy(self._get_default_settings())

        if not SETTINGS_FILE_PATH.exists():
            return settings

        try:
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)

            for section, values in user_settings.items():
                if section in settings and isinstance(values, dict):
                    settings[section].update(values)
                else:
                    settings[section] = values

            return settings

        except (json.JSONDecodeError, IOError):
            print("WARNING: Could not read settings file, using defaults.")
            return self._get_default_settings()

    def get_current_settings(self) -> dict:
        return self._settings

    def save_settings(self, new_settings: dict) -> bool:
        try:
            with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=4, ensure_ascii=False)
            self._settings = new_settings
            return True
        except IOError as e:
            print(f"ERROR: Could not save settings file: {e}")
            return False
