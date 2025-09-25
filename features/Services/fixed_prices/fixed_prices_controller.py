# features/Services/fixed_prices/fixed_price_controller.py

from PySide6.QtCore import QObject, Signal

from features.Services.fixed_prices.fixed_prices_models import FixedPriceDTO
from features.Services.fixed_prices.fixed_prices_logic import FixedPricesLogic
from features.Services.fixed_prices.fixed_prices_view import FixedPricesView
from shared import show_error_message_box, show_information_message_box, show_question_message_box

from shared.dialogs.import_dialog import GenericInputDialog


class FixedPricesController(QObject):
    """Orchestrates the FixedPricesView and FixedPricesLogic."""
    data_changed = Signal()

    def __init__(self, view: FixedPricesView, logic: FixedPricesLogic):
        super().__init__()
        self._view = view
        self._logic = logic
        self._data_cache: list[FixedPriceDTO] = []
        self._connect_signals()

    def get_view(self) -> FixedPricesView:
        """"""
        return self._view

    def _connect_signals(self):
        """Connects _view signals to controller slots."""
        self._view.add_requested.connect(self.handle_add)
        self._view.edit_requested.connect(self.handle_edit)
        self._view.delete_requested.connect(self.handle_delete)
        self._view.bulk_delete_requested.connect(self.handle_bulk_delete)
        self._view.search_text_changed.connect(self.handle_search)

        self.data_changed.connect(self._update_view_display)

    def load_initial_data(self):
        """Loads initial data and populates the _view."""
        try:
            self._data_cache = self._logic.get_all_fixed_prices()
            self.data_changed.emit()
        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطا در بارگذاری هزینه‌های ثابت:\n{str(e)}")

    def handle_add(self):
        """Handles the workflow for adding a new service."""
        form_fields = [
            # (Label,         Key for dict, Placeholder)
            ("نام هزینه ثابت", "name", "مثال: مهر امور خارجه"),
            ("قیمت", "price", "مثال: 150000")
        ]
        dialog = GenericInputDialog("افزودن هزینه ثابت جدید", form_fields, self._view)
        if dialog.exec():
            values = dialog.get_values()
            self._perform_create_fixed_cost(values)

    def handle_edit(self, cost_id: int):
        """Handles the workflow for editing an existing fixed price."""
        # Step 1: Find the full data object from the controller's own cache.
        cost_to_edit = next((cost for cost in self._data_cache if cost.id == cost_id), None)

        if not cost_to_edit:
            show_error_message_box(self._view, "خطا", "مورد انتخاب شده برای ویرایش یافت نشد.")
            return

        # Step 2: Manually create a dictionary from the DTO to pre-fill the dialog.
        form_fields = [
            # (Label,         Key for dict, Placeholder)
            ("نام هزینه ثابت", "name", "مثال: کپی برابر اصل"),
            ("قیمت", "price", "مثال: 2250"),
        ]

        current_data_for_dialog = {
            'name': cost_to_edit.name,
            'price': str(cost_to_edit.price)
        }

        # Step 3: Create and show the dialog.
        dialog = GenericInputDialog("ویرایش هزینه ثابت", form_fields, self._view)
        dialog.set_values(current_data_for_dialog)

        if dialog.exec():
            updated_values = dialog.get_values()
            self._perform_update_fixed_cost(cost_id, updated_values)

    def handle_delete(self, service_id: int):
        """Handles the workflow for deleting a single service."""
        service = next((s for s in self._data_cache if s.id == service_id), None)
        if not service: return

        show_question_message_box(
            parent=self._view, title="حذف", message=f"آیا از حذف '{service.name}' مطمئن هستید؟",
            button_1="بله", button_2="خیر", yes_func=lambda: self._perform_delete_fixed_cost(service.id, service.name)
        )

    def handle_bulk_delete(self, service_ids: list[int]):
        """Handles the workflow for deleting multiple services."""
        count = len(service_ids)
        if count == 0: return

        show_question_message_box(
            parent=self._view, title="حذف گروهی", message=f"آیا از حذف {count} مدرک انتخاب شده مطمئن هستید؟",
            button_1="بله", button_2="خیر", yes_func=lambda: self._perform_bulk_delete_fixed_costs(service_ids)
        )

    def handle_search(self, text: str):
        """Filters the local data cache and updates the _view."""
        text = text.lower().strip()
        if not text:
            self._update_view_display()  # Show all if search is empty
            return

        filtered_data = [s for s in self._data_cache if text in s.name.lower()]
        self._view.update_display(filtered_data)

    def _update_view_display(self):
        """Pushes the current data cache to the _view."""
        self._view.update_display(self._data_cache)

    # --- Private worker methods ---

    def _perform_create_fixed_cost(self, data: dict):
        try:
            new_dto = self._logic.create_fixed_price(data)
            self._data_cache.append(new_dto)
            self._data_cache.sort(key=lambda d: (not d.is_default, d.name))
            self.data_changed.emit()
            show_information_message_box(
                self._view, "موفق", f"هزینه '{new_dto.name}' با موفقیت اضافه شد."
            )
        except Exception as e:
            show_error_message_box(self._view, "خطا در افزودن", str(e))

    def _perform_update_fixed_cost(self, cost_id: int, data: dict):
        try:
            updated_service = self._logic.update_fixed_price(cost_id, data)
            # Optimistic update: find and replace in cache
            index = next((i for i, s in enumerate(self._data_cache) if s.id == cost_id), -1)
            if index != -1:
                self._data_cache[index] = updated_service
                self._data_cache.sort(key=lambda s: s.name)
                self.data_changed.emit()
            show_information_message_box(self._view, "موفق", f"مدرک '{updated_service.name}' ویرایش شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در ویرایش", str(e))

    def _perform_delete_fixed_cost(self, cost_id: int, name: str):
        try:
            if self._logic.delete_fixed_price(cost_id):
                # Optimistic update: remove from cache
                self._data_cache = [s for s in self._data_cache if s.id != cost_id]
                self.data_changed.emit()
                show_information_message_box(self._view, "موفق", f"مدرک '{name}' حذف شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در حذف", str(e))

    def _perform_bulk_delete_fixed_costs(self, cost_ids: list[int]):
        try:
            deleted_count = self._logic.delete_multiple_prices(cost_ids)
            if deleted_count > 0:
                # Optimistic update
                id_set = set(cost_ids)
                self._data_cache = [s for s in self._data_cache if s.id not in id_set]
                self.data_changed.emit()
                show_information_message_box(self._view, "موفق", f"{deleted_count} مدرک حذف شدند.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در حذف گروهی", str(e))
