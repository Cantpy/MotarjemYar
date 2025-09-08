"""services_documents_view.py - Documents management _view using PySide6"""

from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton,
    QLineEdit, QTableWidget, QDialog, QTableWidgetItem, QMenu, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from services_management_controller import ServicesController


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

    def get_values(self) -> Dict[str, str]:
        """Get values from input fields"""
        return {key: widget.text().strip() for key, widget in self.inputs.items()}

    def set_values(self, values: Dict[str, str]):
        """Set values in input fields"""
        for key, value in values.items():
            if key in self.inputs:
                self.inputs[key].setText(str(value) if value is not None else "")


class ServicesDocumentsView(QWidget):
    """Widget for managing services/documents with CRUD operations and search functionality."""

    COLUMN_HEADERS = ["انتخاب", "نام مدرک", "هزینه ترجمه", "نام متغیر ۱", "هزینه متغیر ۱",
                      "نام متغیر ۲", "هزینه متغیر ۲"]
    COLUMN_WIDTHS = [8, 37, 10, 12, 9, 10, 10]  # Percentage widths

    def __init__(self, controller: ServicesController, parent=None):
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
        self.search_bar.setPlaceholderText("جستجوی خدمات...")
        self.search_bar.textChanged.connect(self._filter_services)
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
        """Configure the services table."""
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Enable sorting for all columns except checkbox column
        for i in range(1, len(self.COLUMN_HEADERS)):
            self.table.horizontalHeader().setSortIndicatorShown(True)

        # Disable sorting for checkbox column
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

        self.main_layout.addWidget(self.table)

    def _setup_buttons(self):
        """Create and configure action buttons."""
        button_layout = QHBoxLayout()

        self.add_by_excel_btn = QPushButton("افزودن با اکسل")
        self.add_btn = QPushButton("➕ اضافه کردن مدرک")
        self.edit_btn = QPushButton("✏️ ویرایش مدرک")
        self.delete_btn = QPushButton("🗑️ حذف مدرک")

        buttons = [self.add_by_excel_btn, self.add_btn, self.edit_btn, self.delete_btn]
        for button in buttons:
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        self.add_btn.clicked.connect(self._show_add_dialog)
        self.edit_btn.clicked.connect(self._show_edit_dialog)
        self.delete_btn.clicked.connect(self._delete_selected_service)
        self.add_by_excel_btn.clicked.connect(self._import_from_excel)

        # Connect controller signals
        self.controller.data_changed.connect(self._load_data)

    def _create_checkbox_widget(self, row):
        """Create a checkbox widget for a table row."""
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda state, r=row: self._on_row_checkbox_changed(r, state))

        # Center the checkbox in the cell
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        return widget, checkbox

    def _on_row_checkbox_changed(self, row, state):
        """Handle individual row checkbox state change."""
        self._update_selection_ui()

    def _toggle_select_all(self):
        """Toggle all checkboxes based on select all checkbox state."""
        is_checked = self.select_all_checkbox.isChecked()

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):  # Only affect visible rows
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    # Get the checkbox from the layout
                    layout = checkbox_widget.layout()
                    if layout and layout.count() > 0:
                        checkbox = layout.itemAt(0).widget()
                        if isinstance(checkbox, QCheckBox):
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
        self.select_all_checkbox.blockSignals(False)

    def _get_selected_count(self):
        """Get the number of selected visible rows."""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        count += 1
        return count

    def _get_visible_count(self):
        """Get the number of visible rows."""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                count += 1
        return count

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

    def _bulk_delete_selected(self):
        """Delete all selected services."""
        selected_rows = self._get_selected_rows()

        if not selected_rows:
            return

        # Get service IDs and names for confirmation
        service_ids = []
        service_names = []

        for row in selected_rows:
            service_id = self.row_to_id_mapping.get(row)
            name_item = self.table.item(row, 1)  # Name is in column 1
            if service_id and name_item:
                service_ids.append(service_id)
                service_names.append(name_item.text())

        if not service_ids:
            return

        # Show confirmation dialog
        def confirm_delete():
            return self._show_confirmation_dialog(
                "حذف گروهی",
                f"آیا مطمئن هستید که می‌خواهید {len(service_ids)} مدرک انتخابی را حذف کنید؟"
            )

        if self.controller.delete_multiple_services(service_ids):
            # Data will be refreshed automatically via signal
            pass

    def _filter_services(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.strip().lower()
        for row in range(self.table.rowCount()):
            service_name_item = self.table.item(row, 1)  # Name is in column 1
            if service_name_item:
                service_name = service_name_item.text().lower()
                self.table.setRowHidden(row, search_text not in service_name)

        # Update selection UI when filtering
        self._update_selection_ui()

    def _show_context_menu(self, position):
        """Display context menu for table row operations."""
        selected_row = self.table.indexAt(position).row()
        if selected_row == -1:
            return

        context_menu = QMenu(self)

        edit_action = QAction("ویرایش", self)
        edit_action.triggered.connect(self._show_edit_dialog)
        context_menu.addAction(edit_action)

        remove_action = QAction("حذف", self)
        remove_action.triggered.connect(lambda: self._delete_service_by_row(selected_row))
        context_menu.addAction(remove_action)

        # Add bulk operations to context menu if multiple rows are selected
        selected_count = self._get_selected_count()
        if selected_count > 1:
            context_menu.addSeparator()
            bulk_delete_action = QAction(f"حذف {selected_count} مورد انتخابی", self)
            bulk_delete_action.triggered.connect(self._bulk_delete_selected)
            context_menu.addAction(bulk_delete_action)

        context_menu.exec(self.table.viewport().mapToGlobal(position))

    def _load_data(self):
        """Load services data into the table."""
        # Temporarily disable sorting while populating
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()

        services = self.controller.get_cached_data()

        for row_number, service in enumerate(services):
            self.table.insertRow(row_number)

            # Store ID mapping
            self.row_to_id_mapping[row_number] = service['id']

            # Add checkbox in first column
            checkbox_widget, checkbox = self._create_checkbox_widget(row_number)
            self.table.setCellWidget(row_number, 0, checkbox_widget)

            # Add data in remaining columns
            data_fields = [
                service['name'],
                service['base_price'],
                service['dynamic_price_name_1'] or '',
                service['dynamic_price_1'],
                service['dynamic_price_name_2'] or '',
                service['dynamic_price_2']
            ]

            for column_number, data in enumerate(data_fields):
                item = self._create_table_item(data)
                self.table.setItem(row_number, column_number + 1, item)

        # Re-enable sorting
        self.table.setSortingEnabled(True)
        # Update selection UI
        self._update_selection_ui()

    def _create_table_item(self, value):
        """Create a table widget item with proper formatting."""
        if value is None:
            display_text = ""
        elif isinstance(value, int):
            # Format integers with thousand separators and convert to Persian if needed
            display_text = f"{value:,}" if value != 0 else ""
        else:
            display_text = str(value)

        item = QTableWidgetItem(display_text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _show_add_dialog(self):
        """Show add service dialog."""
        dialog = InputDialog("افزودن مدرک جدید", self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            # Map dialog values to service data format
            service_data = {
                'name': values.get('document_name', ''),
                'base_price': values.get('base_cost', ''),
                'dynamic_price_name_1': values.get('variable_name_1', ''),
                'dynamic_price_1': values.get('variable_cost_1', ''),
                'dynamic_price_name_2': values.get('variable_name_2', ''),
                'dynamic_price_2': values.get('variable_cost_2', '')
            }

            self.controller.create_service(service_data)

    def _show_edit_dialog(self):
        """Show edit service dialog."""
        row = self.table.currentRow()
        if row == -1:
            return

        service_id = self.row_to_id_mapping.get(row)
        if not service_id:
            return

        # Get current row data
        current_data = {}
        field_mapping = {
            0: "document_name",  # Name (column 1 in table)
            1: "base_cost",  # Base cost (column 2 in table)
            2: "variable_name_1",  # Variable name 1 (column 3 in table)
            3: "variable_cost_1",  # Variable cost 1 (column 4 in table)
            4: "variable_name_2",  # Variable name 2 (column 5 in table)
            5: "variable_cost_2"  # Variable cost 2 (column 6 in table)
        }

        for col_index, field_key in field_mapping.items():
            item = self.table.item(row, col_index + 1)  # +1 because of checkbox column
            current_data[field_key] = item.text() if item else ""

        dialog = InputDialog("ویرایش مدرک", self)
        dialog.set_values(current_data)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            # Map dialog values to service data format
            service_data = {
                'name': values.get('document_name', ''),
                'base_price': values.get('base_cost', ''),
                'dynamic_price_name_1': values.get('variable_name_1', ''),
                'dynamic_price_1': values.get('variable_cost_1', ''),
                'dynamic_price_name_2': values.get('variable_name_2', ''),
                'dynamic_price_2': values.get('variable_cost_2', '')
            }

            self.controller.update_service(service_id, service_data)

    def _delete_selected_service(self):
        """Delete the currently selected service."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            self._delete_service_by_row(selected_row)

    def _delete_service_by_row(self, row):
        """Delete a service by table row index."""
        service_id = self.row_to_id_mapping.get(row)
        name_item = self.table.item(row, 1)  # Name is in column 1

        if not service_id or not name_item:
            return

        service_name = name_item.text()

        # Show confirmation dialog
        if self._show_confirmation_dialog(
                "حذف",
                f"آیا مطمئن هستید که می‌خواهید '{service_name}' را حذف کنید؟"
        ):
            self.controller.delete_service(service_id, service_name)

    def _import_from_excel(self):
        """Import services from Excel file."""

        def confirm_import():
            return self._show_confirmation_dialog(
                "بارگذاری از طریق فایل اکسل",
                "با بارگذاری مدارک از طریق اکسل تغییرات قبلی که در این جدول انجام داده‌اید از بین خواهد رفت.\n"
                "آیا از انجام این کار مطمئن هستید؟\n\n"
                "توجه: تمامی تغییرات اعمال شده در فایل اکسل با انجام این‌کار اعمال خواهند شد."
            )

        # Use a timer to delay the actual import to allow dialog to close
        if self.controller.import_from_excel(confirm_import):
            QTimer.singleShot(100, lambda: None)  # Small delay for UI update

    def _show_confirmation_dialog(self, title: str, message: str) -> bool:
        """Show confirmation dialog and return True if user confirms."""
        try:
            from modules.helper_functions import show_question_message_box
            result = [False]  # Use list to capture result from nested function

            def on_yes():
                result[0] = True

            show_question_message_box(
                parent=self,
                title=title,
                message=message,
                button_1="بله، مطمئنم",
                button_2="خیر",
                yes_func=on_yes
            )

            return result[0]
        except ImportError:
            # Fallback to simple print
            print(f"Confirmation needed - {title}: {message}")
            return True

    def resizeEvent(self, event):
        """Adjust column widths dynamically on window resize."""
        super().resizeEvent(event)
        table_width = self.table.width()
        for i, percentage in enumerate(self.COLUMN_WIDTHS):
            if i == 0:  # Checkbox column - fixed width
                self.table.setColumnWidth(i, 60)
            else:
                self.table.setColumnWidth(i, table_width * percentage // 100)
