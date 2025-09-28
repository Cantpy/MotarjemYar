from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from features.Invoice_Page.document_selection.document_selection_models import FixedPrice
from typing import List


class SettingsDialog(QDialog):
    def __init__(self, fixed_prices: List[FixedPrice], parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات تعرفه‌های ثابت")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumSize(450, 500)
        self.setFont(QFont("IranSANS", 11))

        self.updated_prices: List[FixedPrice] = []

        main_layout = QVBoxLayout(self)

        # --- Create and populate the table ---
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["نام تعرفه", "قیمت (تومان)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)

        self.populate_table(fixed_prices)
        main_layout.addWidget(self.table)

        # --- Create OK/Cancel buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("ذخیره تغییرات")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("انصراف")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def populate_table(self, fixed_prices: List[FixedPrice]):
        self.table.setRowCount(len(fixed_prices))
        for row, fp in enumerate(fixed_prices):
            # Name item (read-only)
            name_item = QTableWidgetItem(fp.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # Store the original object in the item to retrieve its ID later
            name_item.setData(Qt.ItemDataRole.UserRole, fp)
            self.table.setItem(row, 0, name_item)

            # Price item (editable)
            price_item = QTableWidgetItem(str(fp.price))
            self.table.setItem(row, 1, price_item)

    def accept(self):
        """
        Override the accept method to validate and collect data before closing.
        """
        temp_updated_prices = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            price_item = self.table.item(row, 1)

            original_fp: FixedPrice = name_item.data(Qt.ItemDataRole.UserRole)
            new_price_str = price_item.text().strip()

            try:
                new_price = int(new_price_str)
                if new_price < 0:
                    raise ValueError("Price cannot be negative.")
                # Update the price on our data object
                original_fp.price = new_price
                temp_updated_prices.append(original_fp)
            except ValueError:
                QMessageBox.critical(
                    self,
                    "خطای ورودی",
                    f"لطفاً یک عدد صحیح و معتبر برای ردیف '{original_fp.name}' وارد کنید."
                )
                return # Stop the accept process

        # If all rows are valid, set the final list and accept the dialog
        self.updated_prices = temp_updated_prices
        super().accept()
