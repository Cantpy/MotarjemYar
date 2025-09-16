# features/Services/documents/documents_models.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, QDialogButtonBox, QListWidget, QTextEdit,
                               QLineEdit, QHBoxLayout)
from PySide6.QtCore import Qt
from features.Services.documents.documents_models import ImportResult


class ImportSourceDialog(QDialog):
    """A simple dialog to ask the user for the import source."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("انتخاب منبع بارگذاری")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("لطفا منبع مدارک برای بارگذاری را انتخاب کنید:"))

        self.from_excel_btn = QPushButton("📂 بارگذاری از فایل اکسل")
        self.from_db_btn = QPushButton("🗄️ بارگذاری از پایگاه داده دیگر")

        self.layout.addWidget(self.from_excel_btn)
        self.layout.addWidget(self.from_db_btn)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.button_box)

        self.button_box.rejected.connect(self.reject)

        # We will connect the button clicks in the controller to know which was chosen
        self.source = None
        self.from_excel_btn.clicked.connect(self._on_excel_selected)
        self.from_db_btn.clicked.connect(self._on_db_selected)

    def _on_excel_selected(self):
        self.source = "excel"
        self.accept()

    def _on_db_selected(self):
        self.source = "database"
        self.accept()


class ImportSummaryDialog(QDialog):
    """A dialog to display the results of the import operation."""

    def __init__(self, result: ImportResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle("خلاصه بارگذاری")
        self.setMinimumSize(600, 450)
        self.layout = QVBoxLayout(self)

        # --- Summary Section ---
        summary_text = (
            f"بارگذاری از {result.source} تکمیل شد.\n"
            f"✅ {result.success_count} مدرک با موفقیت اضافه شد.\n"
            f"❌ {result.failed_count} مورد با خطا مواجه شد."
        )
        self.layout.addWidget(QLabel(summary_text))

        # --- Added Services Section ---
        self.layout.addWidget(QLabel("\nمدارک اضافه شده:"))
        self.added_list = QListWidget()
        if result.added_services_names:
            self.added_list.addItems(result.added_services_names)
        else:
            self.added_list.addItem("هیچ مدرکی اضافه نشد.")
        self.layout.addWidget(self.added_list)

        # --- Errors Section ---
        if result.errors:
            self.layout.addWidget(QLabel("\nخطاهای رخ داده:"))
            self.error_box = QTextEdit()
            self.error_box.setReadOnly(True)
            self.error_box.setText("\n".join(result.errors))
            self.layout.addWidget(self.error_box)

        # --- Guide Section ---
        self.layout.addWidget(QLabel("\nراهنمای بارگذاری صحیح:"))
        guide_text = self._get_guide_text()
        self.guide_box = QTextEdit()
        self.guide_box.setReadOnly(True)
        self.guide_box.setMarkdown(guide_text)
        self.layout.addWidget(self.guide_box)

        self.ok_button = QPushButton("باشه")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def _get_guide_text(self) -> str:
        return """
        ### راهنمای ستون‌ها برای فایل اکسل:
        
        فایل اکسل شما باید حداقل شامل ستون‌های زیر باشد (به ترتیب یا با این نام‌ها):
        
        1.  **`name` (متن):** نام مدرک (اجباری).
        2.  **`base_price` (عدد):** هزینه پایه ترجمه (اجباری).
        3.  **`dynamic_price_name_1` (متن):** نام هزینه متغیر اول (مثال: `تعداد سطر`).
        4.  **`dynamic_price_1` (عدد):** مبلغ هزینه متغیر اول.
        5.  **`dynamic_price_name_2` (متن):** نام هزینه متغیر دوم (مثال: `تعداد درس`).
        6.  **`dynamic_price_2` (عدد):** مبلغ هزینه متغیر دوم.
        
        - **نکته:** ردیف‌هایی که ستون `name` یا `base_price` آن‌ها خالی باشد، نادیده گرفته می‌شوند.
        - **نکته:** مقادیر پولی باید فقط شامل عدد باشند (بدون جداکننده یا واحد پول).
        """


class InputDialog(QDialog):
    """Input dialog for service data entry"""

    def __init__(self, title: str = "اضافه کردن مدرک", parent=None):
        super().__init__(parent)
        self.inputs = {}
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup dialog UI"""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(350)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout()

        # Input fields
        fields = [
            ("نام مدرک", "document_name"),
            ("هزینه پایه", "base_cost"),
            ("نوع هزینه متغیر ۱", "variable_name_1"),
            ("هزینه متغیر ۱", "variable_cost_1"),
            ("نوع هزینه متغیر ۲", "variable_name_2"),
            ("هزینه متغیر ۲", "variable_cost_2")
        ]

        for label_text, field_key in fields:
            row_layout = QHBoxLayout()

            label = QLabel(label_text)
            label.setMinimumWidth(120)
            line_edit = QLineEdit()

            if "هزینه" in label_text:
                line_edit.setPlaceholderText("مثال: 10000")
            elif "نوع" in label_text:
                line_edit.setPlaceholderText("مثال: تعداد درس/ تعداد سطر")

            self.inputs[field_key] = line_edit

            row_layout.addWidget(label)
            row_layout.addWidget(line_edit)
            layout.addLayout(row_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("تایید")
        self.cancel_button = QPushButton("انصراف")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Focus first input
        if self.inputs:
            list(self.inputs.values())[0].setFocus()

    def get_values(self) -> dict[str, str]:
        """Get values from input fields"""
        return {key: widget.text().strip() for key, widget in self.inputs.items()}

    def set_values(self, values: dict[str, str]):
        """Set values in input fields"""
        for key, value in values.items():
            if key in self.inputs:
                self.inputs[key].setText(str(value) if value is not None else "")
