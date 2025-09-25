# features/Invoice_Page/wizard_host/invoice_wizard_controller.py

from PySide6.QtCore import QObject

from features.Invoice_Page.wizard_host.invoice_wizard_view import InvoiceWizardWidget
from features.Invoice_Page.wizard_host.invoice_page_wizard_logic import InvoiceWizardLogic
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

# Import all your feature models
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem

from shared import show_question_message_box, show_error_message_box, show_information_message_box


class InvoiceWizardController(QObject):
    def __init__(self, view: InvoiceWizardWidget,
                 logic: InvoiceWizardLogic,
                 state_manager: WorkflowStateManager,
                 sub_controllers: dict):
        super().__init__()

        self._view = view
        self._logic = logic
        self._state_manager = state_manager
        self.sub_controllers = sub_controllers

        self._connect_signals()
        self._populate_view_widgets()

        # Command the _view to set its initial state to the first page.
        self._view.set_current_step(0)

    def get_view(self) -> InvoiceWizardWidget:
        """Returns the main _view widget to be shown by the application."""
        return self._view

    def _connect_signals(self):
        """Connects high-level navigation signals."""
        self._view.next_button_clicked.connect(self._on_next_step)
        self._view.prev_button_clicked.connect(self._on_previous_step)
        # Bridge the signal from doc selection to the state manager
        doc_select_ctrl = self.sub_controllers['documents']
        doc_select_ctrl.invoice_items_changed.connect(self._state_manager.set_invoice_items)

    def _populate_view_widgets(self):
        """Adds the widgets from the sub-controllers to the stacked _view."""
        self._view.stacked_widget.addWidget(self.sub_controllers['customer'].get_view())
        self._view.stacked_widget.addWidget(self.sub_controllers['documents'].get_view())
        self._view.stacked_widget.addWidget(self.sub_controllers['assignment'])
        self._view.stacked_widget.addWidget(self.sub_controllers['details'].get_view())
        self._view.stacked_widget.addWidget(self.sub_controllers['preview'].get_view())

    def _on_next_step(self):
        """Orchestrates the entire forward navigation workflow."""
        current_index = self._view.stacked_widget.currentIndex()

        # 1. Ask the _logic layer for the next step and any necessary actions
        next_index, payload = self._logic.get_next_step(current_index, self._state_manager)

        # 2. Perform actions based on the payload BEFORE navigating
        if payload:
            action = payload.get('action')
            if action == 'CHECK_CUSTOMER_STATUS':

                if not self._handle_customer_save_confirmation():
                    return
            elif action == 'PREPARE_DETAILS':
                self.sub_controllers['details'].prepare_and_display_data(
                    self._state_manager.get_customer(), self._state_manager.get_invoice_items()
                )
            elif action == 'PREPARE_PREVIEW':
                self.sub_controllers['preview'].prepare_and_display_data()

            if 'unpacked_items' in payload:
                # Prepare the assignment widget with the unpacked items
                self.sub_controllers['assignment'].set_data(
                    self._state_manager.get_customer(), payload['unpacked_items']
                )

        # 3. Command the _view to navigate to the new index
        self._view.set_current_step(next_index)

    def _on_previous_step(self):
        current_index = self._view.stacked_widget.currentIndex()
        prev_index = self._logic.get_previous_step(current_index, self._state_manager)
        self._view.set_current_step(prev_index)

    def _handle_customer_save_confirmation(self) -> bool:
        """Handles the UI _logic for confirming if a new customer should be saved."""
        customer_ctrl = self.sub_controllers['customer']
        raw_data = customer_ctrl.get_view().get_current_data()

        # Here we need to access the sub-controller's _logic to check status. This is acceptable.
        status, customer_obj = customer_ctrl._logic.check_customer_status(raw_data)

        if status == "NEW":  # CustomerStatus.NEW
            def save_customer():
                customer_ctrl.save_current_customer(raw_data)

            def skip_saving():
                temp_customer = customer_ctrl._logic._build_customer_from_data(raw_data)
                self._state_manager.set_customer(temp_customer)

            show_question_message_box(parent=self._view,
                                      title="ذخیره مشتری",
                                      message="این مشتری در پایگاه داده وجود ندارد. آیا مایل به ذخیره آن هستید؟",
                                      button_1="بله",
                                      yes_func=save_customer,
                                      button_2="انصراف",
                                      button_3="خیر",
                                      action_func=skip_saving)
        else:
            self._state_manager.set_customer(customer_obj)

        return True  # Navigation can proceed

    def _print_customer_state(self, customer: Customer):
        print("\n--- STEP 1 COMPLETE: Customer Data ---")
        if customer:
            print(f"  Name: {customer.name}, NID: {customer.national_id}")
            print(f"  Companions: {len(customer.companions)}")
            for i, comp in enumerate(customer.companions):
                print(f"    - Companion {i + 1}: {comp.name}")
        print("--------------------------------------\n")

    def _print_items_state(self, items: list[InvoiceItem]):
        print("\n--- STEP 2 COMPLETE: Invoice Items ---")
        print(f"  Total items: {len(items)}")
        for i, item in enumerate(items):
            print(f"    - Item {i + 1}: {item.service.name}, Qty: {item.quantity}, Price: {item.total_price}")
        print("--------------------------------------\n")

    def _print_assignments_state(self, assignments: dict):
        print("\n--- STEP 3 COMPLETE: Assignments ---")
        for person, items in assignments.items():
            print(f"  Assigned to '{person}': {len(items)} item(s)")
        print("------------------------------------\n")
