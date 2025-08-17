# document_selection/controller.py
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_logic import DocumentSelectionLogic
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_view import DocumentSelectionWidget
from features.Invoice_Page_GAS.workflow_manager.invoice_page_state_manager import WorkflowStateManager


class DocumentSelectionController:
    def __init__(self, state_manager: WorkflowStateManager):
        # The controller creates and owns the logic (presenter) and the view
        self._state_manager = state_manager
        self._logic = DocumentSelectionLogic()
        self._view = DocumentSelectionWidget(self._state_manager)
        self._view.populate_completer(self._logic.get_all_service_names())

        # 2. Connect signals from the View (user actions) to slots in the Logic (processing)
        self._view.add_button_clicked.connect(self._logic.add_service_by_name)
        self._view.delete_button_clicked.connect(self._logic.delete_item_at_index)
        self._view.clear_button_clicked.connect(self._logic.clear_all_items)
        self._view.manual_item_updated.connect(self._logic.update_manual_item)
        self._view.edit_button_clicked.connect(self._logic.edit_item_at_index)
        self._view.delete_button_clicked.connect(self._logic.delete_item_at_index)

        # 3. Connect signals from the Logic (data changes) to slots in the View (UI updates)
        self._logic.invoice_list_updated.connect(self._state_manager.set_invoice_items)
        self._logic.invoice_list_updated.connect(self._view.update_table_display)
        self._logic.operation_successful.connect(self._view.clear_service_input)

    def get_widget(self) -> DocumentSelectionWidget:
        """Exposes the view widget to the outside world (e.g., a main window)."""
        return self._view


