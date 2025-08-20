import sys
from PySide6.QtWidgets import QApplication
from features.Invoice_Table_GAS.invoice_table_GAS_controller import MainController

if __name__ == "__main__":

    app = QApplication(sys.argv)
    controller = MainController()
    window = controller.get_widget()
    window.show()
    sys.exit(app.exec())
