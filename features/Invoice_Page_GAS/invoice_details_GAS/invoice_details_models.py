# invoice_details/models.py
from dataclasses import dataclass
from enum import Enum


@dataclass
class OfficeInfo:
    """Represents the translation office's data."""
    name: str = ""
    reg_no: str = ""
    representative: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""


@dataclass
class InvoiceDetails:
    """Holds all calculated and user-inputted data for the details step."""
    # Factual Info
    invoice_number: int = 0
    docu_num: int = 0
    issue_date: str = ""
    delivery_date: str = ""
    user: str = "نامشخص"
    src_lng: str = "فارسی"
    trgt_lng: str = "انگلیسی"

    # Financial Info
    translation_cost: int = 0
    confirmation_cost: int = 0
    office_costs: int = 0
    certified_copy_costs: int = 0
    total_before_variables: int = 0

    # --- User inputs are now expanded ---
    emergency_cost_percent: float = 0.0
    emergency_cost_amount: int = 0

    discount_percent: float = 0.0
    discount_amount: int = 0

    advance_payment_percent: float = 0.0
    advance_payment_amount: int = 0

    remarks: str = "..."

    # --- Calculated Financials ---
    total_before_discount: int = 0
    total_after_discount: int = 0
    final_amount: int = 0

    # Office Info
    office_info: OfficeInfo = None


class Language(Enum):
    """Supported languages for translation."""
    FARSI = "فارسی"
    ENGLISH = "انگلیسی"
    ARABIC = "عربی"
    GERMAN = "آلمانی"
    FRENCH = "فرانسوی"
    SPANISH = "اسپانیولی"
    ITALIAN = "ایتالیایی"
    RUSSIAN = "روسی"
    CHINESE = "چینی"
    JAPANESE = "ژاپنی"
    KOREAN = "کره‌ای"
    TURKISH = "ترکی استانبولی"
    AZERBAIJANI = "آذربایجانی"
    URDU = "اردو"
    ARMENIAN = "ارمنی"
    ROMANIAN = "رومانیایی"
    SERBIAN = "صربی"
    KURDISH = "کردی"
