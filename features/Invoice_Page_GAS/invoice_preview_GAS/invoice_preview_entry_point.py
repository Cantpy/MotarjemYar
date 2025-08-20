# main.py

import sys
from PySide6.QtWidgets import QApplication
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_view import MainInvoicePreviewWidget
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_controller import InvoicePreviewController

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # The main window which is the primary view
    main_window = MainInvoicePreviewWidget()

    # The controller that binds the view to the logic
    controller = InvoicePreviewController(main_window)

    main_window.show()

    sys.exit(app.exec())
