# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import the main window class from the host_application package
from features.Invoice_Page_GAS.wizard_host.invoice_page_wizard_controller import MainWindowController
from features.Invoice_Page_GAS.wizard_host.invoice_page_wizaard_qss import WIZARD_STYLESHEET


if __name__ == "__main__":
    """This is the entry point of invoice wizard for testing purposes."""

    # Prerequisite check: Ensure the database exists.
    # In a real application, you might have a more robust check or
    # a setup wizard, but for now, this comment serves as a reminder.
    # print("Reminder: Make sure you have run 'create_dummy_services_db.py' at least once.")

    app = QApplication(sys.argv)
    QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(WIZARD_STYLESHEET)

    # 1. Create the main controller. It will build everything else.
    main_controller = MainWindowController()

    # 2. Get the main widget from the controller and show it.
    main_window = main_controller.get_widget()
    main_window.show()

    sys.exit(app.exec())
