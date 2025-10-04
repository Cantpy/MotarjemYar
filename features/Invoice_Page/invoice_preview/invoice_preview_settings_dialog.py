# features/Invoice_Page/invoice_preview/invoice_preview_settings_dialog.py

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGroupBox, QFormLayout, QCheckBox,
                               QSpinBox, QDialogButtonBox)


class SettingsDialog(QDialog):
    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات نمایش فاکتور")
        self.setMinimumWidth(450)
        # Store a copy of the settings to be modified
        self._settings = current_settings.copy()

        # Main layout
        self.main_layout = QVBoxLayout(self)

        # --- Checkboxes ---
        # (The checkbox definitions remain the same)
        self.header_checks = {
            "show_representative": QCheckBox("مترجم مسئول"),
            "show_address": QCheckBox("آدرس دارالترجمه"),
            "show_phone": QCheckBox("تلفن دارالترجمه"),
            "show_email": QCheckBox("ایمیل دارالترجمه"),
            "show_telegram": QCheckBox("تلگرام"),
            "show_whatsapp": QCheckBox("واتساپ"),
            "show_website": QCheckBox("وبسایت"),
            "show_issuer": QCheckBox("صادر کننده"),
            "show_logo": QCheckBox("لوگو")
        }
        self.customer_checks = {
            "show_national_id": QCheckBox("کد ملی مشتری"),
            "show_phone": QCheckBox("شماره همراه مشتری"),
            "show_address": QCheckBox("آدرس مشتری")
        }
        self.footer_checks = {
            "show_subtotal": QCheckBox("جمع جزء"),
            "show_emergency_cost": QCheckBox("هزینه فوریت"),
            "show_discount": QCheckBox("تخفیف"),
            "show_advance_payment": QCheckBox("پیش پرداخت"),
            "show_remarks": QCheckBox("توضیحات"),
            "show_signature": QCheckBox("امضا و مهر"),
            "show_page_number": QCheckBox("شماره صفحه")
        }

        # --- UI Structure ---
        self.main_layout.addWidget(self._create_group_box("بخش‌های قابل نمایش سربرگ", self.header_checks))
        self.main_layout.addWidget(self._create_group_box("بخش‌های قابل نمایش مشتری", self.customer_checks))
        self.main_layout.addWidget(self._create_group_box("بخش‌های قابل نمایش انتهای فاکتور", self.footer_checks))

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)

        self._populate_fields()

    def _create_group_box(self, title: str, checks: dict) -> QGroupBox:
        group_box = QGroupBox(title)
        layout = QFormLayout(group_box)
        for check in checks.values():
            layout.addRow(check)
        return group_box

    def _populate_fields(self):
        """Fills the UI elements with the current settings."""
        self._populate_group(self._settings.get("header_visibility", {}), self.header_checks)
        self._populate_group(self._settings.get("customer_visibility", {}), self.customer_checks)
        self._populate_group(self._settings.get("footer_visibility", {}), self.footer_checks)

    def _populate_group(self, settings_group: dict, checks_group: dict):
        for key, checkbox in checks_group.items():
            checkbox.setChecked(settings_group.get(key, True))

    def get_new_settings(self) -> dict:
        """
        Reads the values from the UI and updates the original settings dictionary
        to ensure non-UI-related settings (like pagination) are preserved.
        """
        self._settings["header_visibility"] = {key: check.isChecked() for key, check in self.header_checks.items()}
        self._settings["customer_visibility"] = {key: check.isChecked() for key, check in self.customer_checks.items()}
        self._settings["footer_visibility"] = {key: check.isChecked() for key, check in self.footer_checks.items()}

        # Return the complete, updated dictionary.
        return self._settings
