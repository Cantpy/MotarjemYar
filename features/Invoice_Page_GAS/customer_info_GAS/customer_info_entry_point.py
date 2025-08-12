# main.py
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from features.Invoice_Page_GAS.customer_info_GAS.customer_info_view import CustomerInfoWidget
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_controller import CustomerController


if __name__ == '__main__':
    app = QApplication(sys.argv)

    QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    controller = CustomerController()
    window = CustomerInfoWidget(controller)
    window.show()
    sys.exit(app.exec())
