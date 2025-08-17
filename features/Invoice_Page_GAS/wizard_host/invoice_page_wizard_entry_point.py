# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import the main window class from the host_application package
from features.Invoice_Page_GAS.wizard_host.invoice_page_wizard import InvoiceMainWidget
from features.Invoice_Page_GAS.wizard_host.invoice_page_wizaard_qss import WIZARD_STYLESHEET


if __name__ == "__main__":
    # This is the entry point of your application.

    # Prerequisite check: Ensure the database exists.
    # In a real application, you might have a more robust check or
    # a setup wizard, but for now, this comment serves as a reminder.
    # print("Reminder: Make sure you have run 'create_dummy_services_db.py' at least once.")

    # 1. Create the application instance.
    app = QApplication(sys.argv)

    # 2. Set global settings for the entire application.
    QApplication.setLayoutDirection(Qt.RightToLeft)
    app.setStyleSheet(WIZARD_STYLESHEET)

    # 3. Create an instance of your main application window.
    window = InvoiceMainWidget()

    # 4. Show the main window.
    window.show()

    # 5. Start the application's event loop and ensure a clean exit.
    sys.exit(app.exec())
