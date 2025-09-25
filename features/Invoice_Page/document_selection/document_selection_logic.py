# document_selection/_logic.py

from features.Invoice_Page.document_selection.document_selection_repo import DocumentSelectionRepository
from features.Invoice_Page.document_selection.document_selection_models import Service, FixedPrice, InvoiceItem
from shared.session_provider import ManagedSessionProvider


class DocumentSelectionLogic:
    """

    """

    def __init__(self, repo: DocumentSelectionRepository,
                 services_engine: ManagedSessionProvider):
        super().__init__()
        self._repo = repo
        self._services_engine = services_engine

        with self._services_engine() as session:
            self._services_map = {s.name: s for s in self._repo.get_all_services(session)}
            self._calculation_fees = self._repo.get_calculation_fees(session)
            self._fees_map = {fee.name: fee.price for fee in self._calculation_fees}

        # --- This is the state managed by the _logic layer ---
        self._current_invoice_items: list[InvoiceItem] = []

    # --- Public API for the Controller ---

    def get_all_service_names(self) -> list[str]:
        """Provides a simple list of service names for the UI completer."""
        return list(self._services_map.keys())

    def get_service_by_name(self, name: str) -> Service | None:
        """Retrieves a single service DTO by its name."""
        return self._services_map.get(name)

    def get_calculation_fees(self) -> list[FixedPrice]:
        """Provides the fee structure needed for the calculation dialog."""
        return self._calculation_fees

    def get_current_items(self) -> list[InvoiceItem]:
        """Returns the current list of all invoice items."""
        return self._current_invoice_items

    def add_item(self, item: InvoiceItem) -> list[InvoiceItem]:
        """Adds a new, fully calculated item to the invoice list."""
        self._current_invoice_items.append(item)
        return self._current_invoice_items

    def update_item_at_index(self, index: int, updated_item: InvoiceItem) -> list[InvoiceItem]:
        """Replaces an item at a specific index with an updated version."""
        if 0 <= index < len(self._current_invoice_items):
            self._current_invoice_items[index] = updated_item
        return self._current_invoice_items

    def delete_item_at_index(self, index: int) -> list[InvoiceItem]:
        """Deletes an item from the list by its index."""
        if 0 <= index < len(self._current_invoice_items):
            del self._current_invoice_items[index]
        return self._current_invoice_items

    def clear_all_items(self) -> list[InvoiceItem]:
        """Clears the entire list of items."""
        self._current_invoice_items.clear()
        return self._current_invoice_items

    def update_manual_item(self, item_to_update: InvoiceItem, new_price: int, new_remarks: str) -> list[
        InvoiceItem]:
        """Updates the price and remarks of a manually-entered item."""
        # Find the item by its unique ID for safety
        for item in self._current_invoice_items:
            if item.unique_id == item_to_update.unique_id:
                item.total_price = new_price
                item.remarks = new_remarks
                break
        return self._current_invoice_items

    def calculate_item_total(self, item: InvoiceItem) -> InvoiceItem:
        """
        A pure Python function to perform price calculations.
        This is the core business _logic, completely decoupled from the UI.
        """
        # This is a simplified example of the calculation _logic
        total = item.service.base_price * item.quantity
        if item.has_judiciary_seal:
            total += self._fees_map.get("مهر دادگستری", 0)
        if item.has_foreign_affairs_seal:
            total += self._fees_map.get("مهر امور خارجه", 0)

        item.total_price = total
        return item

    def calculate_invoice_item(self, item_shell: InvoiceItem) -> InvoiceItem:
        """
        NEW: This is the authoritative calculation engine.
        It takes an InvoiceItem with user inputs and returns a new
        InvoiceItem with all prices correctly calculated.
        """

        # A helper to safely get a fee price
        def get_fee(key: str) -> int:
            return self._fees_map.get(key, 0)

        # Start with base price
        translation_price = item_shell.service.base_price
        for dyn_name, dyn_quantity in item_shell.dynamic_quantities.items():
            dyn_price_obj = next((dp for dp in item_shell.service.dynamic_prices if dp.name == dyn_name), None)
            if dyn_price_obj:
                translation_price += dyn_quantity * dyn_price_obj.unit_price

        # Calculate all component prices
        item_shell.translation_price = translation_price * item_shell.quantity
        item_shell.certified_copy_price = item_shell.page_count * get_fee("کپ برابر اصل") * item_shell.quantity
        item_shell.registration_price = get_fee(
            "ثبت در سامانه") * item_shell.quantity if item_shell.is_official else 0
        item_shell.judiciary_seal_price = get_fee(
            "مهر دادگستری") * item_shell.quantity if item_shell.has_judiciary_seal else 0
        item_shell.foreign_affairs_seal_price = get_fee(
            "مهر امور خارجه") * item_shell.page_count if item_shell.has_foreign_affairs_seal else 0
        item_shell.extra_copy_price = item_shell.extra_copies * get_fee("نسخه اضافی")

        # Calculate final total price
        item_shell.total_price = (
                item_shell.translation_price +
                item_shell.certified_copy_price +
                item_shell.registration_price +
                item_shell.judiciary_seal_price +
                item_shell.foreign_affairs_seal_price +
                item_shell.extra_copy_price
        )

        # The original quantity needs to be adjusted for total
        item_shell.quantity += item_shell.extra_copies

        return item_shell
