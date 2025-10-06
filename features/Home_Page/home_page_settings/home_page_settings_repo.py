# features/home_page/settings/_repository.py

import json
import logging
from typing import Optional
from pathlib import Path
from features.Home_Page.home_page_settings.home_page_settings_models import Settings, StatCardConfig

from shared.utils.path_utils import get_user_data_path

logger = logging.getLogger(__name__)


class HomepageSettingsRepository:
    """
    Stateless _repository for persisting homepage settings to a JSON file.
    """
    SETTINGS_FILE = get_user_data_path("config", "homepage_settings.json")
    BACKUP_FILE = get_user_data_path("config", "homepage_settings_backup.json")

    def load(self) -> Optional[Settings]:
        """Loads settings from file, with fallback to backup."""
        # This method is already excellent. No changes needed.
        self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        settings = self._load_from_file(self.SETTINGS_FILE)
        if settings:
            return settings

        logger.warning("Main settings file failed, trying backup.")
        settings = self._load_from_file(self.BACKUP_FILE)
        if settings:
            self._copy_file(self.BACKUP_FILE, self.SETTINGS_FILE)
        return settings

    def save(self, settings: Settings) -> bool:
        """Saves settings to file with backup."""
        try:
            if self.SETTINGS_FILE.exists():
                self._copy_file(self.SETTINGS_FILE, self.BACKUP_FILE)

            # REFINED: Create the dictionary from the DTO
            data = {
                'row_count': settings.row_count,
                'threshold_days': settings.threshold_days,
                'orange_threshold_days': settings.orange_threshold_days,
                'red_threshold_days': settings.red_threshold_days,
                'stat_cards': [card.__dict__ for card in settings.stat_cards]
            }

            temp_file = self.SETTINGS_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.SETTINGS_FILE)
            logger.info("Settings saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def _load_from_file(self, file_path: Path) -> Optional[Settings]:
        """Loads and deserializes settings from a specific file."""
        try:
            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # REFINED: Removed 'total_cards_number' from required fields
            required_fields = ['row_count', 'threshold_days', 'orange_threshold_days',
                               'red_threshold_days', 'stat_cards']

            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in {file_path}")
                return None

            # REFINED: Explicitly deserialize the list of dicts into StatCardConfig objects
            card_configs = []
            for card_data in data.get('stat_cards', []):
                # We can add a validation step here for each card if we want
                card_configs.append(StatCardConfig(**card_data))

            # Create the final Settings DTO
            return Settings(
                row_count=int(data['row_count']),
                threshold_days=int(data['threshold_days']),
                orange_threshold_days=int(data['orange_threshold_days']),
                red_threshold_days=int(data['red_threshold_days']),
                stat_cards=card_configs
            )

        except (json.JSONDecodeError, TypeError, KeyError, OSError) as e:
            # Added TypeError and KeyError to catch bad data structures
            logger.error(f"Failed to load or parse settings from {file_path}: {e}")
            return None

    def _copy_file(self, source: Path, destination: Path):
        """Copy file from source to destination."""
        try:
            with open(source, 'rb') as src, open(destination, 'wb') as dst:
                dst.write(src.read())
        except Exception as e:
            logger.error(f"Failed to copy {source} to {destination}: {e}")
