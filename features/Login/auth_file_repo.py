# features/Login/auth_file_repo.py

import json
import dataclasses
from typing import Optional
from pathlib import Path

from shared.dtos.auth_dtos import RememberSettingsDTO, SessionDataDTO
from shared.utils.path_utils import get_user_data_path


class AuthFileRepository:
    """
    A single, stateless repository for persisting all authentication-related
    JSON files, such as 'remember me' settings and the current session data.
    """
    def __init__(self):

        self.remember_me_file = get_user_data_path("config", "remember_me.json")
        self.session_file = get_user_data_path("config", "current_session.json")

    # --- Methods for 'Remember Me' Settings ---

    def load_remember_me(self) -> Optional[RememberSettingsDTO]:
        """Loads 'remember me' settings from its JSON file."""
        return self._load_json(self.remember_me_file, RememberSettingsDTO)

    def save_remember_me(self, settings_dto: RememberSettingsDTO) -> None:
        """Saves 'remember me' settings to its JSON file."""
        self._save_json(self.remember_me_file, settings_dto)

    def clear_remember_me(self) -> None:
        """Deletes the 'remember me' settings file."""
        self._clear_file(self.remember_me_file)

    # --- Methods for Current Session Data ---

    def load_session(self) -> Optional[SessionDataDTO]:
        """Loads the current session data from its JSON file."""
        return self._load_json(self.session_file, SessionDataDTO)

    def save_session(self, session_dto: SessionDataDTO) -> None:
        """Saves the current session data to its JSON file."""
        self._save_json(self.session_file, session_dto)

    def clear_session(self) -> None:
        """Deletes the current session file."""
        self._clear_file(self.session_file)

    # --- Private, Generic Helper Methods (DRY Principle) ---

    def _load_json(self, file_path: Path, dto_class: type):
        """Generic helper to load a JSON file into a DTO."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return dto_class(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            print(f"Error loading JSON file '{file_path}': {e}")
        return None

    def _save_json(self, file_path: Path, dto_instance) -> None:
        """Generic helper to save a DTO to a JSON file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dataclasses.asdict(dto_instance), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving JSON file '{file_path}': {e}")

    def _clear_file(self, file_path: Path) -> None:
        """Generic helper to delete a file."""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Error clearing file '{file_path}': {e}")
