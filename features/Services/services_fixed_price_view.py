"""services_fixed_prices_view.py - Fixed prices management _view using PySide6"""

from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton,
    QLineEdit, QTableWidget, QDialog, QTableWidgetItem, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from services_management_controller import FixedPricesController


class SimpleInputDialog(QDialog):
    """Simple input dialog for fixed price data entry"""

    def __init__(self, title: str = "اضافه کردن هزینه ثابت", parent=None):
        super().__init__(parent)
        self.inputs = {}
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """Setup dialog UI"""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout()

        # Input fields
        fields = [
            ("نام هزینه ثابت", "service_name"),
            ("هزینه", "cost")
        ]

        for label_text, field_key in fields:
            row_layout = QHBoxLayout()

            label = QLabel(label_text)
            label.setMinimumWidth(100)
            line_edit = QLineEdit()

            if "هزینه" in label_text:
                line_edit.setPlaceholderText("مثال: 10000")

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

    def get_values(self) -> Dict[str, str]:
        """Get values from input fields"""
        return {key: widget.text().strip() for key, widget in self.inputs.items()}

    def set_values(self, values: Dict[str, str]):
        """Set values in input fields"""
        for key, value in values.items():
            if key in self.inputs:
                self.inputs[key].setText(str(value) if value is not None else "")


class ServicesFixedPricesView(QWidget):
    """Widget for managing fixed prices with CRUD operations and search functionality."""

    COLUMN_HEADERS = ["انتخاب", "هزینه‌های ثابت", "هزینه"]
    COLUMN_WIDTHS = [15, 55, 30]  # Percentage widths

    def __init__(self, controller: FixedPricesController, parent=None):
        super().__init__()
        self.controller = controller
        self.parent_window = parent
        self.row_to_id_mapping = {}

        self._setup_ui()
        self._connect_signals()
        self._load_data()

    def _setup_ui(self):
        """Initialize and configure UI components."""
        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Search bar
        self._setup_search_bar()

        # Selection controls
        self._setup_selection_controls()

        # Table
        self._setup_table()

        # Buttons
        self._setup_buttons()

    def _setup_search_bar(self):
        """Set up the search functionality."""
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی هزینه‌های ثابت...")
        self.search_bar.textChanged.connect(self._filter_prices)
        self.main_layout.addWidget(self.search_bar)

    def _setup_selection_controls(self):
        """Set up bulk selection controls."""
        selection_layout = QHBoxLayout()

        # Select all checkbox
        self.select_all_checkbox = QCheckBox("انتخاب همه")
        self.select_all_checkbox.stateChanged.connect(self._toggle_select_all)
        selection_layout.addWidget(self.select_all_checkbox)

        # Selected count label
        self.selected_count_label = QLabel("0 مورد انتخاب شده")
        selection_layout.addWidget(self.selected_count_label)

        selection_layout.addStretch()

        # Bulk delete button
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        self.bulk_delete_btn.clicked.connect(self._bulk_delete_selected)
        selection_layout.addWidget(self.bulk_delete_btn)

        self.main_layout.addLayout(selection_layout)

    def _setup_table(self):
        """Configure the fixed prices table."""
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Make the checkbox column non-sortable
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().setSectionsClickable(True)

        self.main_layout.addWidget(self.table)

    def _setup_buttons(self):
        """Create and configure action buttons."""
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ اضافه کردن هزینه ثابت")
        self.edit_btn = QPushButton("✏️ ویرایش هزینه ثابت")
        self.delete_btn = QPushButton("🗑️ حذف هزینه ثابت")

        buttons = [self.add_btn, self.edit_btn, self.delete_btn]
        for button in buttons:
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        self.add_btn.clicked.connect(self._show_add_dialog)
        self.edit_btn.clicked.connect(self._show_edit_dialog)
        self.delete_btn.clicked.connect(self._delete_selected_price)

        # Connect controller signals
        self.controller.data_changed.connect(self._load_data)

    def _create_checkbox_widget(self):
        """Create a checkbox widget for table cells."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(checkbox)

        return widget

    def _on_checkbox_changed(self):
        """Handle individual checkbox state change."""
        self._update_selection_ui()

    def _get_selected_rows(self):
        """Get list of selected row indices."""
        selected_rows = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_rows.append(row)
        return selected_rows

    def _get_selected_count(self):
        """Get count of selected rows."""
        return len(self._get_selected_rows())

    def _get_visible_count(self):
        """Get count of visible rows."""
        visible_count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                visible_count += 1
        return visible_count

    def _bulk_delete_selected(self):
        """Delete all selected fixed prices."""
        selected_rows = self._get_selected_rows()

        if not selected_rows:
            return

        # Get price IDs and names for confirmation
        price_ids = []
        price_names = []

        for row in selected_rows:
            price_id = self.row_to_id_mapping.get(row)
            name_item = self.table.item(row, 1)  # Name is in column 1
            if price_id and name_item:
                price_ids.append(price_id)
                price_names.append(name_item.text())

        if not price_ids:
            return

        # Show confirmation dialog
        def confirm_delete():
            services_text = "\n".join(price_names[:5])
            if len(price_names) > 5:
                services_text += f"\n... و {len(price_names) - 5} مورد دیگر"

            return self._show_confirmation_dialog(
                "حذف چندگانه",
                f"آیا مطمئن هستید که می‌خواهید موارد زیر را حذف کنید؟\n\n{services_text}"
            )

        if confirm_delete():
            self.controller.delete_multiple_fixed_prices(price_ids)

    def _toggle_select_all(self):
        """Toggle all checkboxes based on select all checkbox state."""
        is_checked = self.select_all_checkbox.isChecked()

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):  # Only affect visible rows
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.blockSignals(True)  # Prevent recursive calls
                        checkbox.setChecked(is_checked)
                        checkbox.blockSignals(False)

        self._update_selection_ui()

    def _update_selection_ui(self):
        """Update the selection UI elements (count label, buttons)."""
        selected_count = self._get_selected_count()
        total_visible = self._get_visible_count()

        # Update count label
        self.selected_count_label.setText(f"{selected_count} مورد انتخاب شده")

        # Update bulk delete button state
        self.bulk_delete_btn.setEnabled(selected_count > 0)

        # Update select all checkbox state
        self.select_all_checkbox.blockSignals(True)
        if selected_count == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        elif selected_count == total_visible:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    from shared import return_resource

    services_database = return_resource('databases', 'services.db')

    app = QApplication(sys.argv)
    controller = FixedPricesController(services_database)
    view = ServicesFixedPricesView(controller)
    view.show()
    sys.exit(app.exec())
