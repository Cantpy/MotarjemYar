import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QGridLayout, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def find_file_by_name(filename, root_folder):
    """Find a file by name in the given root folder and its subdirectories."""
    for root, dirs, files in os.walk(root_folder):
        if filename in files:
            return os.path.join(root, filename)
    return None


class PricingDetailsDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pricing Details")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Pricing Details for: {item_data['item']}")
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title.setFont(font)
        layout.addWidget(title)

        # Details grid
        details_layout = QGridLayout()
        details_widget = QWidget()
        details_widget.setLayout(details_layout)

        # Item details
        details = [
            ("Item Name:", item_data['item']),
            ("Unit Price:", f"${item_data['unit_price']:.2f}"),
            ("Quantity:", str(item_data['quantity'])),
            ("Subtotal:", f"${item_data['subtotal']:.2f}"),
            ("Tax Rate:", f"{item_data['tax_rate']}%"),
            ("Tax Amount:", f"${item_data['tax_amount']:.2f}"),
            ("Total Price:", f"${item_data['total']:.2f}"),
            ("Discount:", f"{item_data['discount']}%"),
            ("Final Amount:", f"${item_data['final_amount']:.2f}")
        ]

        for i, (label, value) in enumerate(details):
            label_widget = QLabel(label)
            label_widget.setAlignment(Qt.AlignRight)
            value_widget = QLabel(str(value))
            value_widget.setAlignment(Qt.AlignLeft)

            if "Total" in label or "Final" in label:
                font = QFont()
                font.setBold(True)
                label_widget.setFont(font)
                value_widget.setFont(font)

            details_layout.addWidget(label_widget, i, 0)
            details_layout.addWidget(value_widget, i, 1)

        layout.addWidget(details_widget)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        self.setLayout(layout)
