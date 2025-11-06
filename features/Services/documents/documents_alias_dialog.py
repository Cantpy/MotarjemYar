# features/Services/documents/alias_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame, QSpinBox,
    QPushButton, QLineEdit, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt


class ServicePropertiesDialog(QDialog):
    """A dialog for managing properties for a service, including aliases and page count."""

    def __init__(self, service_name: str, service_aliases: list[str],
                 default_page_count: int, dynamic_prices_data: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"ویرایش جزئیات: {service_name}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(500)

        # Store initial data
        self._dynamic_prices_data = dynamic_prices_data

        # Main layout
        layout = QVBoxLayout(self)

        # --- General Properties Section ---
        self._setup_general_properties(layout, default_page_count)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # --- Service Aliases Section ---
        service_group = self._create_alias_group("نام مستعار سرویس اصلی", service_aliases)
        layout.addLayout(service_group)

        # --- Dynamic Prices Aliases Section ---
        for price_data in self._dynamic_prices_data:
            if price_data.get('name'):
                price_group = self._create_alias_group(
                    f"نام مستعار برای: {price_data['name']}",
                    price_data.get('aliases', [])
                )
                layout.addLayout(price_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _setup_general_properties(self, parent_layout: QVBoxLayout, current_page_count: int):
        """Creates the UI for non-alias properties like page count."""
        properties_layout = QHBoxLayout()
        properties_layout.addWidget(QLabel("تعداد صفحات پیش‌فرض:"))

        self.page_count_spinbox = QSpinBox()
        self.page_count_spinbox.setMinimumWidth(100)
        self.page_count_spinbox.setMinimum(1)
        self.page_count_spinbox.setMaximum(1000)
        self.page_count_spinbox.setValue(current_page_count)
        properties_layout.addWidget(self.page_count_spinbox)
        properties_layout.addStretch()

        parent_layout.addLayout(properties_layout)

    def _create_alias_group(self, title: str, aliases: list[str]) -> QVBoxLayout:
        """Helper to create a self-contained widget group for managing a list of aliases."""
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>{title}</b>"))

        list_widget = QListWidget()
        if aliases:
            list_widget.addItems(aliases)
        layout.addWidget(list_widget)

        # --- Input and Buttons Layout ---
        input_layout = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("نام مستعار جدید را وارد کنید...")
        add_btn = QPushButton("افزودن")
        remove_btn = QPushButton("حذف")

        input_layout.addWidget(line_edit)
        input_layout.addWidget(add_btn)
        input_layout.addWidget(remove_btn)
        layout.addLayout(input_layout)

        # --- Connections ---
        add_btn.clicked.connect(lambda: self._add_alias(line_edit, list_widget))
        remove_btn.clicked.connect(lambda: self._remove_alias(list_widget))
        line_edit.returnPressed.connect(lambda: self._add_alias(line_edit, list_widget))
        list_widget.itemDoubleClicked.connect(self._edit_alias)

        list_widget.setObjectName(title)
        return layout

    def _add_alias(self, line_edit: QLineEdit, list_widget: QListWidget):
        alias_text = line_edit.text().strip()
        if alias_text:
            if not list_widget.findItems(alias_text, Qt.MatchFlag.MatchExactly):
                list_widget.addItem(alias_text)
                line_edit.clear()
            else:
                QMessageBox.warning(self, "تکراری", "این نام مستعار از قبل وجود دارد.")
        line_edit.setFocus()

    def _remove_alias(self, list_widget: QListWidget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def _edit_alias(self, item: QListWidgetItem):
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.sender().editItem(item)

    def get_updated_data(self) -> dict:
        """Retrieves all updated properties from the dialog."""
        output = {
            "default_page_count": self.page_count_spinbox.value(),
            "service_aliases": [],
            "dynamic_price_aliases": []
        }

        service_list_widget = self.findChild(QListWidget, "نام مستعار سرویس اصلی")
        if service_list_widget:
            output["service_aliases"] = [service_list_widget.item(i).text() for i in range(service_list_widget.count())]

        for price_data in self._dynamic_prices_data:
            if price_data.get('name'):
                price_list_widget = self.findChild(QListWidget, f"نام مستعار برای: {price_data['name']}")
                if price_list_widget:
                    aliases = [price_list_widget.item(j).text() for j in range(price_list_widget.count())]
                    output["dynamic_price_aliases"].append({
                        "id": price_data.get('id'),
                        "aliases": aliases
                    })
        return output
