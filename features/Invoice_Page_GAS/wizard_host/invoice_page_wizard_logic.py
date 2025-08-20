# wizard_host/invoice_wizard_logic.py
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox, QWidget
from features.Invoice_Page_GAS.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import CustomerStatus
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem


class MainWindowLogic(QObject):
    """
    The 'brain' of the wizard. Contains all navigation and workflow logic.
    It knows nothing about UI elements, only about the controllers and state.
    """

    def __init__(self, view, state_manager, controllers):
        super().__init__()
        self.view = view
        self.state_manager = state_manager
        self.controllers = controllers
        self.stacked_widget = self.view.stacked_widget

        self.next_step_handlers = {
            self.controllers['customer']['widget']: self._handle_next_from_customer_info,
            self.controllers['documents']['widget']: self._handle_next_from_document_selection,
            self.controllers['assignment']['widget']: self._handle_next_from_assignment,
            self.controllers['details']['widget']: self._handle_next_from_invoice_details
        }
        self.prev_step_handlers = {
            self.controllers['details']['widget']: self._handle_prev_from_invoice_details
        }

    # --- Public Slots for the Controller to Call ---

    def go_to_next_step(self):
        """The main forward navigation router."""
        current_widget = self.stacked_widget.currentWidget()

        # This is a dispatch pattern using if/elif, which is perfectly clear here.
        if current_widget is self.controllers['customer']['widget']:
            self._handle_next_from_customer_info()
        elif current_widget is self.controllers['documents']['widget']:
            self._handle_next_from_document_selection()
        elif current_widget is self.controllers['assignment']['widget']:
            self._handle_next_from_assignment()
        elif current_widget is self.controllers['details']['widget']:
            self._handle_next_from_invoice_details()
        else:
            self._navigate_by_offset(1)

    def go_to_previous_step(self):
        """The main backward navigation router."""
        current_widget = self.stacked_widget.currentWidget()
        if current_widget is self.controllers['details']['widget'] and self.state_manager.get_num_people() <= 1:
            self._navigate_to_widget(self.controllers['documents']['widget'])
        else:
            self._navigate_by_offset(-1)

    # --- Specific "Next Step" Handlers ---

    def _handle_next_from_customer_info(self):
        customer_controller = self.controllers['customer']['controller']
        raw_data = customer_controller.get_widget().get_current_data()
        status, customer_obj = customer_controller._logic.check_customer_status(raw_data)
        if status == CustomerStatus.NEW:
            reply = QMessageBox.question(self.view, "ذخیره مشتری",
                                         "این مشتری در پایگاه داده وجود ندارد. آیا مایل به ذخیره آن هستید؟",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                customer_controller.save_current_customer(raw_data)
                self._navigate_to_widget(self.controllers['documents']['widget'])
            elif reply == QMessageBox.No:
                temp_customer = customer_controller._logic._build_customer_from_data(raw_data)
                self.state_manager.set_customer(temp_customer)
                self._navigate_to_widget(self.controllers['documents']['widget'])
        else:
            self.state_manager.set_customer(customer_obj)
            self._navigate_to_widget(self.controllers['documents']['widget'])

    def _handle_next_from_document_selection(self):
        if self.state_manager.get_num_people() > 1:
            unpacked = self._unpack_invoice_items(self.state_manager.get_invoice_items())
            self.controllers['assignment']['widget'].set_data(self.state_manager.get_customer(), unpacked,
                                                              self.state_manager.get_assignments())
            self._navigate_to_widget(self.controllers['assignment']['widget'])
        else:
            self.state_manager.auto_assign_for_single_person()
            self.controllers['details']['controller'].prepare_and_display_data(self.state_manager.get_customer(),
                                                                               self.state_manager.get_invoice_items())
            self._navigate_to_widget(self.controllers['details']['widget'])

    def _handle_next_from_assignment(self):
        self.controllers['details']['controller'].prepare_and_display_data(self.state_manager.get_customer(),
                                                                           self.state_manager.get_invoice_items())
        self._navigate_to_widget(self.controllers['details']['widget'])

    def _handle_next_from_invoice_details(self):
        self.controllers['preview']['controller'].prepare_and_display_data()
        self._navigate_to_widget(self.controllers['preview']['widget'])

    def _handle_prev_from_invoice_details(self):
        """Logic for going back from the invoice details page."""
        next_widget_key = 'assignment' if self.state_manager.get_num_people() > 1 else 'documents'
        self._navigate_to_widget(self.controllers[next_widget_key]['widget'])

    # --- Navigation and Data Helpers ---

    def _navigate_to_widget(self, widget: QWidget):
        index = self.stacked_widget.indexOf(widget)
        if index != -1:
            self.view.set_current_step(index)

    def _navigate_by_offset(self, offset: int):
        current_index = self.stacked_widget.currentIndex()
        new_index = current_index + offset
        self.view.set_current_step(new_index)

    def _unpack_invoice_items(self, items: list[InvoiceItem]) -> list[InvoiceItem]:
        """
        Unpacks items with quantity > 1 into individual items, each with a new unique ID.
        """
        unpacked_list = []
        for item in items:
            # We use the ORIGINAL quantity from the calculation dialog here
            original_quantity = item.quantity

            if original_quantity > 1 and item.service.type != "خدمات دیگر":
                # The total price was for all quantities, so divide it.
                price_per_item = item.total_price // original_quantity

                for _ in range(original_quantity):
                    new_item = item.clone()  # clone() gives it a new unique_id
                    new_item.quantity = 1
                    new_item.total_price = price_per_item
                    unpacked_list.append(new_item)
            else:
                # Keep items with quantity 1 or "Other Services" as they are
                unpacked_list.append(item)
        return unpacked_list
