# main.py
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from features.Invoice_Page_GAS.workflow_manager.invoice_page_state_manager import WorkflowStateManager
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_controller import CustomerController


if __name__ == '__main__':
    app = QApplication(sys.argv)

    QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    state_manager = WorkflowStateManager()
    controller = CustomerController(state_manager=state_manager)
    window = controller.get_widget()

    window.show()
    sys.exit(app.exec())
