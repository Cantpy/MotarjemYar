# features\Home_Page\home_page_settings\home_page_settings_models.py

from dataclasses import dataclass, field
from typing import List


@dataclass
class StatCardConfig:
    """Configuration for a single stat card."""
    id: str
    title: str
    color: str
    enabled: bool = True
    display_order: int = 0


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
