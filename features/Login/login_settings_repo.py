# features/Login/login_settings_repo.py

import json
from typing import Optional

from shared.dtos.auth_dtos import RememberSettingsDTO
from shared.utils.path_utils import get_user_data_path


class LoginSettingsRepository:
    """
    Stateless _repository for persisting 'remember me' settings to a JSON file.
    """
    def __init__(self):
        # A config file path is a reasonable thing for a _repository to know.
        self.settings_path = get_user_data_path("config", "login_settings.json")

    def load(self) -> Optional[RememberSettingsDTO]:
        """Loads remember me settings from the JSON file."""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return RememberSettingsDTO(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            print(f"Error loading remember settings file: {e}")
        return None

    def save(self, settings_dto: RememberSettingsDTO) -> None:
        """Saves remember me settings to the JSON file."""
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                import dataclasses
                json.dump(dataclasses.asdict(settings_dto), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving remember settings file: {e}")

    def clear(self) -> None:
        """Deletes the remember me settings file."""
        try:
            if self.settings_path.exists():
                self.settings_path.unlink()
        except Exception as e:
            print(f"Error clearing remember settings file: {e}")
