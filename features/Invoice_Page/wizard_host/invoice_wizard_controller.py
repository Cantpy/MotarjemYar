# features/Invoice_Page/wizard_host/invoice_wizard_controller.py

from PySide6.QtCore import QObject

from features.Invoice_Page.wizard_host.invoice_wizard_view import InvoiceWizardWidget
from features.Invoice_Page.wizard_host.invoice_page_wizard_logic import InvoiceWizardLogic
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager

# Import all your feature models
from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem, Service

from shared.orm_models.invoices_models import InvoiceData, InvoiceItemData
from shared import show_question_message_box, show_warning_message_box


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

        self._is_edit_mode = False
        self._editing_invoice_number = None

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

        preview_view = self.sub_controllers['preview'].get_view()
        preview_view.finish_clicked.connect(self.finish_and_reset)

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
        next_index, payload = self._logic.get_next_step(current_index, self._state_manager)

        if payload:
            action = payload.get('action')
            if action == 'CHECK_CUSTOMER_STATUS':
                if not self._handle_customer_save_confirmation():
                    return

            # --- MODIFICATION: Differentiate between new and edit workflows ---
            elif action == 'PREPARE_DETAILS':
                details_controller = self.sub_controllers['details']
                customer = self._state_manager.get_customer()
                items = self._state_manager.get_invoice_items()

                if self._is_edit_mode:
                    # If editing, use the original data to pre-fill everything
                    original_invoice = self._state_manager.get_original_invoice_for_edit()
                    details_controller.prepare_and_display_data_for_edit(customer, items, original_invoice)
                    print(f"WORKFLOW: items for the invoice details: {items}")
                else:
                    # If new, use the standard method
                    details_controller.prepare_and_display_data(customer, items)

            elif action == 'PREPARE_PREVIEW':
                is_valid, error_message = self.sub_controllers['details'].validate()
                if not is_valid:
                    show_warning_message_box(self._view, "خطا در اطلاعات فاکتور", error_message)
                    return

                if self._is_edit_mode:
                    details = self._state_manager.get_invoice_details()
                    edit_message = "\n* این فاکتور ویرایش شده است"
                    if edit_message not in details.remarks:
                        details.remarks += edit_message
                    self._state_manager.set_invoice_details(details)
                    print(f"WORKFLOW: details for invoice preview: {details}")

                self.sub_controllers['preview'].prepare_and_display_data()

            if 'unpacked_items' in payload:
                self.sub_controllers['assignment'].set_data(
                    self._state_manager.get_customer(), payload['unpacked_items']
                )

        self._view.set_current_step(next_index)

    def _on_previous_step(self):
        current_index = self._view.stacked_widget.currentIndex()
        prev_index = self._logic.get_previous_step(current_index, self._state_manager)
        self._view.set_current_step(prev_index)

    def _handle_customer_save_confirmation(self) -> bool:
        customer_ctrl = self.sub_controllers['customer']
        raw_data = customer_ctrl.get_view().get_current_data()
        status, customer_obj = customer_ctrl._logic.check_customer_status(raw_data)

        if status == "NEW":
            def save_customer():
                customer_ctrl._on_save_requested(raw_data)  # Use the controller's own save method

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
            # Return False to halt navigation until user decides
            return False
        else:
            self._state_manager.set_customer(customer_obj)
            return True

    def finish_and_reset(self):
        """Ends the process and resets the wizard to its 'new invoice' state."""
        print("WORKFLOW: Finish & Reset requested.")
        self._is_edit_mode = False
        self._editing_invoice_number = None
        self._view.setWindowTitle("ایجاد فاکتور جدید")

        self._state_manager.reset()
        for name, controller in self.sub_controllers.items():
            if hasattr(controller, 'reset_view'):
                controller.reset_view()
        self._view.set_current_step(0)

    def start_deep_edit_session(self, invoice_data: InvoiceData, items_data: list[InvoiceItemData]):
        self.finish_and_reset()
        print(f"Wizard Controller: Starting DEEP EDIT session for {invoice_data.invoice_number}")

        self._is_edit_mode = True
        self._editing_invoice_number = invoice_data.invoice_number

        # 1️⃣ Save the original invoice for reference
        self._state_manager.set_original_invoice_for_edit(invoice_data)

        # 2️⃣ Get customer details
        customer_logic = self.sub_controllers['customer']._logic
        customer_for_edit = customer_logic.get_customer_details(invoice_data.national_id)
        if not customer_for_edit:
            show_warning_message_box(self._view, "خطا", "اطلاعات مشتری مرتبط با این فاکتور یافت نشد.")
            self.finish_and_reset()
            return

        # 3️⃣ Prepare invoice items (wizard-level models)
        doc_logic = self.sub_controllers['documents']._logic
        wizard_items = []
        for db_item in items_data:
            service = doc_logic.get_service_by_name(db_item.service_name)
            if not service:
                print(f"Warning: Could not find service '{db_item.service_name}' for deep edit. Skipping item.")
                continue
            wizard_items.append(
                InvoiceItem(
                    service=service,
                    quantity=db_item.quantity,
                    page_count=db_item.page_count,
                    extra_copies=db_item.additional_issues,
                    is_official=bool(db_item.is_official),
                    has_judiciary_seal=bool(db_item.has_judiciary_seal),
                    has_foreign_affairs_seal=bool(db_item.has_foreign_affairs_seal),
                    remarks=db_item.remarks,
                    translation_price=db_item.translation_price,
                    certified_copy_price=db_item.certified_copy_price,
                    registration_price=db_item.registration_price,
                    judiciary_seal_price=db_item.judiciary_seal_price,
                    foreign_affairs_seal_price=db_item.foreign_affairs_seal_price,
                    total_price=db_item.total_price,
                )
            )

        # 4️⃣ Load the customer view (UI update only)
        self.sub_controllers['customer'].load_customer_for_edit(customer_for_edit)
        self._state_manager.set_customer(customer_for_edit)

        # 5️⃣ Only this call updates both UI and state through the signal
        self.sub_controllers['documents'].load_items_for_edit(wizard_items)

        self._state_manager.set_invoice_items(wizard_items)

        self._view.set_current_step(0)
