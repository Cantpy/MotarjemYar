from dataclasses import dataclass
from typing import Optional
from enum import Enum


class DynamicPriceMode(Enum):
    """Dynamic price display modes"""
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"


@dataclass
class DynamicPriceConfig:
    """Configuration for dynamic pricing UI"""
    mode: DynamicPriceMode
    label1: Optional[str] = None
    label2: Optional[str] = None
    price1: Optional[int] = None
    price2: Optional[int] = None


@dataclass
class PriceDisplayData:
    """Data for price display labels"""
    translation_price: str = "۰ تومان"
    page_price: str = "۰ تومان"
    office_price: str = "۰ تومان"
    judiciary_price: str = "۰ تومان"
    foreign_affairs_price: str = "۰ تومان"
    additional_price: str = "۰ تومان"
    total_price: str = "۰ تومان"


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    error_message: Optional[str] = None


class PriceDialogState:
    """State management for price dialog"""

    def __init__(self):
        self.document_name: str = ""
        self.document_count: int = 1
        self.page_count: int = 1
        self.additional_issues: int = 0
        self.is_official: bool = True
        self.judiciary_seal: bool = False
        self.foreign_affairs_seal: bool = False
        self.dynamic_price_1_count: int = 0
        self.dynamic_price_2_count: int = 0

        # UI state
        self.dynamic_config: Optional[DynamicPriceConfig] = None
        self.price_display: PriceDisplayData = PriceDisplayData()

    def reset(self) -> None:
        """Reset state to defaults"""
        self.__init__()

    def validate_inputs(self) -> ValidationResult:
        """Validate current input values"""
        if self.document_count <= 0:
            return ValidationResult(False, "تعداد اسناد نمی‌تواند ۰ باشد")

        if self.page_count <= 0:
            return ValidationResult(False, "تعداد صفحات سند نمی‌تواند ۰ باشد")

        if not self.document_name.strip():
            return ValidationResult(False, "نام سند نمی‌تواند خالی باشد")

        return ValidationResult(True)

    def get_dialog_data(self):
        """Convert state to PriceDialogData"""
        from features.InvoicePage.document_selection.document_selection_models import PriceDialogData
        return PriceDialogData(
            document_name=self.document_name,
            document_count=self.document_count,
            page_count=self.page_count,
            additional_issues=self.additional_issues,
            is_official=self.is_official,
            judiciary_seal=self.judiciary_seal,
            foreign_affairs_seal=self.foreign_affairs_seal,
            dynamic_price_1_count=self.dynamic_price_1_count,
            dynamic_price_2_count=self.dynamic_price_2_count
        )

    def update_from_dialog_data(self, data) -> None:
        """Update state from PriceDialogData"""
        self.document_name = data.document_name
        self.document_count = data.document_count
        self.page_count = data.page_count
        self.additional_issues = data.additional_issues
        self.is_official = data.is_official
        self.judiciary_seal = data.judiciary_seal
        self.foreign_affairs_seal = data.foreign_affairs_seal
        self.dynamic_price_1_count = data.dynamic_price_1_count
        self.dynamic_price_2_count = data.dynamic_price_2_count


@dataclass
class PriceDialogResult:
    """Result returned from price dialog"""
    accepted: bool
    document_item: Optional[object] = None  # DocumentItem from models.py
    error_message: Optional[str] = None
