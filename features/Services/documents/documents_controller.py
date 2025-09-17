# features/Services/documents/documents_controller.py

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog, QInputDialog
from features.Services.documents.documents_dialogs import InputDialog, ImportSourceDialog, ImportSummaryDialog
from features.Services.documents.documents_logic import ServicesLogic
from features.Services.documents.documents_view import ServicesDocumentsView
from features.Services.documents.documents_models import ServicesDTO
from shared import (show_error_message_box, show_information_message_box, show_question_message_box)


class ServicesController(QObject):
    """
    Controller for services management. Orchestrates the _view and _logic.
    """
    # Signal to notify when the data cache has been updated.
    data_changed = Signal()

    def __init__(self, view: ServicesDocumentsView, logic: ServicesLogic):
        super().__init__()
        self._view = view
        self._logic = logic
        self._data_cache: list[ServicesDTO] = []
        self._connect_signals()

    def get_view(self) -> ServicesDocumentsView:
        """
        Returns the _view managed by this controller.
        """
        return self._view

    def _connect_signals(self):
        """Connect signals from the _view to the controller's handler slots."""
        # --- View Signals ---
        self._view.add_requested.connect(self.handle_add)
        self._view.edit_requested.connect(self.handle_edit)
        self._view.delete_requested.connect(self.handle_delete)
        self._view.bulk_delete_requested.connect(self.handle_bulk_delete)
        self._view.import_requested.connect(self.handle_import)
        self._view.search_text_changed.connect(self.handle_search)

        # --- Internal Controller Signals ---
        self.data_changed.connect(self._update_view_display)

    def load_initial_data(self) -> None:
        """Loads the initial set of data from the _logic layer."""
        try:
            self._data_cache = self._logic.get_all_services()
            self.data_changed.emit()
        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطا در بارگذاری مدارک:\n{str(e)}")

    def _update_view_display(self):
        """Pushes the current data cache to the _view."""
        self._view.update_display(self._data_cache)

    # --- Handlers for User Actions ---

    def handle_add(self):
        """Handles the workflow for adding a new service."""
        dialog = InputDialog("افزودن مدرک جدید", self._view)
        if dialog.exec():
            values = dialog.get_values()
            self._perform_create_service(values)

    def handle_edit(self, service_id: int):
        """Handles the workflow for editing an existing service."""
        current_data = self._view.get_current_service_data_for_edit()
        if not current_data: return

        dialog = InputDialog("ویرایش مدرک", self._view)
        dialog.set_values(current_data)

        if dialog.exec():
            updated_values = dialog.get_values()
            self._perform_update_service(service_id, updated_values)

    def handle_delete(self, service_id: int):
        """Handles the workflow for deleting a single service."""
        service = next((s for s in self._data_cache if s.id == service_id), None)
        if not service: return

        show_question_message_box(
            parent=self._view, title="حذف", message=f"آیا از حذف '{service.name}' مطمئن هستید؟",
            button_1="بله", button_2="خیر", yes_func=lambda: self._perform_delete_service(service.id, service.name)
        )

    def handle_bulk_delete(self, service_ids: list[int]):
        """Handles the workflow for deleting multiple services."""
        count = len(service_ids)
        if count == 0: return

        show_question_message_box(
            parent=self._view, title="حذف گروهی", message=f"آیا از حذف {count} مدرک انتخاب شده مطمئن هستید؟",
            button_1="بله", button_2="خیر", yes_func=lambda: self._perform_bulk_delete(service_ids)
        )

    def handle_search(self, text: str):
        """Filters the local data cache and updates the _view."""
        text = text.lower().strip()
        if not text:
            self._update_view_display()  # Show all if search is empty
            return

        filtered_data = [s for s in self._data_cache if text in s.name.lower()]
        self._view.update_display(filtered_data)

    def handle_import(self):
        """Orchestrates the entire import workflow."""
        source_dialog = ImportSourceDialog(self._view)
        if not source_dialog.exec():
            return  # User cancelled

        result = None
        if source_dialog.source == "excel":
            # Open file dialog to get the path
            file_path, _ = QFileDialog.getOpenFileName(
                self._view, "انتخاب فایل اکسل", "", "Excel Files (*.xlsx *.xls)"
            )
            if file_path:
                result = self._logic.import_from_excel(file_path)

        elif source_dialog.source == "database":
            # Open an input dialog to get the connection string
            # NOTE: In a real app, this should be more secure and user-friendly
            conn_str, ok = QInputDialog.getText(
                self._view, "اتصال به پایگاه داده", "رشته اتصال SQLAlchemy را وارد کنید:"
            )
            if ok and conn_str:
                result = self._logic.import_from_database(conn_str)

        # --- Show the summary ---
        if result:
            summary_dialog = ImportSummaryDialog(result, self._view)
            summary_dialog.exec()

            # --- IMPORTANT: Refresh the main _view with new data ---
            if result.success_count > 0:
                self.load_initial_data()

    # --- Private Worker Methods (Interacting with Logic Layer) ---

    def _perform_create_service(self, service_data: dict):
        try:
            created_service = self._logic.create_service(service_data)
            # Optimistic update: modify cache and notify _view
            self._data_cache.append(created_service)
            self._data_cache.sort(key=lambda s: s.name)  # Keep it sorted
            self.data_changed.emit()
            show_information_message_box(self._view, "موفق", f"مدرک '{created_service.name}' اضافه شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در افزودن", str(e))

    def _perform_update_service(self, service_id: int, service_data: dict):
        try:
            updated_service = self._logic.update_service(service_id, service_data)
            # Optimistic update: find and replace in cache
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
                # Optimistic update: remove from cache
                self._data_cache = [s for s in self._data_cache if s.id != service_id]
                self.data_changed.emit()
                show_information_message_box(self._view, "موفق", f"مدرک '{service_name}' حذف شد.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در حذف", str(e))

    def _perform_bulk_delete(self, service_ids: list[int]):
        try:
            deleted_count = self._logic.delete_multiple_services(service_ids)
            if deleted_count > 0:
                # Optimistic update
                id_set = set(service_ids)
                self._data_cache = [s for s in self._data_cache if s.id not in id_set]
                self.data_changed.emit()
                show_information_message_box(self._view, "موفق", f"{deleted_count} مدرک حذف شدند.")
        except Exception as e:
            show_error_message_box(self._view, "خطا در حذف گروهی", str(e))


