"""services_other_view.py - Other services management _view using PySide6"""

from typing import Dict, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton,
    QLineEdit, QTableWidget, QDialog, QTableWidgetItem, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from services_management_controller import OtherServicesController


class SimpleInputDialog(QDialog):
    """Simple input dialog for other service data entry"""

    def __init__(self, title: str = "اضافه کردن خدمت", parent=None):
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
            ("نام خدمت", "service_name"),
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


class ServicesOtherView(QWidget):
    """Widget for managing other services with CRUD operations and search functionality."""

    COLUMN_HEADERS = ["انتخاب", "خدمات", "هزینه"]
    COLUMN_WIDTHS = [15, 55, 30]  # Percentage widths

    def __init__(self, controller: OtherServicesController, parent=None):
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
        self.search_bar.setPlaceholderText("جستجوی سایر خدمات...")
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
        """Configure the other services table."""
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

        self.add_btn = QPushButton("➕ اضافه کردن خدمت")
        self.edit_btn = QPushButton("✏️ ویرایش خدمت")
        self.delete_btn = QPushButton("🗑️ حذف خدمت")

        buttons = [self.add_btn, self.edit_btn, self.delete_btn]
        for button in buttons:
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        self.add_btn.clicked.connect(self._show_add_dialog)
        self.edit_btn.clicked.connect(self._show_edit_dialog)
        self.delete_btn.clicked.connect(self._delete_selected_service)

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
        """Delete all selected other services."""
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
            services_text = "\n".join(service_names[:5])
            if len(service_names) > 5:
                services_text += f"\n... و {len(service_names) - 5} مورد دیگر"

            return self._show_confirmation_dialog(
                "حذف چندگانه",
                f"آیا مطمئن هستید که می‌خواهید موارد زیر را حذف کنید؟\n\n{services_text}"
            )

        if confirm_delete():
            self.controller.delete_multiple_other_services(service_ids)

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
        self.select_all_checkbox.blockSignals(False)

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

        # Only show delete option for non-default items
        if not self._is_default_service(selected_row):
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
        """Load other services data into the table."""
        # Temporarily disable sorting while populating
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()

        other_services = self.controller.get_cached_data()

        for row_number, service in enumerate(other_services):
            self.table.insertRow(row_number)

            # Store ID mapping
            self.row_to_id_mapping[row_number] = service['id']

            # Add checkbox in first column
            checkbox_widget = self._create_checkbox_widget()
            self.table.setCellWidget(row_number, 0, checkbox_widget)

            # Add name and price items
            name_item = QTableWidgetItem(str(service['name']))
            price_item = QTableWidgetItem(str(service['price']))

            # Set data for proper sorting
            price_item.setData(Qt.ItemDataRole.UserRole, service['price'])  # Store numeric value for sorting

            self.table.setItem(row_number, 1, name_item)
            self.table.setItem(row_number, 2, price_item)

        # Re-enable sorting
        self.table.setSortingEnabled(True)
        # Update selection UI
        self._update_selection_ui()

    def _show_add_dialog(self):
        """Show add other service dialog."""
        dialog = SimpleInputDialog("افزودن سایر خدمات جدید", self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            # Map dialog values to other service data format
            service_data = {
                'name': values.get('service_name', ''),
                'price': values.get('cost', '')
            }

            self.controller.create_other_service(service_data)

    def _show_edit_dialog(self):
        """Show edit other service dialog."""
        row = self.table.currentRow()
        if row == -1:
            return

        service_id = self.row_to_id_mapping.get(row)
        if not service_id:
            return

        # Get current row data
        name_item = self.table.item(row, 1)  # Name is in column 1
        price_item = self.table.item(row, 2)  # Price is in column 2

        if not name_item or not price_item:
            return

        current_data = {
            'service_name': name_item.text(),
            'cost': price_item.text()
        }

        dialog = SimpleInputDialog("ویرایش سایر خدمات", self)
        dialog.set_values(current_data)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            # Map dialog values to other service data format
            service_data = {
                'name': values.get('service_name', ''),
                'price': values.get('cost', '')
            }

            self.controller.update_other_service(service_id, service_data)

    def _delete_selected_service(self):
        """Delete the currently selected other service."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            self._delete_service_by_row(selected_row)

    def _delete_service_by_row(self, row):
        """Delete an other service by table row index."""
        service_id = self.row_to_id_mapping.get(row)
        name_item = self.table.item(row, 1)  # Name is in column 1

        if not service_id or not name_item:
            return

        # Check if it's a default service
        if self._is_default_service(row):
            try:
                from modules.helper_functions import show_warning_message_box
                show_warning_message_box(self, "خطا", "نمی‌توانید خدمات پیش‌فرض را حذف کنید!")
            except ImportError:
                print("Cannot delete default services!")
            return

        service_name = name_item.text()

        # Show confirmation dialog
        if self._show_confirmation_dialog(
                "حذف",
                f"آیا مطمئن هستید که می‌خواهید '{service_name}' را حذف کنید؟"
        ):
            self.controller.delete_other_service(service_id, service_name)

    def _is_default_service(self, row):
        """Check if the service at given row is a default service."""
        # This method should check against database data for is_default field
        # For now, we'll return False as a placeholder
        return False

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
        if hasattr(self, 'table'):
            table_width = self.table.width()
            for i, percentage in enumerate(self.COLUMN_WIDTHS):
                self.table.setColumnWidth(i, table_width * percentage // 100)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    from shared import return_resource

    services_database = return_resource('databases', 'services.db')

    app = QApplication(sys.argv)
    controller = OtherServicesController(services_database)
    view = ServicesOtherView(controller)
    view.show()
    sys.exit(app.exec())
