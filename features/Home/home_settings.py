""" settings.py - Updated Settings dataclass. """

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class StatCardConfig:
    """Configuration for a single stat card."""
    id: str  # Unique identifier matching DashboardStats field
    title: str  # Display title in Persian
    color: str  # Hex color code
    enabled: bool = True  # Whether this card is currently displayed
    display_order: int = 0  # Order in which to display the card


@dataclass
class Settings:
    """Application settings with flexible stat cards configuration."""
    row_count: int = 10
    threshold_days: int = 30
    orange_threshold_days: int = 7
    red_threshold_days: int = 3
    total_cards_number: int = 6
    stat_cards: List[StatCardConfig] = field(default_factory=list)

    @classmethod
    def default(cls, max_cards: int = 6) -> 'Settings':
        """Create default settings with predefined stat cards."""
        # Define all available stat cards
        default_cards = [
            StatCardConfig("total_customers", "تعداد مشتریان", "#2980b9", True, 0),
            StatCardConfig("total_invoices", "کل فاکتورها", "#3498db", True, 1),
            StatCardConfig("today_invoices", "فاکتورهای امروز", "#1abc9c", True, 2),
            StatCardConfig("total_documents", "کل مدارک", "#8e44ad", True, 3),
            StatCardConfig("available_documents", "مدارک موجود در دفتر", "#e67e22", True, 4),
            StatCardConfig("most_repeated_document", "پرتکرارترین مدرک", "#27ae60", True, 5),
            StatCardConfig("most_repeated_document_month", "پرتکرارترین مدرک ماه", "#e74c3c", False, 6),
        ]

        # Enable only the first 'max_cards' cards by default
        enabled_count = min(max_cards, len(default_cards))
        for i, card in enumerate(default_cards):
            card.enabled = i < enabled_count

        return cls(
            total_cards_number=enabled_count,
            stat_cards=default_cards
        )

    def get_enabled_cards(self) -> List[StatCardConfig]:
        """Get list of enabled cards sorted by display order."""
        enabled = [card for card in self.stat_cards if card.enabled]
        return sorted(enabled, key=lambda x: x.display_order)

    def get_available_cards(self) -> List[StatCardConfig]:
        """Get all available cards sorted by display order."""
        return sorted(self.stat_cards, key=lambda x: x.display_order)

    def set_card_enabled(self, card_id: str, enabled: bool):
        """Enable or disable a specific card."""
        for card in self.stat_cards:
            if card.id == card_id:
                card.enabled = enabled
                break

        # Update total_cards_number
        self.total_cards_number = len(self.get_enabled_cards())

    def validate_card_count(self) -> bool:
        """Validate that total cards is a multiple of 3."""
        return self.total_cards_number % 3 == 0 and self.total_cards_number >= 0


class SettingsManager:
    """Manage settings persistence to file with error handling and validation."""

    SETTINGS_FILE = Path("config") / "homepage_settings.json"
    BACKUP_FILE = Path("config") / "homepage_settings_backup.json"

    @classmethod
    def _ensure_config_directory(cls):
        """Ensure the config directory exists."""
        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load_settings(cls, max_cards: int = 6) -> Settings:
        """
        Load settings from file with fallback to backup and defaults.

        Args:
            max_cards: Maximum number of cards that can be displayed (default: 6)

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
        default_settings = Settings.default(max_cards)
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

            # Load stat cards if present
            stat_cards = []
            if 'stat_cards' in data and isinstance(data['stat_cards'], list):
                for card_data in data['stat_cards']:
                    if cls._validate_card_data(card_data):
                        stat_cards.append(StatCardConfig(
                            id=card_data['id'],
                            title=card_data['title'],
                            color=card_data['color'],
                            enabled=card_data.get('enabled', True),
                            display_order=card_data.get('display_order', 0)
                        ))

            # If no valid stat cards found, use defaults
            if not stat_cards:
                logger.warning("No valid stat cards found, using defaults")
                default_settings = Settings.default()
                stat_cards = default_settings.stat_cards

            return Settings(
                row_count=int(data['row_count']),
                threshold_days=int(data['threshold_days']),
                orange_threshold_days=int(data['orange_threshold_days']),
                red_threshold_days=int(data['red_threshold_days']),
                total_cards_number=int(data['total_cards_number']),
                stat_cards=stat_cards
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
                0 <= int(data['total_cards_number']) <= 21,  # Max 21 cards (7 rows x 3)
                int(data['total_cards_number']) % 3 == 0  # Must be multiple of 3
            ]
            return all(validations)
        except (ValueError, TypeError, KeyError):
            return False

    @classmethod
    def _validate_card_data(cls, card_data: dict) -> bool:
        """Validate individual card data."""
        try:
            required_fields = ['id', 'title', 'color']
            if not all(field in card_data for field in required_fields):
                return False

            # Validate color format (hex color)
            color = card_data['color']
            if not (isinstance(color, str) and color.startswith('#') and len(color) == 7):
                return False

            return True
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

            # Prepare stat cards data
            stat_cards_data = []
            for card in settings.stat_cards:
                stat_cards_data.append({
                    'id': card.id,
                    'title': card.title,
                    'color': card.color,
                    'enabled': card.enabled,
                    'display_order': card.display_order
                })

            # Prepare data for saving
            data = {
                'row_count': settings.row_count,
                'threshold_days': settings.threshold_days,
                'orange_threshold_days': settings.orange_threshold_days,
                'red_threshold_days': settings.red_threshold_days,
                'total_cards_number': settings.total_cards_number,
                'stat_cards': stat_cards_data,
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
    def reset_to_defaults(cls, max_cards: int = 6) -> Settings:
        """
        Reset settings to defaults and save.

        Args:
            max_cards: Maximum number of cards for default settings

        Returns:
            Default Settings instance
        """
        logger.info("Resetting settings to defaults")
        default_settings = Settings.default(max_cards)
        cls.save_settings(default_settings)
        return default_settings

    @classmethod
    def export_settings(cls, export_path: Path, settings: Settings) -> bool:
        """
        Export settings to a specific file.

        Args:
            export_path: Path where to export settings
            settings: Settings to export

        Returns:
            True if export was successful
        """
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare stat cards data
            stat_cards_data = []
            for card in settings.stat_cards:
                stat_cards_data.append({
                    'id': card.id,
                    'title': card.title,
                    'color': card.color,
                    'enabled': card.enabled,
                    'display_order': card.display_order
                })

            data = {
                'row_count': settings.row_count,
                'threshold_days': settings.threshold_days,
                'orange_threshold_days': settings.orange_threshold_days,
                'red_threshold_days': settings.red_threshold_days,
                'total_cards_number': settings.total_cards_number,
                'stat_cards': stat_cards_data,
                'exported_at': str(Path().absolute()),
                'version': '1.0'
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Settings exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export settings to {export_path}: {e}")
            return False

    @classmethod
    def import_settings(cls, import_path: Path) -> Optional[Settings]:
        """
        Import settings from a specific file.

        Args:
            import_path: Path to import settings from

        Returns:
            Settings instance or None if import failed
        """
        return cls._load_from_file(import_path)
