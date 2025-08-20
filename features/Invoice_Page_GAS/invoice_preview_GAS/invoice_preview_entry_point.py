# main.py

import sys
from PySide6.QtWidgets import QApplication
from features.Invoice_Page_GAS.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_controller import InvoicePreviewController


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # The main window which is the primary view
    state_manager = WorkflowStateManager()

    # The controller that binds the view to the logic
    controller = InvoicePreviewController(state_manager)
    view = controller.get_widget()

    view.show()

    sys.exit(app.exec())
