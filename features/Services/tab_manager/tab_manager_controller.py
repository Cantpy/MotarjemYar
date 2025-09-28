# features/Services/tab_manager/tab_manager_controller.py

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog

from shared.dialogs.import_dialog import ImportSummaryDialog
from shared import show_error_message_box, show_information_message_box


class ServicesManagementController(QObject):
    """
    Manages the ServicesManagementView and coordinates the sub-controllers for each tab.
    """

    def __init__(self,
                 view: "ServicesManagementView",
                 import_logic: "ExcelImportLogic",
                 documents_controller,
                 other_services_controller):
        super().__init__()
        self._view = view

        # Store the sub-controllers as dependencies
        self._documents_controller = documents_controller
        self._other_services_controller = other_services_controller
        self._import_logic = import_logic

        self._connect_signals()

    def get_view(self) -> "ServicesManagementView":
        """Provides the assembled _view, adhering to the application pattern."""
        return self._view

    def _connect_signals(self):
        """Connects the container _view's signals to this controller's slots."""
        self._view.refresh_all_requested.connect(self.handle_refresh_all)
        self._view.import_requested.connect(self.handle_import)

    def handle_refresh_all(self):
        """Orchestrates a refresh action across all sub-modules."""
        # This controller tells each sub-controller to reload its data.
        self._documents_controller.load_initial_data()
        self._other_services_controller.load_initial_data()

    def handle_import(self):
        """
        Orchestrates the entire multi-sheet Excel import workflow, providing
        detailed feedback to the user and refreshing the UI on success.
        """
        # --- Step 1: Get the file path from the user ---
        file_path, _ = QFileDialog.getOpenFileName(
            self._view,
            "انتخاب فایل اکسل خدمات",
            "",
            "Excel Files (*.xlsx *.xls)"
        )

        # If the user cancels the dialog, do nothing.
        if not file_path:
            return

        # --- Step 2: Call the logic layer to perform the import ---
        try:
            # The logic layer does all the heavy lifting and returns a dictionary of results.
            results = self._import_logic.import_from_excel_file(file_path)

            # --- Step 3: Show the user the detailed summary dialog ---
            # This is a crucial feedback step.
            if results:
                summary_dialog = ImportSummaryDialog(results, self._view)
                summary_dialog.exec()
            else:
                # This case might happen if the Excel file was empty or had no valid sheets
                show_information_message_box(
                    self._view,
                    "اطلاعات",
                    "فایل اکسل پردازش شد، اما هیچ داده‌ای برای بارگذاری یافت نشد."
                )
                return

            # --- Step 4: Refresh the relevant UI tabs on success ---
            # This ensures the UI is synchronized with the new database state.
            print("Refreshing tabs after successful import...")

            if results.get('documents') and results['documents'].success_count > 0:
                print("-> Refreshing Documents tab...")
                self._documents_controller.load_initial_data()

            if results.get('other_services') and results['other_services'].success_count > 0:
                print("-> Refreshing Other Services tab...")
                self._other_services_controller.load_initial_data()

        except Exception as e:
            # --- Step 5: Handle any unexpected errors gracefully ---
            # This will catch errors from the logic layer, like if the file
            # is unreadable or a major database error occurs.
            import traceback
            traceback.print_exc()  # Log the full error for debugging

            show_error_message_box(
                self._view,
                "خطای حیاتی در بارگذاری",
                f"یک خطای پیش‌بینی نشده در هنگام پردازش فایل رخ داد:\n\n{e}"
            )
