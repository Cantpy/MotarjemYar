# features/Invoice_Page/wizard_host/invoice_wizard_logic.py

from PySide6.QtWidgets import QMessageBox, QWidget
from features.Invoice_Page.customer_info.customer_info_logic import CustomerStatus
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem


class InvoiceWizardLogic:
    """
    The pure Python 'brain' of the wizard. Contains all navigation and workflow _logic.
    """

    # --- Public Slots for the Controller to Call ---

    def get_next_step(self, current_index: int, state_manager) -> tuple[int, dict | None]:
        """
        Calculates the next step index based on the current step and the application state.
        Returns the new index and an optional data payload for the controller.
        """
        if current_index == 0:  # From Customer Info
            # The _logic to decide whether to show a dialog now returns a "command"
            # as part of the data payload.
            return 1, {'action': 'CHECK_CUSTOMER_STATUS'}

        elif current_index == 1:  # From Document Selection
            if state_manager.get_num_people() > 1:
                unpacked_items = self._unpack_invoice_items(state_manager.get_invoice_items())
                return 2, {'unpacked_items': unpacked_items}  # Go to Assignment
            else:
                state_manager.auto_assign_for_single_person()
                return 3, {'action': 'PREPARE_DETAILS'}  # Skip to Details

        elif current_index == 2:  # From Assignment
            return 3, {'action': 'PREPARE_DETAILS'}  # Go to Details

        elif current_index == 3:  # From Invoice Details
            return 4, {'action': 'PREPARE_PREVIEW'}  # Go to Preview

        # Default case
        return min(current_index + 1, 4)

    def get_previous_step(self, current_index: int, state_manager) -> int:
        """Calculates the previous step index."""
        if current_index == 3:  # From Invoice Details
            # Skip back over assignment if there's only one person
            return 1 if state_manager.get_num_people() <= 1 else 2

        # Default case
        return max(current_index - 1, 0)

    def _unpack_invoice_items(self, items: list) -> list:  # list[InvoiceItem]
        """
        Unpacks items with quantity > 1 into individual items.
        This is pure data transformation, perfect for the _logic layer.
        """
        unpacked_list = []
        for item in items:
            original_quantity = item.quantity
            if original_quantity > 1 and item.service.type != "خدمات دیگر":
                price_per_item = item.total_price // original_quantity
                for _ in range(original_quantity):
                    new_item = item.clone()
                    new_item.quantity = 1
                    new_item.total_price = price_per_item
                    unpacked_list.append(new_item)
            else:
                unpacked_list.append(item)
        return unpacked_list
