# features/Services/documents/documents_controller.py

from PySide6.QtCore import QObject, Signal
from features.Services.documents.documents_logic import ServicesLogic
from features.Services.documents.documents_view import ServicesDocumentsView
from features.Services.documents.documents_models import ServicesDTO
from features.Services.documents.documents_alias_dialog import ServicePropertiesDialog
from shared import show_error_message_box, show_information_message_box, show_question_message_box
from shared.dialogs.import_dialog import GenericInputDialog


class ServicesController(QObject):
    """
    Controller for services management. Orchestrates the _view and _logic.
    """
    data_changed = Signal()

    def __init__(self, view: ServicesDocumentsView, logic: ServicesLogic):
        super().__init__()
        self._view = view
        self._logic = logic
        self._data_cache: list[ServicesDTO] = []
        print(f'data cache initialized: {self._data_cache}')
        self._connect_signals()

    def get_view(self) -> ServicesDocumentsView:
        return self._view

    def _connect_signals(self):
        """Connect signals from the _view to the controller's handler slots."""
        self._view.add_requested.connect(self.handle_add)
        self._view.edit_requested.connect(self.handle_edit)
        self._view.delete_requested.connect(self.handle_delete)
        self._view.bulk_delete_requested.connect(self.handle_bulk_delete)
        self._view.aliases_requested.connect(self.handle_manage_aliases)
        self._view.search_text_changed.connect(self.handle_search)

        # FIX: The slot for data_changed now correctly refreshes the view
        # without causing recursion.
        self.data_changed.connect(self._on_data_changed)

    def load_initial_data(self) -> None:
        """Loads the initial set of data and clears the search bar."""
        try:
            self._data_cache = self._logic.get_all_services()
            # This clears the search bar in the UI
            self._view.set_search_text("")
            # This emits the signal that will display the full, unfiltered list
            self.data_changed.emit()
        except Exception as e:
            print(f"Error loading services: {e}")
            show_error_message_box(self._view, "خطا", f"خطا در بارگذاری مدارک:\n{str(e)}")

    # --- Handlers for User Actions ---

    def handle_search(self, text: str):
        """
        Handles the user typing in the search bar. It simply calls the main
        filtering method. This is the entry point for UI-driven searches.
        """
        self._filter_and_update_view(text)

    # ... (handle_add, handle_edit, handle_delete, handle_bulk_delete, handle_manage_aliases remain unchanged) ...
    def handle_add(self):
        """Handles adding a new service document."""
        form_fields = [
            ("نام مدرک", "name", "مثال: شناسنامه"),
            ("هزینه پایه", "base_price", "مثال: 150000"),
            ("نام متغیر ۱", "fee_1_name", "مثال: تعداد سطر"),
            ("هزینه متغیر ۱", "fee_1_price", "مثال: 5000"),
            ("نام متغیر ۲", "fee_2_name", "مثال: تعداد صفحه"),
            ("هزینه متغیر ۲", "fee_2_price", "مثال: 25000"),
        ]

        dialog = GenericInputDialog("افزودن مدرک جدید", fields=form_fields, parent=self._view)

        if dialog.exec():
            dialog_values = dialog.get_values()

            logic_data = {
                'name': dialog_values.get('name'),
                'base_price': dialog_values.get('base_price'),
                'dynamic_prices': []
            }

            if dialog_values.get('fee_1_name') and dialog_values.get('fee_1_price'):
                logic_data['dynamic_prices'].append({
                    'name': dialog_values['fee_1_name'],
                    'price': dialog_values['fee_1_price']
                })

            if dialog_values.get('fee_2_name') and dialog_values.get('fee_2_price'):
                logic_data['dynamic_prices'].append({
                    'name': dialog_values['fee_2_name'],
                    'price': dialog_values['fee_2_price']
                })
            self._perform_create_service(logic_data)

    def handle_edit(self, service_id: int):
        service_to_edit = next((s for s in self._data_cache if s.id == service_id), None)
        if not service_to_edit:
            show_error_message_box(self._view, "خطا", "مدرک انتخاب شده یافت نشد.")
            return

        form_fields = [
            ("نام مدرک", "name", "مثال: شناسنامه"),
            ("هزینه پایه", "base_price", "مثال: 150000"),
            ("نام متغیر ۱", "fee_1_name", "مثال: تعداد سطر"),
            ("هزینه متغیر ۱", "fee_1_price", "مثال: 5000"),
            ("نام متغیر ۲", "fee_2_name", "مثال: تعداد صفحه"),
            ("هزینه متغیر ۲", "fee_2_price", "مثال: 25000"),
        ]

        dialog_data = {
            'name': service_to_edit.name,
            'base_price': str(service_to_edit.base_price)
        }
        if len(service_to_edit.dynamic_prices) > 0:
            dialog_data['fee_1_name'] = service_to_edit.dynamic_prices[0].name
            dialog_data['fee_1_price'] = str(service_to_edit.dynamic_prices[0].unit_price)
        if len(service_to_edit.dynamic_prices) > 1:
            dialog_data['fee_2_name'] = service_to_edit.dynamic_prices[1].name
            dialog_data['fee_2_price'] = str(service_to_edit.dynamic_prices[1].unit_price)

        dialog = GenericInputDialog("ویرایش مدرک", fields=form_fields, parent=self._view)
        dialog.set_values(dialog_data)

        if dialog.exec():
            updated_dialog_values = dialog.get_values()

            logic_data = {
                'name': updated_dialog_values.get('name', ''),
                'base_price': updated_dialog_values.get('base_price', '0'),
                'dynamic_prices': []
            }
            if updated_dialog_values.get('fee_1_name') and updated_dialog_values.get('fee_1_price'):
                logic_data['dynamic_prices'].append({
                    'name': updated_dialog_values['fee_1_name'],
                    'price': updated_dialog_values['fee_1_price']
                })
            if updated_dialog_values.get('fee_2_name') and updated_dialog_values.get('fee_2_price'):
                logic_data['dynamic_prices'].append({
                    'name': updated_dialog_values['fee_2_name'],
                    'price': updated_dialog_values['fee_2_price']
                })
            self._perform_update_service(service_id, logic_data)

    def handle_delete(self, service_id: int):
        service = next((s for s in self._data_cache if s.id == service_id), None)
        if not service: return

        show_question_message_box(
            parent=self._view, title="حذف", message=f"آیا از حذف '{service.name}' مطمئن هستید؟",
            button_1="بله", button_2="خیر", yes_func=lambda: self._perform_delete_service(service.id, service.name)
        )

    def handle_bulk_delete(self, service_ids: list[int]):
        count = len(service_ids)
        if count == 0: return

        show_question_message_box(
            parent=self._view, title="حذف گروهی", message=f"آیا از حذف {count} مدرک انتخاب شده مطمئن هستید؟",
            button_1="بله", button_2="خیر", yes_func=lambda: self._perform_bulk_delete(service_ids)
        )

    def handle_manage_aliases(self, service_id: int):
        try:
            service_dto = self._logic.get_service_with_aliases(service_id)
            if not service_dto:
                show_error_message_box(self._view, "خطا", "مدرک مورد نظر یافت نشد.")
                return

            dynamic_prices_for_dialog = [
                {"id": dp.id, "name": dp.name, "aliases": dp.aliases}
                for dp in service_dto.dynamic_prices
            ]

            dialog = ServicePropertiesDialog(
                service_name=service_dto.name,
                service_aliases=service_dto.aliases,
                default_page_count=service_dto.default_page_count,
                dynamic_prices_data=dynamic_prices_for_dialog,
                parent=self._view
            )

            if dialog.exec():
                updated_data = dialog.get_updated_data()
                self._perform_update_properties(service_id, updated_data)

        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطا در باز کردن پنجره جزئیات:\n{e}")

    # --- Private Worker Methods & Slots ---
    def _on_data_changed(self):
        """
        Slot connected to the data_changed signal. This is the entry point for
        data-driven view refreshes (e.g., after an add, edit, or delete).
        It re-applies the current filter to the updated data cache.
        """
        current_search_text = self._view.search_bar.text()
        self._filter_and_update_view(current_search_text)

    def _filter_and_update_view(self, text: str):
        """
        NEW METHOD: This is the single source of truth for filtering data
        and pushing it to the view.
        """
        text = text.lower().strip()
        if not text:
            # If search is empty, display the entire cache
            print(f"Displaying full data cache with {self._data_cache}")
            self._view.update_display(self._data_cache)
            return

        # Otherwise, filter the data and display the result
        filtered_data = [s for s in self._data_cache if text in s.name.lower()]
        self._view.update_display(filtered_data)
        print(f"Filtered data with search '{text}': {filtered_data}")

    def _perform_create_service(self, service_data: dict):
        try:
            created_service = self._logic.create_service(service_data)
            self._data_cache.append(created_service)
            self._data_cache.sort(key=lambda s: s.name)
            self.data_changed.emit()
            show_information_message_box(self._view, "موفق", f"مدرک '{created_service.name}' اضافه شد.")
        except Exception as e:
            print(f"error adding the service: {e}")
            show_error_message_box(self._view, "خطا در افزودن", str(e))

    def _perform_update_service(self, service_id: int, service_data: dict):
        try:
            updated_service = self._logic.update_service(service_id, service_data)
            index = next((i for i, s in enumerate(self._data_cache) if s.id == service_id), -1)
            if index != -1:
                self._data_cache[index] = updated_service
                self._data_cache.sort(key=lambda s: s.name)
                self.data_changed.emit()
            show_information_message_box(self._view, "موفق", f"مدرک '{updated_service.name}' ویرایش شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در ویرایش", str(e))

    def _perform_delete_service(self, service_id: int, service_name: str):
        try:
            if self._logic.delete_service(service_id):
                self._data_cache = [s for s in self._data_cache if s.id != service_id]
                self.data_changed.emit()
                show_information_message_box(self._view, "موفق", f"مدرک '{service_name}' حذف شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در حذف", str(e))

    def _perform_bulk_delete(self, service_ids: list[int]):
        try:
            deleted_count = self._logic.delete_multiple_services(service_ids)
            if deleted_count > 0:
                id_set = set(service_ids)
                self._data_cache = [s for s in self._data_cache if s.id not in id_set]
                self.data_changed.emit()
                show_information_message_box(self._view, "موفق", f"{deleted_count} مدرک حذف شدند.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در حذف گروهی", str(e))

    def _perform_update_properties(self, service_id: int, properties_data: dict):
        try:
            updated_service = self._logic.update_service_properties(service_id, properties_data)
            if updated_service:
                index = next((i for i, s in enumerate(self._data_cache) if s.id == service_id), -1)
                if index != -1:
                    self._data_cache[index] = updated_service
                    # Emit the signal to trigger a filtered refresh
                    self.data_changed.emit()
                show_information_message_box(self._view, "موفق",
                                             f"جزئیات مدرک '{updated_service.name}' بروزرسانی شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطا در بروزرسانی جزئیات:\n{e}")
