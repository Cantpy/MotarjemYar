# document_selection_entry_point.py
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_view import DocumentSelectionWidget


if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    window = DocumentSelectionWidget()
    window.show()

    sys.exit(app.exec())
