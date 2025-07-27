import logging
from pathlib import Path
from features.Home.home_settings_models import Settings
from typing import Optional, Union
import json
from dataclasses import asdict


# Configure logging for settings operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SettingsManager:
    """Manage settings persistence to file with error handling and validation."""

    SETTINGS_FILE = Path("config") / "homepage_settings.json"
    BACKUP_FILE = Path("config") / "homepage_settings_backup.json"

    @classmethod
    def _ensure_config_directory(cls):
        """Ensure the config directory exists."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_settings(cls) -> Settings:
        """
        Load settings from file with fallback to backup and defaults.

        Returns:
            Settings instance loaded from file, backup, or defaults
        """
        cls._ensure_config_directory()

        # Try to load from main settings file
        settings = cls._load_from_file(cls.SETTINGS_FILE)
        if settings:
            logger.info("Settings loaded successfully from main file")
            return settings

        # Try to load from backup file
        logger.warning("Main settings file failed, trying backup")
        settings = cls._load_from_file(cls.BACKUP_FILE)
        if settings:
            logger.info("Settings loaded from backup file")
            # Restore main file from backup
            cls._copy_file(cls.BACKUP_FILE, cls.SETTINGS_FILE)
            return settings

        # Return defaults if both fail
        logger.warning("Both settings files failed, using defaults")
        default_settings = Settings.default()
        cls.save_settings(default_settings)  # Create initial file
        return default_settings

    @classmethod
    def _load_from_file(cls, file_path: Path) -> Optional[Settings]:
        """
        Load settings from a specific file.

        Args:
            file_path: Path to the settings file

        Returns:
            Settings instance or None if loading failed
        """
        try:
            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ['row_count', 'threshold_days', 'orange_threshold_days',
                               'red_threshold_days', 'total_cards_number']

            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in {file_path}")
                return None

            # Validate data types and ranges
            if not cls._validate_settings_data(data):
                logger.error(f"Invalid settings data in {file_path}")
                return None

            return Settings(
                row_count=int(data['row_count']),
                threshold_days=int(data['threshold_days']),
                orange_threshold_days=int(data['orange_threshold_days']),
                red_threshold_days=int(data['red_threshold_days']),
                total_cards_number=int(data['total_cards_number']),
                stat_cards=data.get('stat_cards')  # Optional field
            )

        except (json.JSONDecodeError, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to load settings from {file_path}: {e}")
            return None

    @classmethod
    def _validate_settings_data(cls, data: dict) -> bool:
        """
        Validate settings data for reasonable ranges.

        Args:
            data: Dictionary containing settings data

        Returns:
            True if data is valid, False otherwise
        """
        try:
            validations = [
                1 <= int(data['row_count']) <= 1000,
                1 <= int(data['threshold_days']) <= 365,
                1 <= int(data['orange_threshold_days']) <= 30,
                1 <= int(data['red_threshold_days']) <= 30,
                1 <= int(data['total_cards_number']) <= 50
            ]
            return all(validations)
        except (ValueError, TypeError, KeyError):
            return False

    @classmethod
    def save_settings(cls, settings: Settings) -> bool:
        """
        Save settings to file with backup.

        Args:
            settings: Settings instance to save

        Returns:
            True if save was successful, False otherwise
        """
        cls._ensure_config_directory()

        try:
            # Create backup of existing file if it exists
            if cls.SETTINGS_FILE.exists():
                cls._copy_file(cls.SETTINGS_FILE, cls.BACKUP_FILE)

            # Prepare data for saving
            data = {
                'row_count': settings.row_count,
                'threshold_days': settings.threshold_days,
                'orange_threshold_days': settings.orange_threshold_days,
                'red_threshold_days': settings.red_threshold_days,
                'total_cards_number': settings.total_cards_number,
                'stat_cards': settings.stat_cards,
                'version': '1.0',  # For future compatibility
                'saved_at': str(Path().absolute()),  # Save location info
            }

            # Write to temporary file first, then rename (atomic operation)
            temp_file = cls.SETTINGS_FILE.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Rename temp file to actual file (atomic on most systems)
            temp_file.replace(cls.SETTINGS_FILE)

            logger.info(f"Settings saved successfully to {cls.SETTINGS_FILE}")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    @classmethod
    def _copy_file(cls, source: Path, destination: Path):
        """Copy file from source to destination."""
        try:
            with open(source, 'rb') as src, open(destination, 'wb') as dst:
                dst.write(src.read())
        except Exception as e:
            logger.error(f"Failed to copy {source} to {destination}: {e}")

    @classmethod
    def reset_to_defaults(cls) -> Settings:
        """
        Reset settings to defaults and save.

        Returns:
            Default Settings instance
        """
        logger.info("Resetting settings to defaults")
        default_settings = Settings.default()
        cls.save_settings(default_settings)
        return default_settings

    @classmethod
    def export_settings(cls, export_path: Union[str, Path], settings: Settings) -> bool:
        """
        Export settings to a specific file.

        Args:
            export_path: Path where to export settings
            settings: Settings to export

        Returns:
            True if export was successful
        """
        try:
            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            data = asdict(settings)
            data['exported_at'] = str(Path().absolute())
            data['version'] = '1.0'

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Settings exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export settings to {export_path}: {e}")
            return False

    @classmethod
    def import_settings(cls, import_path: Union[str, Path]) -> Optional[Settings]:
        """
        Import settings from a specific file.

        Args:
            import_path: Path to import settings from

        Returns:
            Settings instance or None if import failed
        """
        return cls._load_from_file(Path(import_path))
