# features/Invoice_Page/invoice_details/invoice_details_settings_dialog.py

import json
import os
import copy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QTextEdit, QComboBox,
    QCheckBox, QDialogButtonBox
)
from shared.utils.path_utils import get_user_data_path
from features.Invoice_Page.invoice_details.invoice_details_models import Language


class SettingsManager:
    """Handles loading and saving of application settings to a JSON file."""

    def __init__(self):
        self.filepath = get_user_data_path('config', 'invoice_details_settings.json')

        self._defaults = {
            "default_remarks": "کلیه هزینه‌های مربوط به تاییدات دادگستری و وزارت امور خارجه بر عهده مشتری می‌باشد.",
            "emergency_basis": "translation_cost",
            "group_box_visibility": {
                "invoice": True,
                "customer": True,
                "financial": True,
                "office": True
            },
            "default_source_language": Language.FARSI.value,
            "default_target_language": Language.ENGLISH.value
        }
        self.settings = {}
        self.load()

    def load(self):
        """Loads settings, creating the file with defaults if it doesn't exist or is invalid."""
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge defaults with loaded settings to handle new keys gracefully
                    self.settings = {**self._defaults, **loaded_settings}
            else:
                raise FileNotFoundError
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = copy.deepcopy(self._defaults)
            self.save()

    def save(self):
        """Saves the current settings to the JSON file, ensuring the directory exists."""
        directory = os.path.dirname(self.filepath)
        os.makedirs(directory, exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        """Gets a setting value by key."""
        return copy.deepcopy(self.settings.get(key, default))

    def set(self, key, value):
        """Sets a setting value. Note: save() must be called separately now."""
        self.settings[key] = value


class SettingsDialog(QDialog):
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("تنظیمات فاکتور")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.main_layout = QVBoxLayout(self)

        # --- Default Remarks Section ---
        remarks_group = QGroupBox("متن پیش‌فرض توضیحات")
        remarks_layout = QVBoxLayout(remarks_group)
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        remarks_layout.addWidget(self.remarks_edit)
        self.main_layout.addWidget(remarks_group)

        # --- Calculation Settings Section ---
        calc_group = QGroupBox("تنظیمات محاسبات")
        calc_layout = QFormLayout(calc_group)
        self.emergency_basis_combo = QComboBox()
        self.emergency_basis_combo.addItems(["هزینه ترجمه", "جمع کل هزینه‌ها"])
        calc_layout.addRow("مبنای محاسبه هزینه فوریت:", self.emergency_basis_combo)
        self.main_layout.addWidget(calc_group)

        # --- Default Language Settings Section ---
        lang_group = QGroupBox("تنظیمات پیش‌فرض زبان")
        lang_layout = QFormLayout(lang_group)
        self.source_lang_combo = QComboBox()
        self.target_lang_combo = QComboBox()
        languages = [lang.value for lang in Language]
        self.source_lang_combo.addItems(languages)
        self.target_lang_combo.addItems(languages)
        lang_layout.addRow("زبان مبدأ پیش‌فرض:", self.source_lang_combo)
        lang_layout.addRow("زبان مقصد پیش‌فرض:", self.target_lang_combo)
        self.main_layout.addWidget(lang_group)

        # --- Visibility Settings Section ---
        visibility_group = QGroupBox("نمایش بخش‌ها")
        visibility_layout = QFormLayout(visibility_group)
        self.invoice_visibility_check = QCheckBox("اطلاعات فاکتور")
        self.customer_visibility_check = QCheckBox("اطلاعات مشتری")
        self.financial_visibility_check = QCheckBox("اطلاعات مالی")
        self.office_visibility_check = QCheckBox("اطلاعات دارالترجمه")
        visibility_layout.addRow(self.invoice_visibility_check)
        visibility_layout.addRow(self.customer_visibility_check)
        visibility_layout.addRow(self.financial_visibility_check)
        visibility_layout.addRow(self.office_visibility_check)
        self.main_layout.addWidget(visibility_group)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("انصراف")
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

        self._load_current_settings()

    def _load_current_settings(self):
        """Populates the dialog widgets with values from the SettingsManager."""
        self.remarks_edit.setPlainText(self.settings_manager.get("default_remarks"))

        basis = self.settings_manager.get("emergency_basis")
        self.emergency_basis_combo.setCurrentIndex(1 if basis == "total_before_discount" else 0)

        self.source_lang_combo.setCurrentText(self.settings_manager.get("default_source_language"))
        self.target_lang_combo.setCurrentText(self.settings_manager.get("default_target_language"))

        visibility = self.settings_manager.get("group_box_visibility")
        self.invoice_visibility_check.setChecked(visibility.get("invoice", True))
        self.customer_visibility_check.setChecked(visibility.get("customer", True))
        self.financial_visibility_check.setChecked(visibility.get("financial", True))
        self.office_visibility_check.setChecked(visibility.get("office", True))

    def _on_save(self):
        """Saves the current widget values back to the SettingsManager and accepts the dialog."""
        self.settings_manager.set("default_remarks", self.remarks_edit.toPlainText())

        basis = "total_before_discount" if self.emergency_basis_combo.currentIndex() == 1 else "translation_cost"
        self.settings_manager.set("emergency_basis", basis)

        self.settings_manager.set("default_source_language", self.source_lang_combo.currentText())
        self.settings_manager.set("default_target_language", self.target_lang_combo.currentText())

        visibility = {
            "invoice": self.invoice_visibility_check.isChecked(),
            "customer": self.customer_visibility_check.isChecked(),
            "financial": self.financial_visibility_check.isChecked(),
            "office": self.office_visibility_check.isChecked()
        }
        self.settings_manager.set("group_box_visibility", visibility)
        self.settings_manager.save()

        self.accept()
