# wizard_host/main_window_controller.py
from features.Invoice_Page_GAS.wizard_host.invoice_page_wizard_view import MainWindowView
from features.Invoice_Page_GAS.wizard_host.invoice_page_wizard_logic import MainWindowLogic
from features.Invoice_Page_GAS.invoice_page_state_manager import WorkflowStateManager
# Import all your feature controllers
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_controller import CustomerInfoController
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_controller import DocumentSelectionController
from features.Invoice_Page_GAS.document_assignment.document_assignment_view import AssignmentWidget
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_controller import InvoiceDetailsController
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_controller import InvoicePreviewController
# Import all your feature models
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem


class MainWindowController:
    def __init__(self):
        self.state_manager = WorkflowStateManager()
        self._view = MainWindowView()

        # 2. Create all the feature controllers
        customer_ctrl = CustomerInfoController(self.state_manager)
        doc_select_ctrl = DocumentSelectionController(self.state_manager)
        invoice_details_ctrl = InvoiceDetailsController(self.state_manager)
        preview_ctrl = InvoicePreviewController(self.state_manager)

        # 3. Get the widget from each controller
        customer_widget = customer_ctrl.get_widget()
        doc_select_widget = doc_select_ctrl.get_widget()
        assignment_widget = AssignmentWidget(self.state_manager)
        invoice_details_widget = invoice_details_ctrl.get_widget()
        preview_widget = preview_ctrl.get_widget()

        # 4. Populate the view's stacked widget
        self._view.stacked_widget.addWidget(customer_widget)
        self._view.stacked_widget.addWidget(doc_select_widget)
        self._view.stacked_widget.addWidget(assignment_widget)
        self._view.stacked_widget.addWidget(invoice_details_widget)
        self._view.stacked_widget.addWidget(preview_widget)

        # 5. Create a dictionary to pass all components to the Logic layer
        self.controllers_and_widgets = {
            'customer': {'controller': customer_ctrl, 'widget': customer_widget},
            'documents': {'controller': doc_select_ctrl, 'widget': doc_select_widget},
            'assignment': {'controller': None, 'widget': assignment_widget},
            'details': {'controller': invoice_details_ctrl, 'widget': invoice_details_widget},
            'preview': {'controller': preview_ctrl, 'widget': preview_widget}
        }

        # 6. Create the navigation _logic, passing it all the pieces it needs
        self._logic = MainWindowLogic(self._view, self.state_manager, self.controllers_and_widgets)

        # 7. Connect the high-level signals and bridge data flow
        self._view.next_button_clicked.connect(self._logic.go_to_next_step)
        self._view.prev_button_clicked.connect(self._logic.go_to_previous_step)
        doc_select_ctrl._logic.invoice_list_updated.connect(self.state_manager.set_invoice_items)

        # 8. Connect the state manager signals to print debug info
        self.state_manager.customer_updated.connect(self._print_customer_state)
        self.state_manager.invoice_items_updated.connect(self._print_items_state)
        self.state_manager.assignments_updated.connect(self._print_assignments_state)

        # command the view to set its initial state to the first page.
        self._view.set_current_step(0)

    def get_widget(self):
        """Returns the main view widget to be shown by main.py."""
        return self._view

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
