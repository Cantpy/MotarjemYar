from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from enum import IntEnum


class PaymentStatus(IntEnum):
    """Payment status enumeration."""
    UNPAID = 0
    PAID = 1


class DeliveryStatus(IntEnum):
    """Delivery status enumeration."""
    PENDING = 0
    IN_PROGRESS = 1
    READY = 2
    QUALITY_CHECK = 3
    DELIVERED = 4


@dataclass
class Customer:
    """CustomerModel domain model."""
    national_id: str
    name: str
    phone: str
    address: str
    telegram_id: Optional[str] = None
    email: Optional[str] = None
    passport_image: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validate customer data after initialization."""
        if not self.national_id or len(self.national_id) != 10:
            raise ValueError("کد ملی باید دقیقاً 10 رقم باشد")
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("نام باید حداقل 2 کاراکتر باشد")
        if not self.phone or len(self.phone.strip()) < 10:
            raise ValueError("شماره تلفن باید حداقل 10 رقم باشد")
        if not self.address or len(self.address.strip()) < 5:
            raise ValueError("آدرس باید حداقل 5 کاراکتر باشد")


@dataclass
class Service:
    """ServicesModel domain model."""
    name: str
    base_price: int
    dynamic_price_1: Optional[int] = None
    dynamic_price_2: Optional[int] = None
    dynamic_price_name_1: Optional[str] = None
    dynamic_price_name_2: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validate service data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("نام سرویس نباید خالی باشد")
        if self.base_price < 0:
            raise ValueError("قیمت پایه نمی‌تواند منفی باشد")


@dataclass
class FixedPrice:
    """Fixed price domain model."""
    name: str
    price: int
    id: Optional[int] = None

    def __post_init__(self):
        """Validate fixed price data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("نام قیمت ثابت نباید خالی باشد")
        if self.price < 0:
            raise ValueError("قیمت نمی‌تواند منفی باشد")


@dataclass
class OtherService:
    """Other service domain model."""
    name: str
    description: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validate other service data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("نام سرویس نباید خالی باشد")


@dataclass
class InvoiceItem:
    """Invoice item domain model."""
    invoice_number: int
    item_name: str
    item_qty: int
    item_price: int
    officiality: int = 0
    judiciary_seal: int = 0
    foreign_affairs_seal: int = 0
    remarks: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validate invoice item data after initialization."""
        if not self.item_name or not self.item_name.strip():
            raise ValueError("نام آیتم نباید خالی باشد")
        if self.item_qty <= 0:
            raise ValueError("تعداد باید بزرگتر از صفر باشد")
        if self.item_price < 0:
            raise ValueError("قیمت نمی‌تواند منفی باشد")
        if self.officiality not in [0, 1]:
            raise ValueError("رسمی بودن باید 0 یا 1 باشد")
        if self.judiciary_seal not in [0, 1]:
            raise ValueError("مهر قوه قضاییه باید 0 یا 1 باشد")
        if self.foreign_affairs_seal not in [0, 1]:
            raise ValueError("مهر امور خارجه باید 0 یا 1 باشد")

    @property
    def total_price(self) -> int:
        """Calculate total price for this item."""
        return self.item_qty * self.item_price


@dataclass
class Invoice:
    """Invoice domain model."""
    invoice_number: int
    name: str
    national_id: str
    phone: str
    issue_date: date
    delivery_date: date
    translator: str
    total_amount: int = 0
    total_translation_price: int = 0
    advance_payment: int = 0
    discount_amount: int = 0
    force_majeure: int = 0
    final_amount: int = 0
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    remarks: Optional[str] = None
    username: Optional[str] = None
    items: List[InvoiceItem] = field(default_factory=list)
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    total_official_docs_count: int = 0
    total_unofficial_docs_count: int = 0
    total_pages_count: int = 0
    total_judiciary_count: int = 0
    total_foreign_affairs_count: int = 0
    total_additional_doc_count: int = 0
    id: Optional[int] = None

    def __post_init__(self):
        """Validate invoice data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("نام نباید خالی باشد")
        if not self.national_id or len(self.national_id) != 10:
            raise ValueError("کد ملی باید 10 رقم باشد")
        if not self.phone or len(self.phone) < 10:
            raise ValueError("شماره تلفن باید حداقل 10 رقم باشد")
        if not self.translator or not self.translator.strip():
            raise ValueError("نام مترجم نباید خالی باشد")
        if self.advance_payment < 0:
            raise ValueError("پیش‌پرداخت نمی‌تواند منفی باشد")
        if self.discount_amount < 0:
            raise ValueError("تخفیف نمی‌تواند منفی باشد")

    def add_item(self, item: InvoiceItem) -> None:
        """Add an item to the invoice."""
        item.invoice_number = self.invoice_number
        self.items.append(item)
        self.recalculate_totals()

    def remove_item(self, item_id: int) -> bool:
        """Remove an item from the invoice."""
        original_length = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        if len(self.items) < original_length:
            self.recalculate_totals()
            return True
        return False

    def recalculate_totals(self) -> None:
        """Recalculate all totals based on items."""
        self.total_amount = sum(item.total_price for item in self.items)
        self.total_translation_price = self.total_amount
        self.total_official_docs_count = sum(item.officiality for item in self.items)
        self.total_unofficial_docs_count = len(self.items) - self.total_official_docs_count
        self.total_pages_count = sum(item.item_qty for item in self.items)
        self.total_judiciary_count = sum(item.judiciary_seal for item in self.items)
        self.total_foreign_affairs_count = sum(item.foreign_affairs_seal for item in self.items)
        self.total_additional_doc_count = len(self.items)

        # Calculate final amount
        self.final_amount = (
                self.total_amount
                - self.discount_amount
                - self.advance_payment
                + self.force_majeure
        )

    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.payment_status == PaymentStatus.PAID

    def is_delivered(self) -> bool:
        """Check if invoice is delivered."""
        return self.delivery_status == DeliveryStatus.DELIVERED

    def get_pending_amount(self) -> int:
        """Get the pending payment amount."""
        if self.is_paid():
            return 0
        return max(0, self.final_amount)


@dataclass
class InvoiceTotals:
    """Invoice totals calculation result."""
    total_items_price: int
    total_items: int
    total_official_docs: int
    total_judiciary_docs: int
    total_foreign_docs: int
    total_pages: int


@dataclass
class ValidationError:
    """Validation error model."""
    field: str
    message: str


@dataclass
class OperationResult:
    """Generic operation result model."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: List[ValidationError] = field(default_factory=list)

    @classmethod
    def success_result(cls, message: str, data: Optional[Any] = None) -> 'OperationResult':
        """Create a successful operation result."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_result(cls, message: str, errors: Optional[List[ValidationError]] = None) -> 'OperationResult':
        """Create an error operation result."""
        return cls(success=False, message=message, errors=errors or [])

    @classmethod
    def validation_error_result(cls, errors: List[ValidationError]) -> 'OperationResult':
        """Create a validation error operation result."""
        return cls(
            success=False,
            message="خطای اعتبارسنجی",
            errors=errors
        )


@dataclass
class CustomerSearchCriteria:
    """CustomerModel search criteria."""
    name: Optional[str] = None
    phone: Optional[str] = None
    national_id: Optional[str] = None


@dataclass
class InvoiceSearchCriteria:
    """Invoice search criteria."""
    invoice_number: Optional[int] = None
    customer_name: Optional[str] = None
    national_id: Optional[str] = None
    payment_status: Optional[PaymentStatus] = None
    delivery_status: Optional[DeliveryStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
