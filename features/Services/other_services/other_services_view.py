# features/Services/other_services/other_services_view.py

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QLabel, QPushButton, QTableWidget, QMenu, QTableWidgetItem
)
from features.Services.other_services.other_services_models import OtherServiceDTO


class OtherServicesView(QWidget):
    """A 'dumb' view for displaying and managing other services."""

    add_requested = Signal()
    edit_requested = Signal(int)  # service_id
    delete_requested = Signal(int)  # service_id
    bulk_delete_requested = Signal(list)  # list of service_ids
    search_text_changed = Signal(str)

    COLUMN_HEADERS = ["انتخاب", "خدمات", "هزینه"]
    COLUMN_WIDTHS = [15, 55, 30]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_to_id_mapping = {}
        self._setup_ui()
        self._connect_signals()

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
        self.search_bar.textChanged.connect(self._filter_costs)
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
        self.bulk_delete_btn.clicked.connect(self._emit_bulk_delete_request)
        selection_layout.addWidget(self.bulk_delete_btn)

        self.main_layout.addLayout(selection_layout)

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
        self.add_btn = QPushButton("➕ اضافه کردن خدمت")
        self.edit_btn = QPushButton("✏️ ویرایش خدمت")
        self.delete_btn = QPushButton("🗑️ حذف خدمت")

        buttons = [self.add_btn, self.edit_btn, self.delete_btn]
        for button in buttons:
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)

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

    @Slot(list)
    def update_display(self, services: list[OtherServiceDTO]):
        """Populates the table with data provided by the controller."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()
        for row_num, service_dto in enumerate(services):
            self.table.insertRow(row_num)
            self.row_to_id_mapping[row_num] = service_dto.id
            self._populate_row(row_num, service_dto)
        self.table.setSortingEnabled(True)
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

    def get_current_data_for_edit(self) -> dict | None:
        """Provides the controller with the current values of the selected row."""
        row = self.table.currentRow()
        if row == -1: return None
        return {
            'name': self.table.item(row, 1).text(),
            'price': self.table.item(row, 2).text().replace(',', ''),
        }

    def _filter_costs(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.strip().lower()
        for row in range(self.table.rowCount()):
            cost_name_item = self.table.item(row, 1)  # Name is now in column 1
            if cost_name_item:
                cost_name = cost_name_item.text().lower()
                self.table.setRowHidden(row, search_text not in cost_name)

        # Update selection UI when filtering
        self._update_selection_ui()

    def _connect_signals(self):
        self.add_btn.clicked.connect(self.add_requested)
        self.edit_btn.clicked.connect(self._emit_edit_request)
        self.delete_btn.clicked.connect(self._emit_delete_request)
        self.bulk_delete_btn.clicked.connect(self._emit_bulk_delete_request)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _populate_row(self, row_num: int, service_dto: OtherServiceDTO):
        checkbox_widget = self._create_checkbox_widget()  # Assuming this method exists
        self.table.setCellWidget(row_num, 0, checkbox_widget)
        name_item = QTableWidgetItem(service_dto.name)
        price_item = QTableWidgetItem(f"{service_dto.price:,}")
        self.table.setItem(row_num, 1, name_item)
        self.table.setItem(row_num, 2, price_item)

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

    def _on_checkbox_changed(self):
        """Handle individual checkbox state change."""
        self._update_selection_ui()

    def _emit_edit_request(self):
        """Emit edit request for the currently selected row."""
        row = self.table.currentRow()
        if row != -1 and (service_id := self.row_to_id_mapping.get(row)):
            self.edit_requested.emit(service_id)

    def _emit_delete_request(self):
        """Emit delete request for the currently selected row."""
        row = self.table.currentRow()
        if row != -1 and (service_id := self.row_to_id_mapping.get(row)):
            self.delete_requested.emit(service_id)

    def _emit_bulk_delete_request(self):
        """Emit bulk delete request for all selected rows."""
        selected_rows = self._get_selected_rows()
        service_ids = [self.row_to_id_mapping[row] for row in selected_rows if row in self.row_to_id_mapping]
        if service_ids:
            self.bulk_delete_requested.emit(service_ids)

    def _show_context_menu(self, position):
        """Display context menu for table row operations."""
        selected_row = self.table.indexAt(position).row()
        if selected_row == -1:
            return

        context_menu = QMenu(self)

        edit_action = QAction("ویرایش", self)
        edit_action.triggered.connect(self._emit_edit_request)
        context_menu.addAction(edit_action)

        remove_action = QAction("حذف", self)
        remove_action.triggered.connect(self._emit_delete_request)
        context_menu.addAction(remove_action)

        # Add bulk operations to context menu if multiple rows are selected
        selected_count = self._get_selected_count()
        if selected_count > 1:
            context_menu.addSeparator()
            bulk_delete_action = QAction(f"حذف {selected_count} مورد انتخابی", self)
            bulk_delete_action.triggered.connect(self._emit_bulk_delete_request)
            context_menu.addAction(bulk_delete_action)

        context_menu.exec(self.table.viewport().mapToGlobal(position))
