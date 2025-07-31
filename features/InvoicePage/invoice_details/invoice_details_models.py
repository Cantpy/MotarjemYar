from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum


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


@dataclass
class TranslationOfficeInfo:
    """Information about the translation office."""
    name: str = "نامشخص"
    registration_number: int = 0
    translator: str = "نامشخص"
    address: str = "نامشخص"
    phone: str = "نامشخص"
    email: str = "نامشخص"


@dataclass
class FinancialDetails:
    """Financial details of the invoice."""
    translation_cost: int = 0
    confirmation_cost: int = 0
    office_affairs_cost: int = 0
    copy_certification_cost: int = 0
    emergency_cost: int = 0
    is_emergency: bool = False
    discount_amount: int = 0
    advance_payment: int = 0

    @property
    def subtotal(self) -> int:
        """Calculate subtotal before discount and advance payment."""
        return (self.translation_cost + self.confirmation_cost +
                self.office_affairs_cost + self.copy_certification_cost +
                self.emergency_cost)

    @property
    def final_amount(self) -> int:
        """Calculate final amount after discount and advance payment."""
        return max(0, self.subtotal - self.discount_amount - self.advance_payment)


@dataclass
class InvoiceData:
    """Complete invoice data model."""
    # Invoice basic info
    receipt_number: str = "نامشخص"
    receive_date: datetime = field(default_factory=datetime.now)
    delivery_date: date = field(default_factory=lambda: date.today())
    username: str = "نامشخص"

    # Translation info
    source_language: Language = Language.FARSI
    target_language: Language = Language.ENGLISH

    # Financial details
    financial: FinancialDetails = field(default_factory=FinancialDetails)

    # Translation office info
    office_info: TranslationOfficeInfo = field(default_factory=TranslationOfficeInfo)

    # Additional info
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'receipt_number': self.receipt_number,
            'receive_date': self.receive_date.isoformat() if isinstance(self.receive_date, datetime) else str(
                self.receive_date),
            'delivery_date': self.delivery_date.isoformat() if isinstance(self.delivery_date, date) else str(
                self.delivery_date),
            'username': self.username,
            'source_language': self.source_language.value,
            'target_language': self.target_language.value,
            'translation_cost': self.financial.translation_cost,
            'confirmation_cost': self.financial.confirmation_cost,
            'office_affairs_cost': self.financial.office_affairs_cost,
            'copy_certification_cost': self.financial.copy_certification_cost,
            'emergency_cost': self.financial.emergency_cost,
            'is_emergency': self.financial.is_emergency,
            'discount_amount': self.financial.discount_amount,
            'advance_payment': self.financial.advance_payment,
            'office_name': self.office_info.name,
            'office_address': self.office_info.address,
            'office_phone': self.office_info.phone,
            'office_email': self.office_info.email,
            'office_license': self.office_info.registration_number,
            'office_translator': self.office_info.translator,
            'remarks': self.remarks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InvoiceData':
        """Create from dictionary."""
        # Parse dates
        receive_date = data.get('receive_date', datetime.now())
        if isinstance(receive_date, str):
            try:
                receive_date = datetime.fromisoformat(receive_date)
            except ValueError:
                receive_date = datetime.now()

        delivery_date = data.get('delivery_date', date.today())
        if isinstance(delivery_date, str):
            try:
                delivery_date = date.fromisoformat(delivery_date)
            except ValueError:
                delivery_date = date.today()

        # Parse languages
        source_lang = Language.FARSI
        target_lang = Language.ENGLISH

        for lang in Language:
            if lang.value == data.get('source_language'):
                source_lang = lang
            if lang.value == data.get('target_language'):
                target_lang = lang

        # Create financial details
        financial = FinancialDetails(
            translation_cost=data.get('translation_cost', 0),
            confirmation_cost=data.get('confirmation_cost', 0),
            office_affairs_cost=data.get('office_affairs_cost', 0),
            copy_certification_cost=data.get('copy_certification_cost', 0),
            emergency_cost=data.get('emergency_cost', 0),
            is_emergency=data.get('is_emergency', False),
            discount_amount=data.get('discount_amount', 0),
            advance_payment=data.get('advance_payment', 0)
        )

        # Create office info
        office_info = TranslationOfficeInfo(
            name=data.get('office_name', 'نامشخص'),
            address=data.get('office_address', 'نامشخص'),
            phone=data.get('office_phone', 'نامشخص'),
            email=data.get('office_email', 'نامشخص'),
            registration_number=data.get('office_license', 0)
        )

        return cls(
            receipt_number=data.get('receipt_number', 'نامشخص'),
            receive_date=receive_date,
            delivery_date=delivery_date,
            username=data.get('username', 'نامشخص'),
            source_language=source_lang,
            target_language=target_lang,
            financial=financial,
            office_info=office_info,
            remarks=data.get('remarks', '')
        )

    def is_valid(self) -> bool:
        """Check if the invoice data is valid."""
        return (self.receipt_number != "نامشخص" and
                self.receipt_number.strip() != "" and
                self.financial.subtotal > 0)

    def get_validation_errors(self) -> list:
        """Get list of validation errors."""
        errors = []

        if self.receipt_number == "نامشخص" or not self.receipt_number.strip():
            errors.append("شماره رسید الزامی است")

        if self.financial.subtotal <= 0:
            errors.append("مجموع هزینه باید بیشتر از صفر باشد")

        if self.financial.discount_amount > self.financial.subtotal:
            errors.append("تخفیف نمی‌تواند بیشتر از مجموع هزینه باشد")

        if self.financial.advance_payment > (self.financial.subtotal - self.financial.discount_amount):
            errors.append("پیش‌پرداخت نمی‌تواند بیشتر از مبلغ قابل پرداخت باشد")

        if self.delivery_date < self.receive_date.date():
            errors.append("تاریخ تحویل نمی‌تواند قبل از تاریخ دریافت باشد")

        return errors
