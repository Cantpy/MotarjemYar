# document_selection_entry_point.py
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_controller import DocumentSelectionController
from features.Invoice_Page_GAS.workflow_manager.invoice_page_state_manager import WorkflowStateManager


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    state_manager = WorkflowStateManager()
    controller = DocumentSelectionController(state_manager=state_manager)

    # 2. Get the fully constructed widget from the controller.
    view = controller.get_widget()
    view.show()

    sys.exit(app.exec())
