# invoice_page_wizard.py
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox
)

from features.Invoice_Page_GAS.customer_info_GAS.customer_info_controller import CustomerController
# Import the data models to hold the state
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
# Import the widgets for each step
from features.Invoice_Page_GAS.document_assignment.document_assignment_view import AssignmentWidget
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_controller import DocumentSelectionController
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem
from features.Invoice_Page_GAS.workflow_manager.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_controller import InvoiceDetailsController
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_logic import CustomerStatus
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_controller import InvoicePreviewController

from shared import show_question_message_box


class InvoiceMainWidget(QWidget):
    """
    The main application window that hosts and manages the multi-step invoice creation process.
     It acts as a "conductor" for the different steps.
    """
    customer_step_completed = Signal(List[dict])
    invoice_step_completed = Signal(List[dict])
    assignment_step_completed = Signal(List[dict])

    def __init__(self):
        super().__init__()

        # --- 1. Window and State Initialization ---
        self.setObjectName("InvoiceWizard")
        self.setWindowTitle("ایجاد فاکتور جدید")
        self.setGeometry(100, 100, 1200, 900)
        self.state_manager = WorkflowStateManager()

        self._connect_signals()
        self._setup_state_listeners()
        self._setup_ui()

        self.next_step_handlers = {
            self.customer_widget: self._handle_next_from_customer_info,
            self.document_selection_widget: self._handle_next_from_document_selection,
            self.assignment_widget: self._handle_next_from_assignment,
            self.invoice_details_widget: self._handle_next_from_invoice_details
        }

    # ----------------------------------------------------------------------
    # UI Creation Methods
    # ----------------------------------------------------------------------
    def _setup_ui(self):

        # The main layout is a vertical box: top bar, stacked widget, bottom bar.
        self.main_layout = QVBoxLayout(self)

        # Create each section of the UI using helper methods for clarity
        self._create_top_bar()
        self._create_stacked_widget()
        self._create_bottom_bar()

        # Add the created sections to the main layout
        self.main_layout.addLayout(self.top_bar_layout)
        self.main_layout.addWidget(self.stacked_widget)
        self.main_layout.addLayout(self.bottom_bar_layout)

        # Set the initial UI state for the first step
        self._update_step_ui(0)

    def _create_top_bar(self):
        """Creates the top progress bar with step labels."""
        self.top_bar_layout = QHBoxLayout()
        self.top_bar_layout.setObjectName('top_bar_layout')
        self.top_bar_layout.setContentsMargins(20, 10, 20, 10)

        self.step_labels = []
        steps = [
            "۱. اطلاعات مشتری", "۲. انتخاب اسناد", "۳. تخصیص اسناد",
            "۴. جزئیات فاکتور", "۵. پیش‌نمایش"
        ]

        for i, text in enumerate(steps):
            label = QLabel(text)
            label.setObjectName("StepLabel")
            self.step_labels.append(label)
            self.top_bar_layout.addWidget(label)
            if i < len(steps) - 1:
                self.top_bar_layout.addStretch()

    def _create_stacked_widget(self):
        """Creates the QStackedWidget and populates it with the step widgets."""
        self.stacked_widget = QStackedWidget()

        # --- Step 1: Customer Info ---
        self.customer_controller = CustomerController(self.state_manager)
        self.customer_widget = self.customer_controller.get_widget()
        self.stacked_widget.addWidget(self.customer_widget)

        # --- Step 2: Document Selection ---
        self.doc_controller = DocumentSelectionController(self.state_manager)
        self.doc_controller._logic.invoice_list_updated.connect(self.state_manager.set_invoice_items)
        self.document_selection_widget = self.doc_controller.get_widget()
        self.stacked_widget.addWidget(self.document_selection_widget)

        # --- Step 3: Assignment ---
        self.assignment_widget = AssignmentWidget(self.state_manager)
        self.stacked_widget.addWidget(self.assignment_widget)

        # --- Step 4: Invoice details ---
        self.invoice_details_controller = InvoiceDetailsController(self.state_manager)
        self.invoice_details_widget = self.invoice_details_controller.get_widget()
        self.stacked_widget.addWidget(self.invoice_details_widget)

        # --- Step 5: Invoice preview ---
        self.preview_controller = InvoicePreviewController(self.state_manager)
        self.preview_widget = self.preview_controller.get_widget()
        self.stacked_widget.addWidget(self.preview_widget)

    def _create_bottom_bar(self):
        """Creates the bottom navigation bar with 'Previous' and 'Next' buttons."""
        self.bottom_bar_layout = QHBoxLayout()

        self.prev_button = QPushButton("مرحله قبل")
        self.next_button = QPushButton("مرحله بعد")
        self.next_button.setObjectName("PrimaryButton")

        self.prev_button.clicked.connect(self._go_to_previous_step)
        self.next_button.clicked.connect(self._go_to_next_step)

        self.bottom_bar_layout.addStretch()
        self.bottom_bar_layout.addWidget(self.prev_button)
        self.bottom_bar_layout.addWidget(self.next_button)

    # ----------------------------------------------------------------------
    # Connecting Signals
    # ----------------------------------------------------------------------
    def _connect_signals(self):
        self.state_manager.customer_updated.connect(self._print_customer_state)
        self.state_manager.invoice_items_updated.connect(self._print_items_state)
        self.state_manager.assignments_updated.connect(self._print_assignments_state)

    def _setup_state_listeners(self):
        """Attributes to hold key widget references."""
        self.customer_widget = None
        self.document_selection_widget = None
        self.assignment_widget = None
        self.invoice_details_widget = None  # Placeholder for step 4
        self.preview_controller = None  # Add new attribute

    # ----------------------------------------------------------------------
    # Data Handling Slots
    # ----------------------------------------------------------------------

    def on_customer_saved(self, customer: Customer):
        """Receives the customer data from Step 1 and stores it."""
        self.current_customer = customer
        print(f"INFO: Customer '{customer.name}' data received.")

    def on_invoice_items_updated(self, items: list[InvoiceItem]):
        """Receives the list of invoice items from Step 2 and stores it."""
        self.current_invoice_items = items
        print(f"INFO: Invoice items updated. Count: {len(items)}.")

    def on_assignments_updated(self, assignments: dict):
        """Receives the document assignments from Step 3 and stores them."""
        self.current_assignments = assignments
        print("INFO: Document assignments updated.")

    # ----------------------------------------------------------------------
    # Navigation and Logic
    # ----------------------------------------------------------------------

    def _go_to_next_step(self):
        """
        A clean, dispatch-based method for handling forward navigation.
        """
        current_widget = self.stacked_widget.currentWidget()

        # Look up the specific handler for the current page.
        handler = self.next_step_handlers.get(current_widget)

        if handler:
            # If a specific handler exists, call it.
            # The handler is now responsible for validation and navigation.
            handler()
        else:
            # If no specific handler, perform the default navigation.
            self._navigate_by_offset(1)

    def _go_to_previous_step(self):
        """Handles backward navigation with conditional skipping."""
        current_widget = self.stacked_widget.currentWidget()

        # Special case: If we are on Invoice Details and skipped Assignment, go back 2 steps.
        if current_widget is self.invoice_details_widget:
            if self.state_manager.get_num_people() <= 1:
                self._navigate_to_widget(self.document_selection_widget)
                return  # Stop further execution

        # Default behavior for all other cases
        self._navigate_by_offset(-1)

    # --- Specific "Next Step" Handlers ---

    def _handle_next_from_customer_info(self):
        """Logic for when the 'Next' button is clicked on the customer info page."""
        raw_data = self.customer_widget.get_current_data()
        status, customer_obj = self.customer_controller.check_status(raw_data)

        if status == CustomerStatus.NEW:
            reply = QMessageBox.question(
                self, "ذخیره مشتری",
                "این مشتری در پایگاه داده وجود ندارد. آیا مایل به ذخیره آن هستید؟",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.customer_controller.save_current_customer(raw_data)
                # The state manager is updated automatically by the controller's success path
                self._navigate_to_widget(self.document_selection_widget)
            elif reply == QMessageBox.No:
                # Create a temporary customer object for the state manager
                temp_customer = self.customer_controller._logic._build_customer_from_data(raw_data)
                self.state_manager.set_customer(temp_customer)
                self._navigate_to_widget(self.document_selection_widget)
            # If Cancel, do nothing.
        else:  # Existing customer (modified or not)
            self.state_manager.set_customer(customer_obj)
            self._navigate_to_widget(self.document_selection_widget)

    def _handle_next_from_document_selection(self):
        """Logic for leaving the document selection page."""
        if self.state_manager.get_num_people() > 1:
            # Go to Assignment step
            unpacked_items = self._unpack_invoice_items(self.state_manager.get_invoice_items())
            saved_assignments = self.state_manager.get_assignments()
            self.assignment_widget.set_data(
                self.state_manager.get_customer(), unpacked_items, saved_assignments
            )
            self._navigate_to_widget(self.assignment_widget)
        else:
            # Skip to Invoice Details step
            self.state_manager.auto_assign_for_single_person()
            self.invoice_details_controller.prepare_and_display_data(
                self.state_manager.get_customer(),
                self.state_manager.get_invoice_items()
            )
            self._navigate_to_widget(self.invoice_details_widget)

    def _handle_next_from_assignment(self):
        """Logic for leaving the assignment page."""
        self.invoice_details_controller.prepare_and_display_data(
            self.state_manager.get_customer(),
            self.state_manager.get_invoice_items()  # Use original items
        )
        self._navigate_to_widget(self.invoice_details_widget)

    def _handle_next_from_invoice_details(self):
        """Logic for leaving the invoice details page."""
        current_widget = self.stacked_widget.currentWidget()
        # --- NEW LOGIC: When leaving Invoice Details (Step 4) ---
        if current_widget is self.invoice_details_widget:
            # --- FIX: "Activate" the preview controller ---
            # Tell the preview controller to assemble all the data from the state manager
            # and render its view for the first time.
            self.preview_controller.prepare_and_display_data()

            # Now, navigate to the preview page
            next_index = self.stacked_widget.indexOf(self.preview_widget)
            self.stacked_widget.setCurrentIndex(next_index)
            self._update_step_ui(next_index)
        # self.preview_controller.prepare_and_display_data()
        # self._navigate_to_widget(self.preview_widget)

    # --- Navigation Helper Methods ---
    def _navigate_to_widget(self, widget: QWidget):
        """Navigates the stack to a specific widget."""
        index = self.stacked_widget.indexOf(widget)
        if index != -1:
            self.stacked_widget.setCurrentIndex(index)
            self._update_step_ui(index)

    def _navigate_by_offset(self, offset: int):
        """Navigates forward (1) or backward (-1) from the current page."""
        current_index = self.stacked_widget.currentIndex()
        new_index = current_index + offset
        if 0 <= new_index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(new_index)
            self._update_step_ui(new_index)

    def _update_step_ui(self, current_index):
        """Updates the top bar styles and enables/disables navigation buttons."""
        for i, label in enumerate(self.step_labels):
            if i == current_index:
                label.setProperty("state", "active")
            else:
                label.setProperty("state", "inactive")
            label.style().unpolish(label)
            label.style().polish(label)

        self.prev_button.setEnabled(current_index > 0)
        self.next_button.setEnabled(current_index < self.stacked_widget.count() - 1)

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

    # --- NEW: Print statement slots ---
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
