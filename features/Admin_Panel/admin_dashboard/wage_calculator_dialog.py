# motarjemyar/admin_dashboard/wage_calculator_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
                               QLineEdit, QPushButton, QDialogButtonBox, QLabel)
from shared.fonts.font_manager import FontManager


class WageCalculatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("محاسبه دستمزد کارکنان")
        self.setMinimumWidth(400)
        self.setFont(FontManager.get_font(size=11))

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.employee_type_combo = QComboBox()
        self.employee_type_combo.addItems(["مترجم", "کارمند", "حسابدار"])
        form_layout.addRow("نوع کارمند:", self.employee_type_combo)

        self.employee_name_combo = QComboBox()
        form_layout.addRow("نام کارمند:", self.employee_name_combo)

        self.result_label = QLabel("لطفا برای محاسبه کلیک کنید.")
        self.result_label.setStyleSheet("font-weight: bold; color: #0078D7;")

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.result_label)

        # Standard OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Add a calculate button
        self.calculate_btn = QPushButton("محاسبه")
        button_box.addButton(self.calculate_btn, QDialogButtonBox.ActionRole)

        main_layout.addWidget(button_box)

        # In a real implementation, you would connect signals here to fetch
        # employee names and perform calculations.
        # self.calculate_btn.clicked.connect(self.perform_calculation)
