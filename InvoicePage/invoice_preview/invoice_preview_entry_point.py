# main.py

import sys
from PySide6.QtWidgets import QApplication
from InvoicePage.invoice_preview.invoice_preview_view import MainInvoiceWindow
from InvoicePage.invoice_preview.invoice_preview_controller import InvoiceController

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # The main window which is the primary view
    main_window = MainInvoiceWindow()

    # The controller that binds the view to the logic
    controller = InvoiceController(main_window)

    main_window.show()

    sys.exit(app.exec())
