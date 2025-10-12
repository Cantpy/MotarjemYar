# features/Invoice_Page/document_selection/document_selection_logic.py

from features.Invoice_Page.document_selection.document_selection_repo import DocumentSelectionRepository
from features.Invoice_Page.document_selection.document_selection_models import Service, FixedPrice, InvoiceItem
from shared.session_provider import ManagedSessionProvider


class DocumentSelectionLogic:
    """
    The core business _logic for the document selection page.
    """

    def __init__(self, repo: DocumentSelectionRepository,
                 services_engine: ManagedSessionProvider):
        super().__init__()
        self._repo = repo
        self._services_engine = services_engine
        self._parsing_keywords = {
            "با تاییدات": {"judiciary": True, "foreign_affairs": True},
            "با مهرها": {"judiciary": True, "foreign_affairs": True},
            "مهر دادگستری": {"judiciary": True},
            "دادگستری": {"judiciary": True},
            "مهر امور خارجه": {"foreign_affairs": True},
            "مهر خارجه": {"foreign_affairs": True},
            "امورخارجه": {"foreign_affairs": True},
            "رسمی": {"is_official": True},
            "غیررسمی": {"is_official": False},
            "غیر رسمی": {"is_official": False},
        }

        self._special_keywords = {
            'page_count': ['صفحه', 'صحفه', 'برگ', 'برگه'],
            'quantity': ['عدد', 'نسخه', 'فقره', 'تا'],
            'extra_copies': ['نسخه اضافی', 'اضافی'],
        }

        with self._services_engine() as session:
            self._services_map = {s.name: s for s in self._repo.get_all_services(session)}
            self._calculation_fees = self._repo.get_calculation_fees(session)
            self._fees_map = {fee.name: fee.price for fee in self._calculation_fees}

        # --- This is the state managed by the _logic layer ---
        self._current_invoice_items: list[InvoiceItem] = []

        self._load_all_data()

    # --- Public API for the Controller ---

    def _load_all_data(self):
        """
        Private method to fetch all services, fees, and aliases from the
        database and populate the in-memory cache.
        """
        print("Reloading all services, fees, and aliases from the database...")
        with self._services_engine() as session:
            all_services_and_fees = self._repo.get_all_services(session)
            # Create a map of both Service and FixedPrice objects by name
            self._services_map = {s.name: s for s in all_services_and_fees}

            self._calculation_fees = self._repo.get_calculation_fees(session)
            self._fees_map = {fee.name: fee.price for fee in self._calculation_fees}
        print("Data reloaded successfully.")

    def refresh_all_data(self):
        """
        Public API for the controller to trigger a full reload of the application's
        service and fee data from the database.
        """
        self._load_all_data()

    def get_smart_search_history(self) -> list[str]:
        """Provides a list of recent smart search entries for the completer."""
        with self._services_engine() as session:
            return self._repo.get_smart_search_history(session)

    def _build_item_shell(self, service, original_text: str, quantity: int, page_count: int, extra_copies: int,
                          dynamic_quantities: dict, options: dict):

        """Builds a preliminary InvoiceItem before calculation."""
        return InvoiceItem(
            service=service,
            quantity=quantity,
            page_count=page_count,
            extra_copies=extra_copies,
            has_judiciary_seal=options["judiciary"],
            has_foreign_affairs_seal=options["foreign_affairs"],
            is_official=options["is_official"],
            dynamic_quantities=dynamic_quantities,
            remarks=f"افزودن سریع: {original_text}",
        )

    def process_smart_entry(self, text: str) -> bool:
        """
        Main entry point. Now handles a leading number as a prioritized quantity.
        """
        original_text = text

        # 1. Extract options (seals, etc.)
        options, cleaned_text = self._extract_options(text)

        # 2. Extract ALL numeric patterns first
        patterns, service_text = self._extract_patterns(cleaned_text)

        # 3. Find the service from the text that remains AFTER patterns are removed
        service = self._find_service_from_text(service_text)
        if not service:
            # Fallback: If service not found, try searching the original cleaned text
            service = self._find_service_from_text(cleaned_text)
            if not service: return False

        # 4. Assign quantities based on keywords
        parsed_quantity, page_count, extra_copies, dynamic_quantities = self._assign_quantities(service, patterns)

        # 5. Check for a leading number as a final override
        import re
        final_quantity = parsed_quantity
        leading_match = re.match(r'^(\d+)\s+', cleaned_text)
        # If an explicit keyword like 'تا' wasn't used, AND a leading number exists, use the leading number.
        if parsed_quantity == 1 and leading_match:
            final_quantity = int(leading_match.group(1))

        # 6. Build the shell
        item_shell = self._build_item_shell(
            service=service,
            original_text=original_text,
            quantity=final_quantity,
            page_count=page_count,
            extra_copies=extra_copies,
            dynamic_quantities=dynamic_quantities,
            options=options,
        )

        # 7. Finalize and add
        final_item = self.calculate_invoice_item(item_shell)
        self.add_item(final_item)
        self._add_to_smart_search_history(original_text)

        return True

    def _extract_options(self, text: str) -> tuple[dict, str]:
        """Parse text for special keywords and return options + cleaned text."""
        options = {
            "judiciary": False,
            "foreign_affairs": False,
            "is_official": True,
        }
        cleaned_text = text
        for keyword, effect in self._parsing_keywords.items():
            if keyword in cleaned_text:
                cleaned_text = cleaned_text.replace(keyword, "", -1).strip()
                if effect.get("judiciary"):
                    options["judiciary"] = True
                if effect.get("foreign_affairs"):
                    options["foreign_affairs"] = True
                if effect.get("is_official") is not None:
                    options["is_official"] = effect["is_official"]
        return options, cleaned_text

    def _assign_quantities(self, service, patterns: list[tuple[str, str]]) -> tuple[int, int, int, dict]:
        """Assign quantity, page_count, extra_copies, and dynamic values."""
        quantity = 1
        page_count = service.default_page_count
        extra_copies = 0
        dynamic_quantities = {}

        unassigned = list(patterns)
        assigned = []

        # Pass 1: Special keywords
        for num_str, word in unassigned:
            num = int(num_str)
            if word in self._special_keywords['page_count']:
                page_count = num
                assigned.append((num_str, word))
            elif word in self._special_keywords['quantity']:
                quantity = num
                assigned.append((num_str, word))
            elif word in self._special_keywords['extra_copies']:
                extra_copies = num
                assigned.append((num_str, word))

        unassigned = [p for p in unassigned if p not in assigned]

        # Pass 2: Dynamic prices
        for num_str, word in unassigned:
            num = int(num_str)
            for dyn_price in service.dynamic_prices:
                if word == dyn_price.name or word in dyn_price.aliases:
                    dynamic_quantities[dyn_price.name] = num
                    assigned.append((num_str, word))
                    break

        unassigned = [p for p in unassigned if p not in assigned]

        # Pass 3: Single leftover may be quantity
        if len(unassigned) == 1:
            num_str, word = unassigned[0]
            if word == service.name or word in service.aliases:
                quantity = int(num_str)

        return quantity, page_count, extra_copies, dynamic_quantities

    def _extract_patterns(self, text: str) -> tuple[list[tuple[str, str]], str]:
        """Find number-word pairs and return remaining service text."""
        import re
        patterns = re.findall(r'(\d+)\s+([\w]+)', text)
        service_text = text
        for num, word in patterns:
            service_text = service_text.replace(f"{num} {word}", "", 1).strip()
        # Cleanup connectors
        service_text = service_text.replace(" و ", " ").replace(" با ", " ").strip()
        return patterns, service_text

    def _find_service_from_text(self, text: str) -> Service | None:
        """Helper method to find the best service match from a string."""
        if not text: return None

        # Exact match on name or alias first
        for s in self._services_map.values():
            if isinstance(s, Service) and (text == s.name or text in s.aliases):
                return s

        # Fallback to fuzzy search
        calculable_services = [s for s in self._services_map.values() if isinstance(s, Service)]
        sorted_services = sorted(calculable_services, key=lambda s: len(s.name), reverse=True)
        for s in sorted_services:
            if s.name in text:
                return s
        return None

    def get_all_fixed_prices(self) -> list[FixedPrice]:
        """Provides all fixed price items for the settings dialog."""
        with self._services_engine() as session:
            return self._repo.get_all_fixed_prices(session)

    def update_fixed_prices(self, updated_prices: list[FixedPrice]):
        """Saves the updated prices to the database."""
        with self._services_engine() as session:
            self._repo.update_fixed_prices(session, updated_prices)
            session.commit()

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

    def set_items(self, items: list[InvoiceItem]):
        """
        Directly sets the internal list of invoice items.
        This is crucial for initializing the logic in an edit session.
        """
        self._current_invoice_items = items
        print(f"LOGIC UPDATE: Internal items set for editing: {self._current_invoice_items}")

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

    def update_manual_item(self, item_to_update: InvoiceItem, new_price: int, new_remarks: str) -> list[InvoiceItem]:
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
        This is the authoritative calculation engine.
        It takes an InvoiceItem with user inputs and returns a new
        InvoiceItem with all prices correctly calculated.
        """

        total_quantity = item_shell.quantity + item_shell.extra_copies
        item_shell.quantity = total_quantity

        def get_fee(key: str) -> int:
            return self._fees_map.get(key, 0)

        # Clear previous details and calculate new ones
        item_shell.dynamic_price_details = []
        translation_price_per_item = item_shell.service.base_price

        for dyn_name, dyn_quantity in item_shell.dynamic_quantities.items():
            dyn_price_obj = next((dp for dp in item_shell.service.dynamic_prices if dp.name == dyn_name), None)
            if dyn_price_obj:
                dynamic_price_total_for_item = dyn_quantity * dyn_price_obj.unit_price
                translation_price_per_item += dynamic_price_total_for_item
                # Add the detailed breakdown for DB mapping
                item_shell.dynamic_price_details.append(
                    (dyn_name, dyn_quantity, dynamic_price_total_for_item)
                )

        item_shell.translation_price = translation_price_per_item * total_quantity
        item_shell.certified_copy_price = item_shell.page_count * get_fee("کپی برابر اصل") * total_quantity
        item_shell.registration_price = get_fee("ثبت در سامانه") * total_quantity if item_shell.is_official else 0
        item_shell.judiciary_seal_price = get_fee(
            "مهر دادگستری") * total_quantity if item_shell.has_judiciary_seal else 0
        # NOTE: Foreign affairs price is often per page, not per item quantity. This logic seems correct.
        item_shell.foreign_affairs_seal_price = get_fee(
            "مهر امور خارجه") * item_shell.page_count * total_quantity if item_shell.has_foreign_affairs_seal else 0
        item_shell.extra_copy_price = item_shell.extra_copies * get_fee("نسخه اضافی")

        item_shell.total_price = (
                item_shell.translation_price +
                item_shell.certified_copy_price +
                item_shell.registration_price +
                item_shell.judiciary_seal_price +
                item_shell.foreign_affairs_seal_price +
                item_shell.extra_copy_price # Add extra copy price to the grand total
        )

        return item_shell

    # --- Private methods

    def _add_to_smart_search_history(self, text: str):
        """Saves a successful smart search entry to the database."""
        with self._services_engine() as session:
            self._repo.add_smart_search_entry(session, text)
