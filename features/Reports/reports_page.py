import sys
from PySide6.QtWidgets import QWidget, QApplication


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        from qt_designer_ui.ui_reports_page import Ui_Form
        self. ui = Ui_Form()
        self.ui.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportsPage(parent=None)
    window.show()
    app.exec()
