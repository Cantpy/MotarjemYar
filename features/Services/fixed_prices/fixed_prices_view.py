# features/Services/fixed_prices/fixed_prices_view.py

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox, QLabel, QPushButton, QTableWidget, QMenu, QTableWidgetItem
)
from features.Services.fixed_prices.fixed_prices_models import FixedPriceDTO
from shared.utils.persian_tools import to_persian_numbers


class FixedPricesView(QWidget):
    """A 'dumb' view for displaying and managing fixed prices."""

    # --- Public Signals for the Controller ---
    add_requested = Signal()
    edit_requested = Signal(int)  # cost_id
    delete_requested = Signal(int)  # cost_id
    bulk_delete_requested = Signal(list)  # list of cost_ids
    search_text_changed = Signal(str)

    COLUMN_HEADERS = ["انتخاب", "هزینه‌های ثابت", "هزینه"]
    COLUMN_WIDTHS = [8, 60, 30]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_to_id_mapping = {}
        self._displayed_costs: list[FixedPriceDTO] = []
        self._setup_ui()
        self._connect_signals()

    # --- Public Slots for the Controller ---

    @Slot(list)
    def update_display(self, costs: list[FixedPriceDTO]):
        """Populates the table with data provided by the controller."""
        self._displayed_costs = costs

        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()

        for row_num, cost_dto in enumerate(costs):
            self.table.insertRow(row_num)
            self.row_to_id_mapping[row_num] = cost_dto.id
            self._populate_row(row_num, cost_dto)

        self.table.setSortingEnabled(True)
        self._update_selection_ui()

    def get_current_data_for_edit(self) -> dict | None:
        """Provides the controller with the current values of the selected row."""
        row = self.table.currentRow()
        if row == -1: return None
        return {
            'name': self.table.item(row, 1).text(),
            'price': self.table.item(row, 2).text().replace(',', ''),
        }

    # --- UI Setup and Signal Connections (Internal) ---

    def _setup_ui(self):
        """Initialize and configure UI components."""
        self.main_layout = QVBoxLayout(self)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی هزینه‌ها...")
        self.main_layout.addWidget(self.search_bar)

        selection_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("انتخاب همه")
        self.selected_count_label = QLabel("0 مورد انتخاب شده")
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        selection_layout.addWidget(self.select_all_checkbox)
        selection_layout.addWidget(self.selected_count_label)
        selection_layout.addStretch()
        selection_layout.addWidget(self.bulk_delete_btn)
        self.main_layout.addLayout(selection_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ اضافه کردن هزینه")
        self.edit_btn = QPushButton("✏️ ویرایش هزینه")
        self.delete_btn = QPushButton("🗑️ حذف هزینه")
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
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

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        self.add_btn.clicked.connect(self.add_requested)
        self.edit_btn.clicked.connect(self._emit_edit_request)
        self.delete_btn.clicked.connect(self._emit_delete_request)
        self.bulk_delete_btn.clicked.connect(self._emit_bulk_delete_request)
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.select_all_checkbox.stateChanged.connect(self._update_selection_ui)

    def _populate_row(self, row_num: int, cost_dto: FixedPriceDTO):
        # Checkbox
        checkbox_widget = self._create_checkbox_widget()
        self.table.setCellWidget(row_num, 0, checkbox_widget)

        # Data
        name_item = QTableWidgetItem(cost_dto.name)
        price_item = QTableWidgetItem(to_persian_numbers(f"{cost_dto.price:,}"))

        if cost_dto.is_default:
            font = name_item.font()
            font.setBold(True)
            name_item.setFont(font)
            price_item.setFont(font)
            name_item.setToolTip("این هزینه پیش‌فرض است و قابل حذف نیست.")
            price_item.setToolTip("این هزینه پیش‌فرض است و قابل حذف نیست.")

        self.table.setItem(row_num, 1, name_item)
        self.table.setItem(row_num, 2, price_item)

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

    def _show_context_menu(self, position):
        row = self.table.indexAt(position).row()
        if row == -1: return

        cost_id = self.row_to_id_mapping.get(row)
        if not cost_id: return

        # Now, find the DTO from the stored list to check its properties
        cost_dto = next((c for c in self._displayed_costs if c.id == cost_id), None)
        if not cost_dto: return

        context_menu = QMenu(self)

        edit_action = QAction("✏️ ویرایش", self)
        edit_action.triggered.connect(self._emit_edit_request)
        context_menu.addAction(edit_action)

        # This is a PRESENTATION rule, so it's OK for the view to know it.
        if not cost_dto.is_default:
            delete_action = QAction("🗑️ حذف", self)
            delete_action.triggered.connect(self._emit_delete_request)
            context_menu.addAction(delete_action)

        context_menu.exec(self.table.viewport().mapToGlobal(position))

    def _on_checkbox_changed(self):
        """Handle individual checkbox state change."""
        self._update_selection_ui()

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

    def _get_selected_rows(self):
        return [r for r in range(self.table.rowCount()) if self._is_row_selected(r)]

    def _is_row_selected(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget:
            checkbox = widget.findChild(QCheckBox)
            return checkbox and checkbox.isChecked()
        return False

    # --- Emit Signals
    def _emit_edit_request(self):
        row = self.table.currentRow()
        if row != -1 and (cost_id := self.row_to_id_mapping.get(row)):
            self.edit_requested.emit(cost_id)

    def _emit_delete_request(self):
        row = self.table.currentRow()
        if row != -1 and (service_id := self.row_to_id_mapping.get(row)):
            self.delete_requested.emit(service_id)

    def _emit_bulk_delete_request(self):
        selected_rows = self._get_selected_rows()
        service_ids = [self.row_to_id_mapping.get(r) for r in selected_rows if self.row_to_id_mapping.get(r)]
        if service_ids:
            self.bulk_delete_requested.emit(service_ids)
