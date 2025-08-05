from typing import List, Optional, Tuple
from features.InvoicePage.document_selection.document_selection_models import (Service, OtherService, FixedPrice,
                                                                               PriceCalculation, PriceDialogData)
from features.InvoicePage.document_selection.document_selection_repo import DatabaseRepository
from shared import to_persian_number


class DocumentLogic:
    """Core business logic for document operations"""

    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
        self._fixed_prices_cache = None

    def get_document_suggestions(self, partial_name: str) -> List[str]:
        """Get document name suggestions for autocomplete"""
        all_names = self.repository.get_all_document_names()
        return [name for name in all_names if partial_name.lower() in name.lower()]

    def validate_document_name(self, name: str) -> bool:
        """Validate if document name exists in database"""
        return self.repository.document_exists(name)

    def get_service_details(self, name: str) -> Optional[Service]:
        """Get service details by name"""
        return self.repository.get_service_by_name(name)

    def get_other_service_details(self, name: str) -> Optional[OtherService]:
        """Get other service details by name"""
        return self.repository.get_other_service_by_name(name)

    def get_fixed_prices(self) -> List[FixedPrice]:
        """Get all fixed prices with caching"""
        if self._fixed_prices_cache is None:
            self._fixed_prices_cache = self.repository.get_all_fixed_prices()
        return self._fixed_prices_cache

    def get_fixed_price_by_name(self, name: str) -> Optional[FixedPrice]:
        """Get fixed price by name"""
        fixed_prices = self.get_fixed_prices()
        for price in fixed_prices:
            if price.name == name:
                return price
        return None


class PriceCalculationLogic:
    """Business logic for price calculations"""

    def __init__(self, document_logic: DocumentLogic):
        self.document_logic = document_logic

    def calculate_price(self, data: PriceDialogData, service: Optional[Service] = None) -> Tuple[PriceCalculation, str]:
        """Calculate total price and generate remarks"""
        calculation = PriceCalculation()

        # Get fixed prices
        page_price_info = self.document_logic.get_fixed_price_by_name("certified_copy")
        office_price_info = self.document_logic.get_fixed_price_by_name("official_translation")
        judiciary_price_info = self.document_logic.get_fixed_price_by_name("judiciary_seal")
        foreign_affairs_price_info = self.document_logic.get_fixed_price_by_name("foreign_affairs_seal")
        additional_price_info = self.document_logic.get_fixed_price_by_name("additional_issues")

        # Page price calculation
        if page_price_info:
            calculation.page_price = (page_price_info.price * data.page_count) * data.document_count

        # Office price calculation (only for official documents)
        if office_price_info and data.is_official:
            calculation.office_price = office_price_info.price * data.document_count

        # Judiciary seal price
        if judiciary_price_info and data.judiciary_seal:
            calculation.judiciary_price = judiciary_price_info.price * data.document_count

        # Foreign affairs price
        if foreign_affairs_price_info and data.foreign_affairs_seal:
            calculation.foreign_affairs_price = foreign_affairs_price_info.price * data.document_count

        # Additional issues price
        if additional_price_info:
            calculation.additional_issue_price = additional_price_info.price * data.additional_issues

        # Base price and dynamic prices
        if service:
            if service.base_price:
                calculation.base_price = service.base_price * data.document_count

            # Dynamic price 1
            if service.dynamic_price_1 and data.dynamic_price_1_count > 0:
                calculation.dynamic_price_1_total = (
                        service.dynamic_price_1 * data.dynamic_price_1_count * data.document_count
                )

            # Dynamic price 2
            if service.dynamic_price_2 and data.dynamic_price_2_count > 0:
                calculation.dynamic_price_2_total = (
                        service.dynamic_price_2 * data.dynamic_price_2_count * data.document_count
                )

        # Generate remarks
        remarks = self._generate_remarks(data, service)

        return calculation, remarks

    def _generate_remarks(self, data: PriceDialogData, service: Optional[Service]) -> str:
        """Generate remarks text based on dynamic pricing"""
        if not service:
            return ""

        remarks_parts = []

        # Dynamic price 1
        if service.dynamic_price_name_1 and data.dynamic_price_1_count > 0:
            title = service.dynamic_price_name_1.replace("هر", "",
                                                         1).strip() if service.dynamic_price_name_1.startswith(
                "هر") else service.dynamic_price_name_1
            remarks_parts.append(f"{to_persian_number(data.dynamic_price_1_count)} {title}")

        # Dynamic price 2
        if service.dynamic_price_name_2 and data.dynamic_price_2_count > 0:
            title = service.dynamic_price_name_2.replace("هر", "",
                                                         1).strip() if service.dynamic_price_name_2.startswith(
                "هر") else service.dynamic_price_name_2
            remarks_parts.append(f"{to_persian_number(data.dynamic_price_2_count)} {title}")

        return " و ".join(remarks_parts)

    def get_dynamic_price_labels(self, service: Service) -> Tuple[Optional[str], Optional[str]]:
        """Get transformed dynamic price labels"""

        def transform_label(label: Optional[str]) -> Optional[str]:
            if label and label.startswith("هر"):
                return label.replace("هر", "تعداد", 1)
            return label

        label1 = transform_label(service.dynamic_price_name_1)
        label2 = transform_label(service.dynamic_price_name_2)

        return label1, label2

    def has_dynamic_pricing(self, service: Service) -> bool:
        """Check if service has dynamic pricing"""
        return bool(service.dynamic_price_name_1 or service.dynamic_price_name_2)

    def format_price_display(self, price: int) -> str:
        """Format price for display"""
        if price == 0:
            return "۰ تومان"
        return f"{to_persian_number(price)} تومان"


class InvoiceLogic:
    """Business logic for invoice management"""

    def __init__(self):
        self.items: List = []

    def add_item(self, item) -> None:
        """Add item to invoice"""
        self.items.append(item)

    def remove_item(self, index: int) -> bool:
        """Remove item from invoice by index"""
        if 0 <= index < len(self.items):
            del self.items[index]
            return True
        return False

    def get_total_amount(self) -> int:
        """Calculate total invoice amount"""
        return sum(item.total_price for item in self.items)

    def clear_items(self) -> None:
        """Clear all items from invoice"""
        self.items.clear()

    def get_items_count(self) -> int:
        """Get number of items in invoice"""
        return len(self.items)
