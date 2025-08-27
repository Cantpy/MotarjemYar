from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QCheckBox, QLabel,
                               QPushButton, QHeaderView, QTableWidgetItem, QComboBox, QMenu, QDialog)
from PySide6.QtCore import Qt, Signal, QPoint, QUrl
from PySide6.QtGui import QDesktopServices, QAction
from functools import partial
from typing import List, Any
from features.Invoice_Table_GAS.invoice_table_GAS_models import InvoiceData, InvoiceSummary


# This view is now "dumb". It only emits signals and updates its UI when told to.

class InvoiceTableView(QWidget):
    """Main view for the invoice table. It is completely unaware of the controller."""

    # --- Signals Emitted by the View for the Controller to Catch ---

    # User Actions
    add_invoice_requested = Signal()
    edit_invoice_requested = Signal(str)  # invoice_number
    delete_invoice_requested = Signal(str)  # invoice_number
    bulk_delete_requested = Signal()
    export_requested = Signal()
    refresh_requested = Signal()
    summary_requested = Signal()

    # Data/UI Interactions
    search_text_changed = Signal(str)
    selection_changed = Signal(list)  # list of selected invoice numbers
    select_all_toggled = Signal(bool)
    translator_updated = Signal(str, str)  # invoice_number, translator_name
    column_visibility_changed = Signal(int, bool)  # column_index, is_visible
    toggle_column_filter_requested = Signal()
    open_pdf_requested = Signal(str)  # invoice_number

    # Window events
    window_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # UI Components
        self.search_bar = None
        self.table = None
        self.select_all_checkbox = None
        self.selected_count_label = None
        self.filter_button = None
        self.bulk_delete_btn = None
        self.column_checkboxes = []
        self.column_checkboxes_layout = None
        self.checkboxes_visible = False

        self._setup_ui()
        self._connect_internal_signals()  # Connects widget signals to emit class signals

    def _setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("فاکتورها صادر شده")
        self.setLayoutDirection(Qt.RightToLeft)
        self.layout = QVBoxLayout(self)

        self._create_search_bar()
        self._create_selection_controls()
        self._create_column_checkboxes()
        self._create_table()
        self._create_action_buttons()

    def _connect_internal_signals(self):
        """Connects internal Qt widget signals to this class's public signals."""
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.select_all_checkbox.stateChanged.connect(
            lambda state: self.select_all_toggled.emit(state == Qt.Checked)
        )
        self.filter_button.clicked.connect(self.toggle_column_filter_requested)
        self.bulk_delete_btn.clicked.connect(self.bulk_delete_requested)
        self.export_btn.clicked.connect(self.export_requested)

        self.add_invoice_btn.clicked.connect(self.add_invoice_requested)
        self.edit_invoice_btn.clicked.connect(self._emit_edit_request)
        self.delete_invoice_btn.clicked.connect(self._emit_delete_request)
        self.summary_btn.clicked.connect(self.summary_requested)
        self.refresh_btn.clicked.connect(self.refresh_requested)

        self.table.customContextMenuRequested.connect(self._show_context_menu)
        for i, checkbox in enumerate(self.column_checkboxes):
            checkbox.stateChanged.connect(
                lambda state, col=i: self.column_visibility_changed.emit(col, state == Qt.Checked)
            )

    # --- Public Methods (Slots) for the Controller to Call ---

    def update_table(self, invoices: List[InvoiceData], doc_counts: dict, translator_names: List[str]):
        """Populate the table with fresh invoice data."""
        self.table.setRowCount(len(invoices))
        for row_idx, invoice in enumerate(invoices):
            self._populate_row(row_idx, invoice, doc_counts.get(invoice.invoice_number, 0), translator_names)
        self._apply_column_visibility()

    def update_selection_info(self, selected_count: int, total_visible_count: int):
        """Update UI elements related to selection counts."""
        self.selected_count_label.setText(f"{selected_count} مورد انتخاب شده")
        self.bulk_delete_btn.setEnabled(selected_count > 0)
        self.export_btn.setEnabled(selected_count > 0)

        # Update select all checkbox state without emitting signals
        self.select_all_checkbox.blockSignals(True)
        if selected_count == 0:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        elif selected_count == total_visible_count:
            self.select_all_checkbox.setCheckState(Qt.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    def set_column_visibility(self, column_index: int, is_visible: bool):
        """Hides or shows a table column."""
        self.table.setColumnHidden(column_index + 1, not is_visible)

    def restore_column_checkboxes(self, visibility_states: List[bool]):
        """Sets the checked state of column filter checkboxes on startup."""
        for i, checkbox in enumerate(self.column_checkboxes):
            checkbox.blockSignals(True)
            checkbox.setChecked(visibility_states[i])
            checkbox.blockSignals(False)

    def toggle_column_filter_widgets(self, show: bool):
        """Shows or hides the column filter checkboxes."""
        for checkbox in self.column_checkboxes:
            checkbox.setVisible(show)
        self.filter_button.setText("پنهان کردن فیلتر" if show else "فیلتر ستون‌ها")

    def open_pdf_file_path(self, file_path: str):
        """Opens the given file path using the default system application."""
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except Exception as e:
            # Although the view is dumb, this is pure UI _logic.
            # A more advanced setup might involve a "show error" signal.
            print(f"Error opening PDF from view: {e}")

    def clear_search_bar(self):
        self.search_bar.clear()

    # --- Internal Helper Methods ---

    def _populate_row(self, row_idx: int, invoice: InvoiceData, doc_count: int, translator_names: list):
        # Checkbox for selection
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._emit_selection_changed)
        self.table.setCellWidget(row_idx, 0, checkbox)

        # Invoice data columns
        data_columns = [
            str(invoice.invoice_number),
            invoice.name, invoice.national_id, invoice.phone,
            invoice.issue_date, invoice.delivery_date or ""
        ]
        for col_idx, value in enumerate(data_columns):
            self.table.setItem(row_idx, col_idx + 1, self._create_table_item(str(value)))

        self._setup_translator_column(row_idx, invoice, translator_names)
        self.table.setItem(row_idx, 8, self._create_table_item(str(doc_count)))
        self.table.setItem(row_idx, 9, self._create_table_item(f"{invoice.total_amount:,}"))

        pdf_button = QPushButton("مشاهده فاکتور")
        pdf_button.clicked.connect(partial(self.open_pdf_requested.emit, invoice.invoice_number))
        self.table.setCellWidget(row_idx, 10, pdf_button)

    def _emit_selection_changed(self):
        """Gathers selected invoice numbers and emits the selection_changed signal."""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                item = self.table.item(row, 1)
                if item:
                    selected.append(item.text())
        self.selection_changed.emit(selected)

    def _emit_edit_request(self):
        """Emits the edit_invoice_requested signal for the currently selected row."""
        row = self.table.currentRow()
        if row != -1:
            item = self.table.item(row, 1)
            if item:
                self.edit_invoice_requested.emit(item.text())

    def _emit_delete_request(self):
        """Emits the delete_invoice_requested signal for the currently selected row."""
        row = self.table.currentRow()
        if row != -1:
            item = self.table.item(row, 1)
            if item:
                self.delete_invoice_requested.emit(item.text())

    # ... (Code for _create_search_bar, _create_table, etc. is largely the same, so it's omitted for brevity)
    # ... (Just ensure they don't reference `self.controller`.)

    def closeEvent(self, event):
        """Handle window close event."""
        self.window_closed.emit()
        event.accept()

    # Other UI creation methods...
    def _create_search_bar(self):
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجو بر اساس نام، کد ملی، شماره تماس، یا غیره ...")
        search_layout.addWidget(self.search_bar)
        self.layout.addLayout(search_layout)

    def _create_table(self):
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(11)
        headers = ["انتخاب", "شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
                   "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزینه فاکتور", "مشاهده فاکتور"]
        self.table.setHorizontalHeaderLabels(headers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

    def _create_selection_controls(self):
        selection_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("انتخاب همه")
        self.selected_count_label = QLabel("0 مورد انتخاب شده")
        self.filter_button = QPushButton("فیلتر کردن ستونها")
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.export_btn = QPushButton("📊 صادرات انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        selection_layout.addWidget(self.select_all_checkbox)
        selection_layout.addWidget(self.selected_count_label)
        selection_layout.addStretch()
        selection_layout.addWidget(self.filter_button)
        selection_layout.addWidget(self.bulk_delete_btn)
        selection_layout.addWidget(self.export_btn)
        self.layout.addLayout(selection_layout)

    def _create_column_checkboxes(self):
        # This setup is now simpler as it only creates the widgets
        self.column_checkboxes_layout = QHBoxLayout()
        self.column_checkboxes = []
        column_names = ["شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
                        "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزینه فاکتور", "مشاهده فاکتور"]
        for name in column_names:
            checkbox = QCheckBox(name)
            checkbox.setVisible(False)
            self.column_checkboxes.append(checkbox)
            self.column_checkboxes_layout.addWidget(checkbox)
        self.layout.addLayout(self.column_checkboxes_layout)

    def _create_action_buttons(self):
        button_layout = QHBoxLayout()
        self.add_invoice_btn = QPushButton("افزودن فاکتور")
        self.edit_invoice_btn = QPushButton("ویرایش فاکتور")
        self.delete_invoice_btn = QPushButton("حذف فاکتور")
        self.summary_btn = QPushButton("خلاصه فاکتورها")
        self.refresh_btn = QPushButton("🔄 به‌روزرسانی")
        button_layout.addWidget(self.add_invoice_btn)
        button_layout.addWidget(self.edit_invoice_btn)
        button_layout.addWidget(self.delete_invoice_btn)
        button_layout.addWidget(self.summary_btn)
        button_layout.addWidget(self.refresh_btn)
        self.layout.addLayout(button_layout)

    def _create_table_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def _setup_translator_column(self, row_idx: int, invoice: InvoiceData, translator_names: List[str]):
        if not invoice.translator or invoice.translator == "نامشخص":
            translator_combo = QComboBox()
            translator_combo.addItems(translator_names)
            translator_combo.currentTextChanged.connect(
                lambda name: self.translator_updated.emit(invoice.invoice_number, name)
            )
            self.table.setCellWidget(row_idx, 7, translator_combo)
        else:
            self.table.setItem(row_idx, 7, self._create_table_item(invoice.translator))

    def _show_context_menu(self, position: QPoint):
        if self.table.itemAt(position) is None:
            return
        menu = QMenu(self)
        edit_action = QAction("ویرایش فاکتور", self)
        edit_action.triggered.connect(self._emit_edit_request)
        menu.addAction(edit_action)
        delete_action = QAction("حذف فاکتور", self)
        delete_action.triggered.connect(self._emit_delete_request)
        menu.addAction(delete_action)
        menu.exec_(self.table.mapToGlobal(position))


class EditInvoiceDialog(QDialog):
    # This dialog is now dumber too. It just displays data and returns the new data.
    def __init__(self, invoice_data: InvoiceData, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ویرایش اطلاعات فاکتور")

        self.invoice_data = invoice_data

        if not self.invoice_data:
            self.reject()
            return

        self._setup_ui()

    def _setup_ui(self):
        """Setup edit invoice dialog UI"""
        layout = QVBoxLayout(self)

        # Form fields
        self.fields = {}

        # Name field
        layout.addWidget(QLabel("نام:"))
        self.fields['name'] = QLineEdit(self.invoice_data.name)
        layout.addWidget(self.fields['name'])

        # National ID field
        layout.addWidget(QLabel("کد ملی:"))
        self.fields['national_id'] = QLineEdit(str(self.invoice_data.national_id))
        layout.addWidget(self.fields['national_id'])

        # Phone field
        layout.addWidget(QLabel("شماره تماس:"))
        self.fields['phone'] = QLineEdit(self.invoice_data.phone)
        layout.addWidget(self.fields['phone'])

        # Delivery date field
        layout.addWidget(QLabel("تاریخ تحویل:"))
        self.fields['delivery_date'] = QLineEdit(self.invoice_data.delivery_date or "")
        layout.addWidget(self.fields['delivery_date'])

        # Translator field
        layout.addWidget(QLabel("مترجم:"))
        self.fields['translator'] = QLineEdit(self.invoice_data.translator or "")
        layout.addWidget(self.fields['translator'])

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("ذخیره")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("لغو")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_updated_data(self) -> dict:
        """Return a dict of the new values from the line edits."""
        return {
            'name': self.fields['name'].text().strip(),
            'national_id': self.fields['national_id'].text().strip(),
            'phone': self.fields['phone'].text().strip(),
            'delivery_date': self.fields['delivery_date'].text().strip(),
            'translator': self.fields['translator'].text().strip()
        }


class SummaryDialog(QDialog):
    def __init__(self, summary: InvoiceSummary, parent=None):
        super().__init__(parent)
        self.setWindowTitle("خلاصه فاکتورها")
        self.summary = summary

        if not self.summary:
            self.reject()
            return

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)

        # Total statistics
        total_count_text = NumberFormatLogic.to_persian_number(str(self.summary.total_count))
        layout.addWidget(QLabel(f"تعداد کل فاکتورها: {total_count_text}"))

        total_amount_text = NumberFormatLogic.format_currency(self.summary.total_amount)
        layout.addWidget(QLabel(f"مجموع مبلغ: {total_amount_text} تومان"))

        layout.addWidget(QLabel("\nآمار مترجمان:"))

        # Translator statistics
        for translator, count in self.summary.translator_stats:
            count_text = NumberFormatLogic.to_persian_number(str(count))
            layout.addWidget(QLabel(f"  {translator}: {count_text} فاکتور"))

        # Close button
        close_btn = QPushButton("بستن")
        layout.addWidget(close_btn)
        close_btn.clicked.connect(self.accept)