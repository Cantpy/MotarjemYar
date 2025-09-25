# shared/dialogs/import_dialog.py

from PySide6.QtWidgets import (QTabWidget, QListWidget, QTextEdit, QDialog, QVBoxLayout, QPushButton,
                               QLabel, QWidget, QDialogButtonBox, QLineEdit, QHBoxLayout)
from PySide6.QtCore import Qt
from typing import List, Tuple, Dict


class ImportSourceDialog(QDialog):
    """A simple dialog to ask the user for the import source."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("انتخاب منبع بارگذاری")
        self.layout = QVBoxLayout(self)
        self.source = None

        self.layout.addWidget(QLabel("لطفا منبع داده‌ها برای بارگذاری را انتخاب کنید:"))

        self.from_excel_btn = QPushButton("📂 بارگذاری از فایل اکسل")
        self.from_db_btn = QPushButton("🗄️ بارگذاری از پایگاه داده دیگر")
        self.layout.addWidget(self.from_excel_btn)
        self.layout.addWidget(self.from_db_btn)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.layout.addWidget(self.button_box)

        self.button_box.rejected.connect(self.reject)
        self.from_excel_btn.clicked.connect(self._on_excel_selected)
        self.from_db_btn.clicked.connect(self._on_db_selected)

    def _on_excel_selected(self):
        self.source = "excel"
        self.accept()

    def _on_db_selected(self):
        self.source = "database"
        self.accept()


class ImportSummaryDialog(QDialog):
    """
    A powerful dialog to display the results of a multi-part import operation.
    """

    def __init__(self, results: dict[str, "ImportResult"], parent=None):
        super().__init__(parent)
        self.setWindowTitle("خلاصه بارگذاری از فایل")
        self.setMinimumSize(700, 550)
        self.layout = QVBoxLayout(self)
        self.results = results

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # --- Dynamically create a tab for each result set ---
        for sheet_name, result in self.results.items():
            # Create a dedicated widget for this sheet's summary
            summary_widget = self._create_summary_widget(result)
            # Add it as a new tab
            self.tab_widget.addTab(summary_widget, sheet_name.replace('_', ' ').title())

        # --- Add a final "Guide" tab ---
        guide_widget = self._create_guide_widget()
        self.tab_widget.addTab(guide_widget, "راهنما")

        self.ok_button = QPushButton("باشه")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def _create_summary_widget(self, result: "ImportResult") -> QWidget:
        """Helper to create the content widget for a single summary tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # --- Summary Section ---
        summary_text = (
            f"بارگذاری از {result.source} تکمیل شد.\n"
            f"✅ {result.success_count} مورد با موفقیت اضافه شد.\n"
            f"❌ {result.failed_count} مورد با خطا مواجه شد."
        )
        layout.addWidget(QLabel(summary_text))

        # --- Added Items Section ---
        layout.addWidget(QLabel("\nموارد اضافه شده:"))
        added_list = QListWidget()
        if result.added_services_names:
            added_list.addItems(result.added_services_names)
        else:
            added_list.addItem("هیچ موردی اضافه نشد.")
        layout.addWidget(added_list)

        # --- Errors Section ---
        if result.errors:
            layout.addWidget(QLabel("\nخطاهای رخ داده:"))
            error_box = QTextEdit()
            error_box.setReadOnly(True)
            error_box.setText("\n".join(result.errors))
            layout.addWidget(error_box)

        return widget

    def _create_guide_widget(self) -> QWidget:
        """Helper to create the instructional guide tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        guide_box = QTextEdit()
        guide_box.setReadOnly(True)
        guide_box.setMarkdown(self._get_guide_text())
        layout.addWidget(guide_box)
        return widget

    def _get_guide_text(self) -> str:
        """
        Returns the instructional guide text in Markdown format.
        """
        return """
        ### راهنمای فایل اکسل

        فایل اکسل شما باید شامل شیت‌های زیر با نام‌های دقیق انگلیسی باشد:

        ---
        #### شیت: `Documents`
        برای ثبت مدارک و هزینه‌های متغیر آن‌ها.
        - **ستون‌ها:** `Name`, `Base Price`, `Fee 1 Name`, `Fee 1 Price`, `Fee 2 Name`, `Fee 2 Price`, ...
        - **نکته:** می‌توانید هر تعداد زوج ستون `Fee X Name` و `Fee X Price` که نیاز دارید اضافه کنید.

        ---
        #### شیت: `Fixed Prices`
        برای ثبت هزینه‌های ثابت برنامه.
        - **ستون‌ها:** `name`, `price`, `is_default` (اختیاری، `true`/`false`), `label_name` (اختیاری).

        ---
        #### شیت: `Other Services`
        برای ثبت سایر خدمات متفرقه.
        - **ستون‌ها:** `name`, `price`.

        ---
        **قوانین کلی:**
        - ردیف‌هایی که ستون‌های اجباری آن‌ها (مانند `name` و `price`) خالی باشد، نادیده گرفته می‌شوند.
        - مقادیر پولی باید فقط شامل عدد باشند (بدون جداکننده یا واحد پول).
        """


class GenericInputDialog(QDialog):
    """
    A highly reusable input dialog that can be configured with any set of fields.
    """

    def __init__(self, title: str, fields: List[Tuple[str, str, str]], parent=None):
        """
        Initializes the dialog.

        Args:
            title: The window title for the dialog.
            fields: A list of tuples, where each tuple defines a field:
                    (label_text, field_key, placeholder_text)
                    Example: [("نام مدرک", "name", "مثال: شناسنامه")]
            parent: The parent widget.
        """
        super().__init__(parent)
        self.inputs: Dict[str, QLineEdit] = {}
        self._setup_ui(title, fields)

    def _setup_ui(self, title: str, fields: List[Tuple[str, str, str]]):
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(350)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)

        # --- Dynamically create input fields ---
        for label_text, field_key, placeholder in fields:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setMinimumWidth(120)

            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            self.inputs[field_key] = line_edit

            row_layout.addWidget(label)
            row_layout.addWidget(line_edit)
            layout.addLayout(row_layout)

        # --- Standard Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        if self.inputs:
            list(self.inputs.values())[0].setFocus()

    def get_values(self) -> dict[str, str]:
        """Returns a dictionary of {field_key: value}."""
        return {key: widget.text().strip() for key, widget in self.inputs.items()}

    def set_values(self, values: dict[str, str]):
        """Pre-fills the dialog fields from a dictionary."""
        for key, value in values.items():
            if key in self.inputs:
                self.inputs[key].setText(str(value) if value is not None else "")
