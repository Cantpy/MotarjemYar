# workflow_state_manager.py
from PySide6.QtCore import QObject, Signal
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import InvoiceItem


class WorkflowStateManager(QObject):
    """
    A non-GUI class that holds the state of the invoice creation process.
    It acts as the single source of truth for all data.
    """
    customer_updated = Signal(Customer)
    invoice_items_updated = Signal(list)
    assignments_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self._customer: Customer = None
        self._invoice_items: list[InvoiceItem] = []
        self._assignments: dict = {}

    # --- Public methods to get the current state ---
    def get_customer(self) -> Customer:
        return self._customer

    def get_invoice_items(self) -> list[InvoiceItem]:
        return self._invoice_items

    def get_assignments(self) -> dict:
        """Returns the current dictionary of document assignments."""
        return self._assignments

    def get_num_people(self) -> int:
        if not self._customer:
            return 0
        return 1 + len(self._customer.companions)

    # --- Public slots to update the state ---
    def set_customer(self, customer: Customer):
        """Updates the customer data and notifies listeners."""
        self._customer = customer
        print(f"STATE UPDATE: Customer set to '{customer.name}'")
        self.customer_updated.emit(self._customer)

    def set_invoice_items(self, items: list[InvoiceItem]):
        """Updates the invoice items and notifies listeners."""
        self._invoice_items = items
        print(f"STATE UPDATE: Invoice items set. Count: {len(items)}")
        self.invoice_items_updated.emit(self._invoice_items)

    def set_assignments(self, assignments: dict):
        """Updates the document assignments and notifies listeners."""
        self._assignments = assignments
        print("STATE UPDATE: Assignments set.")
        self.assignments_updated.emit(self._assignments)

    def auto_assign_for_single_person(self):
        """Helper method to create default assignments when skipping step 3."""
        if self._customer and self.get_num_people() == 1:
            assignments = {
                self._customer.name: self._invoice_items,
                "__unassigned__": []
            }
            self.set_assignments(assignments)
