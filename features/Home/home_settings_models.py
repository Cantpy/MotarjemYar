from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Settings:
    row_count: int
    threshold_days: int
    orange_threshold_days: int
    red_threshold_days: int
    total_cards_number: int
    stat_cards: Optional[List[tuple]] = None

    @staticmethod
    def default() -> "Settings":
        return Settings(
            row_count=10,
            threshold_days=10,
            orange_threshold_days=3,
            red_threshold_days=1,
            total_cards_number=6,
            stat_cards=None
        )

    def __eq__(self, other):
        """Compare settings for equality (excluding stat_cards for simplicity)."""
        if not isinstance(other, Settings):
            return False
        return (
            self.row_count == other.row_count and
            self.threshold_days == other.threshold_days and
            self.orange_threshold_days == other.orange_threshold_days and
            self.red_threshold_days == other.red_threshold_days and
            self.total_cards_number == other.total_cards_number
        )
