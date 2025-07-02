from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton, QLineEdit,
                               QTableWidget, QDialog, QTableWidgetItem, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from modules.helper_functions import show_question_message_box, show_warning_message_box, show_error_message_box
from modules.Documents.helper_functions import InputDialog
from modules.Documents.backend.fixed_costs_backend import FixedCostsService
from typing import Dict, Optional


class FixedCostsWidget(QWidget):
    """Widget for managing fixed costs with CRUD operations and search functionality."""

    COLUMN_HEADERS = ["انتخاب", "هزینه‌های ثابت", "هزینه"]
    COLUMN_WIDTHS = [15, 55, 30]  # Percentage widths - added checkbox column

    def __init__(self):
        super().__init__()
        # Initialize service
        self.service = FixedCostsService()

        # Store ID mapping: row_index -> database_id
        self.row_to_id_mapping = {}

        self._setup_ui()
        self._connect_signals()
        self.load_fixed_costs()

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

    def _setup_search_bar(self):
        """Set up the search functionality."""
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی هزینه‌های ثابت...")
        self.search_bar.textChanged.connect(self._filter_costs)
        self.main_layout.addWidget(self.search_bar)

    def _setup_table(self):
        """Configure the fixed costs table."""
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
        self.edit_btn.clicked.connect(self._edit_selected_cost)
        self.delete_btn.clicked.connect(self._delete_selected_cost)

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

    def _filter_costs(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.strip().lower()
        for row in range(self.table.rowCount()):
            cost_name_item = self.table.item(row, 1)  # Name is in column 1
            if cost_name_item:
                cost_name = cost_name_item.text().lower()
                self.table.setRowHidden(row, search_text not in cost_name)

        # Update selection UI when filtering
        self._update_selection_ui()

    def _show_context_menu(self, position):
        """Display context menu for table row operations."""
        selected_row = self.table.indexAt(position).row()
        if selected_row == -1:
            return

        context_menu = QMenu(self)

        edit_action = QAction("ویرایش", self)
        edit_action.triggered.connect(lambda: self._edit_cost_by_row(selected_row))
        context_menu.addAction(edit_action)

        # Only show delete option for non-default items
        if not self._is_default_cost(selected_row):
            remove_action = QAction("حذف", self)
            remove_action.triggered.connect(lambda: self._delete_cost_by_row(selected_row))
            context_menu.addAction(remove_action)

        context_menu.exec(self.table.viewport().mapToGlobal(position))

    def resizeEvent(self, event):
        """Adjust column widths dynamically on window resize."""
        super().resizeEvent(event)
        if hasattr(self, 'table'):
            table_width = self.table.width()
            for i, percentage in enumerate(self.COLUMN_WIDTHS):
                self.table.setColumnWidth(i, table_width * percentage // 100)

    def load_fixed_costs(self):
        """Load fixed costs from database and populate the table."""
        # Disable sorting temporarily to avoid issues during population
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()

        try:
            costs = self.service.get_all_fixed_costs()

            for row_number, cost in enumerate(costs):
                self.table.insertRow(row_number)

                # Store the ID mapping
                self.row_to_id_mapping[row_number] = cost.id

                # Add checkbox in first column
                checkbox_widget = self._create_checkbox_widget()
                self.table.setCellWidget(row_number, 0, checkbox_widget)

                # Add name and price items
                name_item = QTableWidgetItem(str(cost.name))
                price_item = QTableWidgetItem(str(cost.price))

                # Set data for proper sorting
                price_item.setData(Qt.ItemDataRole.UserRole, cost.price)

                # Make default items visually distinct
                if cost.is_default:
                    name_item.setBackground(Qt.GlobalColor.lightGray)
                    price_item.setBackground(Qt.GlobalColor.lightGray)

                self.table.setItem(row_number, 1, name_item)
                self.table.setItem(row_number, 2, price_item)

        except Exception as e:
            message = f"خطا در بارکذاری هزینه‌های ثابت:\n{str(e)}"
            show_error_message_box(self, "خطا", message)

        finally:
            # Re-enable sorting
            self.table.setSortingEnabled(True)
            # Update selection UI
            self._update_selection_ui()

    def _get_cost_id_by_row(self, row):
        """Get the database ID for a given table row."""
        return self.row_to_id_mapping.get(row)

    def _is_default_cost(self, row):
        """Check if a cost is a default (non-deletable) cost."""
        try:
            cost_id = self._get_cost_id_by_row(row)
            if cost_id is None:
                return False

            # Get the cost from service to check if it's default
            cost = self.service.get_fixed_cost_by_id(cost_id)
            return cost.is_default if cost else False
        except Exception:
            return False

    def _show_add_dialog(self) -> Optional[Dict[str, str]]:
        """Show dialog to add a new fixed cost."""
        dialog = InputDialog("FixedCostsWidget", self)
        dialog.setWindowTitle("افزودن هزینه ثابت جدید")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the values and map them to our expected format
            values = dialog.get_values()
            data = {
                'fixed_cost': values.get('service_name', ''),
                'cost': values.get('cost', '')
            }
            if self.service.add_fixed_cost(self, data):
                self.load_fixed_costs()  # Reload to update the table and ID mapping
        return None

    def _show_edit_dialog(self, current_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Show edit dialog with current data pre-filled."""
        dialog = InputDialog("FixedCostsWidget", self)
        dialog.setWindowTitle("ویرایش هزینه ثابت")

        # Pre-fill the dialog with current data
        dialog_data = {
            'service_name': current_data.get('fixed_cost', ''),
            'cost': current_data.get('cost', '')
        }

        # Set the values in the dialog
        for key, value in dialog_data.items():
            if key in dialog.inputs:
                dialog.inputs[key].setText(str(value))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the values and map them back to our expected format
            values = dialog.get_values()
            return {
                'fixed_cost': values.get('service_name', ''),
                'cost': values.get('cost', '')
            }
        return None

    def _edit_selected_cost(self):
        """Edit the currently selected fixed cost."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            self._edit_cost_by_row(selected_row)

    def _edit_cost_by_row(self, row):
        """Edit a fixed cost by table row index."""
        if row == -1:
            show_warning_message_box(self, "خطا", "لطفا هزینه ثابتی که می‌خواهید ویرایش کنید را انتخاب کنید")
            return

        cost_id = self._get_cost_id_by_row(row)
        if cost_id is None:
            show_error_message_box(self, "خطا", "شناسه هزینه ثابت پیدا نشد")
            return

        # Get current data
        name_item = self.table.item(row, 1)  # Name is in column 1
        price_item = self.table.item(row, 2)  # Price is in column 2

        if not name_item or not price_item:
            show_warning_message_box(self, "خطا", "اطلاعات ردیف انتخاب شده نامعتبر است")
            return

        current_data = {
            'fixed_cost': name_item.text(),
            'cost': price_item.text()
        }

        # Show edit dialog
        new_data = self._show_edit_dialog(current_data)
        if new_data:
            if self.service.edit_fixed_cost(self, cost_id, new_data):
                self.load_fixed_costs()  # Reload to update the table

    def _delete_selected_cost(self):
        """Delete the currently selected fixed cost."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            self._delete_cost_by_row(selected_row)

    def _delete_cost_by_row(self, row):
        """Delete a fixed cost by table row index."""
        if row == -1:
            show_warning_message_box(self, "خطا", "لطفا هزینه ثابتی که می‌خواهید حذف کنید را انتخاب کنید")
            return

        # Check if this is a default cost
        if self._is_default_cost(row):
            show_warning_message_box(self, "خطا", "امکان حذف هزینه‌های پیش‌فرض وجود ندارد")
            return

        cost_id = self._get_cost_id_by_row(row)
        if cost_id is None:
            show_error_message_box(self, "خطا", "شناسه هزینه ثابت پیدا نشد")
            return

        # Get cost name for confirmation dialog
        name_item = self.table.item(row, 1)
        cost_name = name_item.text() if name_item else "نامشخص"

        # Show confirmation dialog
        if show_question_message_box(
                self,
                "تأیید حذف",
                f"آیا مطمئن هستید که می‌خواهید هزینه ثابت '{cost_name}' را حذف کنید؟"
        ):
            if self.service.delete_fixed_cost(self, cost_id):
                self.load_fixed_costs()  # Reload to update the table

    def _bulk_delete_selected(self):
        """Delete all selected fixed costs."""
        selected_rows = self._get_selected_rows()
        if not selected_rows:
            show_warning_message_box(self, "خطا", "هیچ موردی انتخاب نشده است")
            return

        # Filter out default costs and get IDs
        deletable_ids = []
        default_count = 0

        for row in selected_rows:
            if self._is_default_cost(row):
                default_count += 1
                continue

            cost_id = self._get_cost_id_by_row(row)
            if cost_id:
                deletable_ids.append(cost_id)

        # Show warning if some items can't be deleted
        if default_count > 0:
            show_warning_message_box(
                self,
                "هشدار",
                f"{default_count} مورد از موارد انتخابی هزینه‌های پیش‌فرض هستند و حذف نخواهند شد"
            )

        if not deletable_ids:
            show_warning_message_box(self, "خطا", "هیچ موردی برای حذف وجود ندارد")
            return

        # Show confirmation dialog
        if show_question_message_box(
                self,
                "تأیید حذف",
                f"آیا مطمئن هستید که می‌خواهید {len(deletable_ids)} مورد انتخاب شده را حذف کنید؟"
        ):
            success_count = 0
            for cost_id in deletable_ids:
                if self.service.delete_fixed_cost(self, cost_id):
                    success_count += 1

            # Show result message
            if success_count == len(deletable_ids):
                show_warning_message_box(
                    self,
                    "موفق",
                    f"{success_count} مورد با موفقیت حذف شد"
                )
            else:
                show_error_message_box(
                    self,
                    "خطا",
                    f"تنها {success_count} از {len(deletable_ids)} مورد حذف شد"
                )

            self.load_fixed_costs()  # Reload to update the table

    def get_selected_costs(self):
        """Get list of selected fixed costs data."""
        selected_costs = []
        selected_rows = self._get_selected_rows()

        for row in selected_rows:
            cost_id = self._get_cost_id_by_row(row)
            name_item = self.table.item(row, 1)
            price_item = self.table.item(row, 2)

            if cost_id and name_item and price_item:
                selected_costs.append({
                    'id': cost_id,
                    'name': name_item.text(),
                    'price': float(price_item.text()) if price_item.text().replace('.', '').isdigit() else 0.0
                })

        return selected_costs

    def clear_selection(self):
        """Clear all selections in the table."""
        self.select_all_checkbox.setChecked(False)
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        self._update_selection_ui()

    def refresh_data(self):
        """Refresh the table data from database."""
        self.load_fixed_costs()

    def set_search_filter(self, search_text):
        """Set the search filter programmatically."""
        self.search_bar.setText(search_text)
        self._filter_costs(search_text)
