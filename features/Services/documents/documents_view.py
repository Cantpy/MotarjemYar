# features/Services/documents/documents_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QMenu
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from features.Services.documents.documents_models import ServicesDTO, ServiceDynamicFeeDTO

from shared.utils.ui_utils import TableColumnResizer
from shared.utils.persian_tools import to_persian_numbers


class ServicesDocumentsView(QWidget):
    """
    A 'dumb' _view for displaying and managing services/documents.
    It emits signals for user actions and has public slots for updates.
    It has no knowledge of controllers or business _logic.
    """

    # --- Public Signals for the Controller ---
    add_requested = Signal()
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    bulk_delete_requested = Signal(list)
    search_text_changed = Signal(str)
    aliases_requested = Signal(int)

    COLUMN_HEADERS = ["انتخاب", "نام مدرک", "هزینه ترجمه", "نام متغیر ۱", "هزینه متغیر ۱",
                      "نام متغیر ۲", "هزینه متغیر ۲"]
    COLUMN_WIDTHS = [8, 37, 10, 12, 9, 10, 10]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_to_id_mapping = {}

        self._setup_ui()
        self._connect_signals()

    # --- UI Setup (Largely Unchanged) ---
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self._setup_search_bar()
        self._setup_selection_controls()
        self._setup_table()
        self._setup_buttons()

    def _setup_search_bar(self):
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی خدمات...")
        self.main_layout.addWidget(self.search_bar)

    def _setup_selection_controls(self):
        selection_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("انتخاب همه")
        self.selected_count_label = QLabel("0 مورد انتخاب شده")
        selection_layout.addWidget(self.select_all_checkbox)
        selection_layout.addWidget(self.selected_count_label)
        selection_layout.addStretch()
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        selection_layout.addWidget(self.bulk_delete_btn)
        self.main_layout.addLayout(selection_layout)

    def _setup_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.stretchLastSection = False
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.main_layout.addWidget(self.table)

        # Apply column resizer (5%, 45%, then 5×10%)
        TableColumnResizer(self.table, [6, 30, 11, 11, 9, 11, 9])

    def _setup_buttons(self):
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ اضافه کردن مدرک")
        self.edit_btn = QPushButton("✏️ ویرایش مدرک")
        self.delete_btn = QPushButton("🗑️ حذف مدرک")
        self.aliases_btn = QPushButton("🏷️ جزئیات و نام‌های مستعار")
        buttons = [self.add_btn, self.edit_btn, self.delete_btn, self.aliases_btn]
        for button in buttons:
            button_layout.addWidget(button)
        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect internal widget signals to this _view's public signals."""
        # --- User Actions ---
        self.add_btn.clicked.connect(self.add_requested)
        self.edit_btn.clicked.connect(self._emit_edit_request)
        self.delete_btn.clicked.connect(self._emit_delete_request)
        self.bulk_delete_btn.clicked.connect(self._emit_bulk_delete_request)
        self.search_bar.textChanged.connect(self._emit_search_text_changed)
        self.aliases_btn.clicked.connect(self._emit_aliases_request)
        self.table.doubleClicked.connect(self._emit_aliases_request)
        # --- Internal UI Logic ---
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.select_all_checkbox.stateChanged.connect(self._toggle_select_all)

    # --- Public Slots for the Controller ---

    @Slot(list)
    def update_display(self, services: list[ServicesDTO]):
        """Populates the table with service data provided by the controller."""
        print(f'Updating display with services: {services}')
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()

        for row_number, service in enumerate(services):
            self.table.insertRow(row_number)
            self.row_to_id_mapping[row_number] = service.id
            self._populate_row(row_number, service)

        self.table.setSortingEnabled(True)
        self._update_selection_ui()

    @Slot(str)
    def set_search_text(self, text: str):
        """Allows the controller to set the search bar text without triggering signals."""
        self.search_bar.blockSignals(True)
        self.search_bar.setText(text)
        self.search_bar.blockSignals(False)

    def get_current_service_data_for_edit(self) -> dict | None:
        """
        Provides the controller with the current values of the selected row.
        """
        row = self.table.currentRow()
        if row == -1:
            return None

        return {
            "name": self.table.item(row, 1).text(),
            "base_price": self.table.item(row, 2).text().replace(',', ''),

            # These are used to populate the dialog fields:
            "fee_1_name": self.table.item(row, 3).text(),
            "fee_1_price": self.table.item(row, 4).text().replace(',', ''),
            "fee_2_name": self.table.item(row, 5).text(),
            "fee_2_price": self.table.item(row, 6).text().replace(',', ''),
        }

    # --- Internal Helper Methods (Purely for UI Management) ---

    def _populate_row(self, row_number: int, service: ServicesDTO):
        """Fills a single table row with data."""
        print(f'Populating row {row_number} with service: {service}')
        # Checkbox
        checkbox_widget, _ = self._create_checkbox_widget()
        self.table.setCellWidget(row_number, 0, checkbox_widget)

        data_fields = [
            service.name,
            to_persian_numbers(f"{service.base_price:,}") if service.base_price is not None else ''
        ]

        for fee in service.dynamic_prices:
            data_fields.append(fee.name)
            data_fields.append(to_persian_numbers(f"{fee.unit_price:,}"))

        max_dynamic_slots = 2
        while len(service.dynamic_prices) < max_dynamic_slots:
            data_fields.append('')
            data_fields.append('')
            service.dynamic_prices.append(ServiceDynamicFeeDTO(id=-1, service_id=service.id, name='', unit_price=0))

        for col_idx, data in enumerate(data_fields, start=1):
            item = self._create_table_item(data)
            self.table.setItem(row_number, col_idx, item)

    def _create_checkbox_widget(self):
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._update_selection_ui)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return widget, checkbox

    def _create_table_item(self, value):
        if value is None:
            display_text = ""
        elif isinstance(value, int):
            display_text = f"{value:,}" if value != 0 else ""
        else:
            display_text = str(value)
        item = QTableWidgetItem(display_text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _show_context_menu(self, position):
        # The services menu now ONLY emits signals.
        row = self.table.indexAt(position).row()
        if row == -1: return

        context_menu = QMenu(self)
        context_menu.addSeparator()

        edit_action = QAction("ویرایش", self)
        edit_action.triggered.connect(self._emit_edit_request)
        context_menu.addAction(edit_action)

        delete_action = QAction("حذف", self)
        delete_action.triggered.connect(self._emit_delete_request)
        context_menu.addAction(delete_action)

        aliases_action = QAction("جزئیات و نام‌های مستعار", self)
        aliases_action.triggered.connect(self._emit_aliases_request)
        context_menu.addAction(aliases_action)

        context_menu.exec(self.table.viewport().mapToGlobal(position))

    # --- UI State Update Methods (OK to keep in View) ---

    def _update_selection_ui(self):
        selected_rows = self._get_selected_rows()
        selected_count = len(selected_rows)
        total_visible = sum(1 for r in range(self.table.rowCount()) if not self.table.isRowHidden(r))
        self.selected_count_label.setText(f"{selected_count} مورد انتخاب شده")
        self.bulk_delete_btn.setEnabled(selected_count > 0)
        self.select_all_checkbox.blockSignals(True)
        if selected_count == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        elif selected_count == total_visible:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    def _get_selected_rows(self):
        return [r for r in range(self.table.rowCount()) if self._is_row_selected(r)]

    def _is_row_selected(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget:
            checkbox = widget.findChild(QCheckBox)
            return checkbox and checkbox.isChecked()
        return False

    def _toggle_select_all(self, state):
        """
        Handles the state change of the 'select all' checkbox.
        This method is now optimized to prevent a "signal storm".
        """
        # Determine the target state. If the master checkbox was clicked and became
        # 'Checked', all children should be checked. Otherwise, they are unchecked.
        is_checked = (state == Qt.CheckState.Checked.value)

        # Iterate through all rows and set the state of each checkbox.
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    # Temporarily block signals for the row checkbox
                    checkbox.blockSignals(True)
                    checkbox.setChecked(is_checked)
                    checkbox.blockSignals(False)

        # After all programmatic changes are done, call the UI update method once.
        # This will correctly update the "X items selected" label.
        self._update_selection_ui()

    # --- Private Signal Emitters ---

    def _emit_edit_request(self):
        row = self.table.currentRow()
        if row != -1 and (service_id := self.row_to_id_mapping.get(row)):
            self.edit_requested.emit(service_id)

    def _emit_delete_request(self):
        row = self.table.currentRow()
        if row != -1 and (service_id := self.row_to_id_mapping.get(row)):
            self.delete_requested.emit(service_id)

    def _emit_bulk_delete_request(self):
        selected_rows = self._get_selected_rows()
        service_ids = [self.row_to_id_mapping.get(r) for r in selected_rows if self.row_to_id_mapping.get(r)]
        if service_ids:
            self.bulk_delete_requested.emit(service_ids)

    def _emit_search_text_changed(self):
        """
        Emits the search_text_changed signal when the search bar text changes.
        """
        text = self.search_bar.text().strip()
        self.search_text_changed.emit(text)

    def _emit_aliases_request(self):
        """Emits a signal to open the alias management dialog."""
        row = self.table.currentRow()
        if row != -1 and (service_id := self.row_to_id_mapping.get(row)):
            self.aliases_requested.emit(service_id)
