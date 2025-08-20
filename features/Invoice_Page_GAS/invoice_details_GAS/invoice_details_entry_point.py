# invoice_details/invoice_details_entry_point.py

from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_controller import InvoiceDetailsController
from features.Invoice_Page_GAS.invoice_page_state_manager import WorkflowStateManager
from PySide6.QtWidgets import QApplication
import sys


if __name__ == "__main__":
    app = QApplication([])

    state_manager = WorkflowStateManager
    controller = InvoiceDetailsController(state_manager)
    window = controller.get_widget()

    window.show()
    sys.exit(app.exec())
