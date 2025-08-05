from dataclasses import dataclass
from typing import Optional
from enum import Enum


class DocumentType(Enum):
    OFFICIAL = "رسمی"
    UNOFFICIAL = "غیررسمی"


@dataclass
class Service:
    """ServicesModel entity from services table"""
    id: int
    name: str
    base_price: Optional[int] = None
    dynamic_price_name_1: Optional[str] = None
    dynamic_price_1: Optional[int] = None
    dynamic_price_name_2: Optional[str] = None
    dynamic_price_2: Optional[int] = None


@dataclass
class OtherService:
    """Other service entity from other_services table"""
    id: int
    name: str
    price: int


@dataclass
class FixedPrice:
    """Fixed price entity from fixed_prices table"""
    id: int
    name: str
    price: int
    is_default: bool
    label_name: Optional[str] = None


@dataclass
class DocumentItem:
    """Document item for the invoice table"""
    name: str
    document_type: DocumentType
    count: int
    judiciary_seal: bool
    foreign_affairs_seal: bool
    total_price: int
    remarks: str

    @property
    def judiciary_display(self) -> str:
        return "✔" if self.judiciary_seal else "-"

    @property
    def foreign_affairs_display(self) -> str:
        return "✔" if self.foreign_affairs_seal else "-"


@dataclass
class PriceCalculation:
    """Price calculation details"""
    base_price: int = 0
    page_price: int = 0
    office_price: int = 0
    judiciary_price: int = 0
    foreign_affairs_price: int = 0
    additional_issue_price: int = 0
    dynamic_price_1_total: int = 0
    dynamic_price_2_total: int = 0

    @property
    def total_price(self) -> int:
        return (
                self.base_price + self.page_price + self.office_price +
                self.judiciary_price + self.foreign_affairs_price +
                self.additional_issue_price + self.dynamic_price_1_total +
                self.dynamic_price_2_total
        )


@dataclass
class PriceDialogData:
    """Data structure for price dialog input/output"""
    document_name: str
    document_count: int = 1
    page_count: int = 1
    additional_issues: int = 0
    is_official: bool = True
    judiciary_seal: bool = False
    foreign_affairs_seal: bool = False
    dynamic_price_1_count: int = 0
    dynamic_price_2_count: int = 0

    def to_document_item(self, total_price: int, remarks: str) -> DocumentItem:
        """Convert to DocumentItem"""
        return DocumentItem(
            name=self.document_name,
            document_type=DocumentType.OFFICIAL if self.is_official else DocumentType.UNOFFICIAL,
            count=self.document_count,
            judiciary_seal=self.judiciary_seal,
            foreign_affairs_seal=self.foreign_affairs_seal,
            total_price=total_price,
            remarks=remarks
        )
