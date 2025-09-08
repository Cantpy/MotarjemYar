# features/Invoice_Page/wizard_host/invoice_wizard_logic.py

from PySide6.QtWidgets import QMessageBox, QWidget
from features.Invoice_Page.customer_info.customer_info_logic import CustomerStatus
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem


class InvoiceWizardLogic:
    """
    The pure Python 'brain' of the wizard. Contains all navigation and workflow logic.
    """

    # --- Public Slots for the Controller to Call ---

    def get_next_step(self, current_index: int, state_manager) -> tuple[int, dict | None]:
        """
        Calculates the next step index based on the current step and the application state.
        Returns the new index and an optional data payload for the controller.
        """
        if current_index == 0:  # From Customer Info
            # The logic to decide whether to show a dialog now returns a "command"
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
        This is pure data transformation, perfect for the logic layer.
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

    # --- Specific "Next Step" Handlers ---

    # def _handle_next_from_customer_info(self):
    #     customer_controller = self.controllers['customer']['controller']
    #     raw_data = customer_controller.get_view().get_current_data()
    #     status, customer_obj = customer_controller._logic.check_customer_status(raw_data)
    #     if status == CustomerStatus.NEW:
    #         reply = QMessageBox.question(self.view, "ذخیره مشتری",
    #                                      "این مشتری در پایگاه داده وجود ندارد. آیا مایل به ذخیره آن هستید؟",
    #                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
    #         if reply == QMessageBox.Yes:
    #             customer_controller.save_current_customer(raw_data)
    #             self._navigate_to_widget(self.controllers['documents']['widget'])
    #         elif reply == QMessageBox.No:
    #             temp_customer = customer_controller._logic._build_customer_from_data(raw_data)
    #             self.state_manager.set_customer(temp_customer)
    #             self._navigate_to_widget(self.controllers['documents']['widget'])
    #     else:
    #         self.state_manager.set_customer(customer_obj)
    #         self._navigate_to_widget(self.controllers['documents']['widget'])
    #
    # def _handle_next_from_document_selection(self):
    #     if self.state_manager.get_num_people() > 1:
    #         unpacked = self._unpack_invoice_items(self.state_manager.get_invoice_items())
    #         self.controllers['assignment']['widget'].set_data(self.state_manager.get_customer(), unpacked,
    #                                                           self.state_manager.get_assignments())
    #         self._navigate_to_widget(self.controllers['assignment']['widget'])
    #     else:
    #         self.state_manager.auto_assign_for_single_person()
    #         self.controllers['details']['controller'].prepare_and_display_data(self.state_manager.get_customer(),
    #                                                                            self.state_manager.get_invoice_items())
    #         self._navigate_to_widget(self.controllers['details']['widget'])
    #
    # def _handle_next_from_assignment(self):
    #     self.controllers['details']['controller'].prepare_and_display_data(self.state_manager.get_customer(),
    #                                                                        self.state_manager.get_invoice_items())
    #     self._navigate_to_widget(self.controllers['details']['widget'])
    #
    # def _handle_next_from_invoice_details(self):
    #     self.controllers['preview']['controller'].prepare_and_display_data()
    #     self._navigate_to_widget(self.controllers['preview']['widget'])
    #
    # def _handle_prev_from_invoice_details(self):
    #     """Logic for going back from the invoice details page."""
    #     next_widget_key = 'assignment' if self.state_manager.get_num_people() > 1 else 'documents'
    #     self._navigate_to_widget(self.controllers[next_widget_key]['widget'])
    #
    # # --- Navigation and Data Helpers ---
    #
    # def _navigate_to_widget(self, widget: QWidget):
    #     index = self.stacked_widget.indexOf(widget)
    #     if index != -1:
    #         self.view.set_current_step(index)
    #
    # def _navigate_by_offset(self, offset: int):
    #     current_index = self.stacked_widget.currentIndex()
    #     new_index = current_index + offset
    #     self.view.set_current_step(new_index)
    #
    # def _unpack_invoice_items(self, items: list[InvoiceItem]) -> list[InvoiceItem]:
    #     """
    #     Unpacks items with quantity > 1 into individual items, each with a new unique ID.
    #     """
    #     unpacked_list = []
    #     for item in items:
    #         # We use the ORIGINAL quantity from the calculation dialog here
    #         original_quantity = item.quantity
    #
    #         if original_quantity > 1 and item.service.type != "خدمات دیگر":
    #             # The total price was for all quantities, so divide it.
    #             price_per_item = item.total_price // original_quantity
    #
    #             for _ in range(original_quantity):
    #                 new_item = item.clone()  # clone() gives it a new unique_id
    #                 new_item.quantity = 1
    #                 new_item.total_price = price_per_item
    #                 unpacked_list.append(new_item)
    #         else:
    #             # Keep items with quantity 1 or "Other Services" as they are
    #             unpacked_list.append(item)
    #     return unpacked_list
