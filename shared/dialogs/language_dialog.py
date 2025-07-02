from PySide6.QtWidgets import (QDialog, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox)


class LanguageDialog(QDialog):
    def __init__(self, current, parent=None):
        super(LanguageDialog, self).__init__(parent)
        self.setWindowTitle("Select Language")
        self.setStyleSheet("""
            QDialog{
            padding: 10px;
            }
            """)
        # Set up layout
        layout = QVBoxLayout(self)

        # A combo box to choose the language (populate with your actual languages)
        self.language_combo = QComboBox(self)
        self.language_combo.addItems([
            "آذربایجانی", "آلمانی", "اردو", "ارمنی",
            "اسپانیولی", "ایتالیایی", "انگلیسی", "ترکی استانبولی",
            "چینی", "روسی", "رومانیایی", "ژاپنی",
            "صربی", "عربی", "فرانسوی", "کردی"])
        self.language_combo.setStyleSheet("""
            QComboBox{
            font-family: IRANSans;
            font-size: 12px;
            border: 1px solid #ddd;
            padding: 2px;
            }
            """)
        layout.addWidget(self.language_combo)

        # Set the current language if available
        index = self.language_combo.findText(current)
        if index != -1:
            self.language_combo.setCurrentIndex(index)

        # Add the QCheckBox with the requested text:
        self.default_checkbox = QCheckBox("این زبان را پیشفرض قرار بده", self)
        self.default_checkbox.setStyleSheet("""
                    QComboBox{
                    font-family: IRANSans;
                    font-size: 12px;
                    }
                    """)
        layout.addWidget(self.default_checkbox)

        # Add Dialog buttons
        accept_button = QPushButton("تایید", self)
        cancel_button = QPushButton("انصراف", self)
        accept_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        h_layout = QHBoxLayout()
        h_layout.addWidget(accept_button)
        h_layout.addWidget(cancel_button)
        layout.addLayout(h_layout)

    def get_selected_language(self):
        """
        Returns a tuple containing the selected language and whether it should be the default.
        """
        return self.language_combo.currentText(), self.default_checkbox.isChecked()