# class ServicesController(QObject):
#     """Controller for services management"""
#     data_changed = Signal()
#
#     def __init__(self, _view: ServicesDocumentsView, _logic: ServicesLogic):
#         super().__init__()
#         self._view = _view
#         self._logic = _logic
#         self._data_cache: list[ServicesDTO] = []
#         self.connect_signals()
#
#     def get_view(self) -> ServicesDocumentsView:
#         """
#
#         """
#         return self._view
#
#     def connect_signals(self):
#         """
#
#         """
#         self._view.add_requested.connect(self.handle_add)
#         self._view.edit_requested.connect(self.handle_edit)
#         self._view.search_text_changed.connect(self.handle_search)
#         self.data_changed.connect(self._update_view_display)
#
#     def load_services(self) -> list[ServicesDTO]:
#         """Load all services, update cache, and emit data_changed signal."""
#         try:
#             self._data_cache = self._logic.get_all_services()
#             self.data_changed.emit()
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در بارگذاری مدارک:\n{str(e)}")
#             return []
#
#     def get_cached_data(self) -> list[ServicesDTO]:
#         """Get cached data without database call"""
#         return self._data_cache
#
#     def create_service(self, service_data: dict[str, Any]) -> bool:
#         """Create new service"""
#         try:
#             created_service = self._logic.create_service(service_data)
#
#             # --- Optimistic Update ---
#             self._data_cache.append(created_service)  # Add to the cache
#             self.data_changed.emit()
#
#             show_information_message_box(self._view, "موفق",
#                                          f"مدرک '{created_service.name}' با موفقیت اضافه شد!")
#             return True
#         except ValueError as e:
#             show_warning_message_box(self._view, "خطا", str(e))
#             return False
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در افزودن مدرک:\n{str(e)}")
#             return False
#
#     def update_service(self, service_id: int, service_data: dict[str, Any]) -> bool:
#         """Update existing service"""
#         try:
#             updated_service = self._logic.update_service(service_id, service_data)
#             if updated_service:
#                 self.load_services()  # Refresh data
#                 show_information_message_box(self._view, "موفق",
#                                              f"مدرک '{updated_service.name}' با موفقیت ویرایش شد!")
#                 return True
#             else:
#                 show_warning_message_box(self._view, "خطا", "مدرک مورد نظر یافت نشد")
#                 return False
#         except ValueError as e:
#             show_warning_message_box(self._view, "خطا", str(e))
#             return False
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در ویرایش مدرک:\n{str(e)}")
#             return False
#
#     def handle_add(self):
#         # All the _logic from the old _show_add_dialog moves here
#         dialog = InputDialog("افزودن مدرک جدید", self._view)
#         if dialog.exec() == QDialog.Accepted:
#             values = dialog.get_values()
#             self.create_service(values)
#
#     def handle_edit(self, service_id: int):
#         """The controller asks the _view for the current data to pre-fill the dialog."""
#         # This avoids an unnecessary database call.
#         current_data = self._view.get_current_service_data_for_edit()
#         if not current_data:
#             return  # Should not happen if the UI is in a consistent state
#
#         dialog = InputDialog("ویرایش مدرک", self._view)
#         dialog.set_values(current_data)
#
#         if dialog.exec() == QDialog.Accepted:
#             updated_values = dialog.get_values()
#             self.update_service(service_id, updated_values)
#
#     def handle_search(self, text: str) -> None:
#         """Filters the cached data and updates the _view display."""
#         text = text.lower().strip()
#         if not text:
#             # If search is cleared, show all data
#             self._update_view_display()
#             return
#
#         # Filter the cache in memory (very fast)
#         filtered_data = [
#             service for service in self._data_cache
#             if text in service.name.lower()
#         ]
#
#         # Push the filtered list to the _view
#         self._view.update_display(filtered_data)
#
#     def handle_delete(self, service_id: int):
#         # Find the service name from the cache for a better message
#         service_to_delete = next((s for s in self._data_cache if s.id == service_id), None)
#         if not service_to_delete: return
#
#         # The controller asks for confirmation
#         show_question_message_box(
#             parent=self._view, title="حذف",
#             message=f"آیا مطمئن هستید که می‌خواهید '{service_to_delete.name}' را حذف کنید؟",
#             button_1="بله", yes_func=lambda: self._perform_delete_service(service_id, service_to_delete.name),
#             button_2="خیر"
#         )
#
#     def delete_service(self, service_id: int, service_name: str = "") -> bool:
#         """Delete single service"""
#         try:
#             if self._logic.delete_service(service_id):
#                 self.load_services()  # Refresh data
#                 show_information_message_box(self._view, "موفق",
#                                              f"مدرک '{service_name}' با موفقیت حذف شد!")
#                 return True
#             else:
#                 show_warning_message_box(self._view, "خطا", "مدرک مورد نظر یافت نشد")
#                 return False
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در حذف مدرک:\n{str(e)}")
#             return False
#
#     def delete_multiple_services(self, service_ids: list[int]) -> bool:
#         """Delete multiple services"""
#         try:
#             deleted_count = self._logic.delete_multiple_services(service_ids)
#             if deleted_count > 0:
#                 self.load_services()  # Refresh data
#                 show_information_message_box(self._view, "موفق",
#                                              f"{deleted_count} مدرک با موفقیت حذف شدند!")
#                 return True
#             else:
#                 show_warning_message_box(self._view, "خطا", "هیچ مدرکی حذف نشد")
#                 return False
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در حذف مدارک:\n{str(e)}")
#             return False
#
#     def search_services(self, search_term: str) -> list[ServicesDTO]:
#         """Search services"""
#         try:
#             return self._logic.search_services(search_term)
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در جستجو:\n{str(e)}")
#             return []
#
#     def import_from_excel(self, confirmation_callback: Callable = None) -> bool:
#         """Import services from Excel with confirmation"""
#         try:
#             if confirmation_callback and not confirmation_callback():
#                 return False
#
#             imported_count, errors = self._logic.import_from_excel()
#
#             if errors:
#                 error_msg = f"تعداد {imported_count} مدرک وارد شد با خطاهای زیر:\n" + "\n".join(errors[:5])
#                 if len(errors) > 5:
#                     error_msg += f"\n... و {len(errors) - 5} خطای دیگر"
#                 show_warning_message_box(self._view, "هشدار", error_msg)
#             else:
#                 show_information_message_box(self._view, "موفق",
#                                              f"تعداد {imported_count} مدرک با موفقیت از اکسل وارد شد!")
#
#             self.load_services()  # Refresh data
#             return True
#
#         except ValueError as e:
#             show_warning_message_box(self._view, "خطا", str(e))
#             return False
#         except Exception as e:
#             show_error_message_box(self._view, "خطا", f"خطا در بارگذاری از اکسل:\n{str(e)}")
#             return False
