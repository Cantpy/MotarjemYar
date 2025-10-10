# features/Invoice_Page/invoice_details/invoice_details_models.py

from dataclasses import dataclass, field
from enum import Enum
from features.Invoice_Page.invoice_preview.invoice_preview_models import PreviewOfficeInfo
from datetime import datetime


@dataclass
class UserInfo:
    """Represents the logged-in user's data."""
    full_name: str = "نامشخص"
    role: str = "نامشخص"
    role_fa: str = "نامشخص"
    username: str = "نامشخص"


@dataclass
class InvoiceDetails:
    """Holds all calculated and user-inputted data for the details step."""
    # Factual Info
    invoice_number: str = ""
    docu_num: int = 0

    issue_date: datetime | None = None
    delivery_date: datetime | None = None

    user: UserInfo = field(default_factory=UserInfo)
    src_lng: str = "فارسی"
    trgt_lng: str = "انگلیسی"

    # Financial Info
    translation_cost: int = 0
    confirmation_cost: int = 0
    office_costs: int = 0
    certified_copy_costs: int = 0
    additional_issues_costs: int = 0
    total_before_variables: int = 0

    # --- User inputs are now expanded ---
    emergency_cost_percent: float = 0.0
    emergency_cost_amount: int = 0

    discount_percent: float = 0.0
    discount_amount: int = 0

    advance_payment_percent: float = 0.0
    advance_payment_amount: int = 0

    remarks: str = ""

    # --- Calculated Financials ---
    total_before_discount: int = 0
    total_after_discount: int = 0
    final_amount: int = 0

    # Office Info
    office_info: PreviewOfficeInfo | None = None


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
