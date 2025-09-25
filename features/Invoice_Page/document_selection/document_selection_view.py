# document_selection/_view.py

from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QVBoxLayout, QHBoxLayout, QGroupBox, QHeaderView, QCompleter, QGridLayout, QGraphicsDropShadowEffect, QMenu
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QAction, QFont
from features.Invoice_Page.document_selection.document_selection_models import InvoiceItem
from features.Invoice_Page.document_selection.document_selection_qss_styles import (DOC_SELECTION_STYLES,
                                                                                    COMPLETER_POPUP)
from shared.utils.persian_tools import to_persian_numbers


class DocumentSelectionWidget(QWidget):
    # --- The communication signal ---
    add_button_clicked = Signal(str)
    edit_button_clicked = Signal(int)
    delete_button_clicked = Signal(int)
    clear_button_clicked = Signal()
    manual_item_updated = Signal(object, int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("DocumentSelectionWidget")
        # self.setStyleSheet(DOC_SELECTION_STYLES)
        self._is_updating_table = False

        main_layout = QVBoxLayout(self)
        self._setup_ui(main_layout)
        self._setup_connections()

    def _setup_ui(self, main_layout):
        self._setup_service_input(main_layout)
        self._setup_invoice_table(main_layout)
        self._setup_action_buttons(main_layout)

    def _apply_shadow_effect(self, widget: QGroupBox):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 25))
        widget.setGraphicsEffect(shadow)

    def _setup_service_input(self, parent_layout):
        service_input_group = QGroupBox("افزودن خدمات به فاکتور")
        # Use a grid layout for better alignment and control
        layout = QGridLayout(service_input_group)
        layout.setSpacing(15)

        self.service_edit = QLineEdit()
        self.service_edit.setPlaceholderText("نام سند یا خدمات را جستجو کنید...")
        self.add_button = QPushButton("➕ افزودن خدمت")
        self.add_button.setObjectName("PrimaryButton")
        self.add_button.setEnabled(False)
        self.add_button.setToolTip("ابتدا یک خدمت معتبر از لیست انتخاب کنید")

        layout.addWidget(QLabel("انتخاب سند:"), 0, 0)
        layout.addWidget(self.service_edit, 0, 1)
        layout.addWidget(self.add_button, 0, 2)
        layout.setColumnStretch(1, 1)

        self._apply_shadow_effect(service_input_group)
        parent_layout.addWidget(service_input_group)

    def _setup_invoice_table(self, parent_layout):
        invoice_table_group = QGroupBox("لیست خدمات")
        layout = QVBoxLayout(invoice_table_group)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(40)
        self.table.verticalHeader().setFont(QFont("IRANSans", 10))

        self.table.setStyleSheet("""QHeaderView::section:vertical {border-right: 1px solid #edf2f7;}""")

        self.table.setAlternatingRowColors(True)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "شرح خدمات", "تعداد کل", "تعداد صفحات", "مهر دادگستری", "مهر امورخارجه",
            "قیمت کل", "توضیحات"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)
        self._apply_shadow_effect(invoice_table_group)
        parent_layout.addWidget(invoice_table_group)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _setup_action_buttons(self, parent_layout):
        buttons_layout = QHBoxLayout()
        self.clear_button = QPushButton("پاک کردن کل لیست")
        self.delete_button = QPushButton("حذف ردیف انتخاب شده")
        self.delete_button.setObjectName("RemoveButton")
        self.delete_button.setEnabled(False)  # Initially disabled

        # --- NEW: Edit Button ---
        self.edit_button = QPushButton("ویرایش ردیف انتخاب شده")
        self.edit_button.setEnabled(False)  # Initially disabled

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.clear_button)
        parent_layout.addLayout(buttons_layout)

    def _setup_connections(self):
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.customContextMenuRequested.connect(self._show_table_context_menu)

        self.delete_button.clicked.connect(self._delete_selected_row)
        self.delete_button.clicked.connect(lambda: self.delete_button_clicked.emit(self.table.currentRow()))

        self.edit_button.clicked.connect(lambda: self.edit_button_clicked.emit(self.table.currentRow()))
        self.add_button.clicked.connect(lambda: self.add_button_clicked.emit(self.service_edit.text()))

        self.clear_button.clicked.connect(self.clear_button_clicked.emit)
        self.service_edit.returnPressed.connect(self.add_button.click)

    def populate_completer(self, service_names: list):
        completer = QCompleter(service_names, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)

        completer.popup().setStyleSheet(COMPLETER_POPUP)

        self.service_edit.setCompleter(completer)

        completer.activated.connect(lambda text: self.add_button.setEnabled(True))
        self.service_edit.textChanged.connect(lambda text: self.add_button.setEnabled(text in service_names))

    def update_table_display(self, items: list[InvoiceItem]):
        self._is_updating_table = True
        self.table.setRowCount(0)

        for item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # --- CRITICAL FIX: Differentiate between editable and non-editable rows ---
            if item.service.type == "خدمات دیگر":
                # This is a manual entry, cells should be editable
                self.table.setItem(row, 0, self._create_cell(item.service.name, data=item, editable=False))
                self.table.setItem(row, 1, self._create_cell("۱", centered=True))
                self.table.setItem(row, 2, self._create_cell("-", centered=True))
                self.table.setItem(row, 3, self._create_cell("-", centered=True))
                self.table.setItem(row, 4, self._create_cell("-", centered=True))
                # Price and Remarks are editable by default
                self.table.setItem(row, 5, self._create_cell(to_persian_numbers(f"{item.total_price:,} تومان"),
                                                             centered=True, data=item, editable=True))
                self.table.setItem(row, 6, self._create_cell(item.remarks, data=item, editable=True))
            else:
                # This is a calculated item, all cells are read-only
                self.table.setItem(row, 0, self._create_cell(item.service.name, data=item))
                self.table.setItem(row, 1, self._create_cell(to_persian_numbers(item.quantity), centered=True))
                self.table.setItem(row, 2, self._create_cell(to_persian_numbers(item.page_count), centered=True))
                self.table.setItem(row, 3, self._create_cell("✔" if item.has_judiciary_seal else "-",
                                                             centered=True))
                self.table.setItem(row, 4, self._create_cell("✔" if item.has_foreign_affairs_seal else "-",
                                                             centered=True))
                self.table.setItem(row, 5, self._create_cell(to_persian_numbers(f"{item.total_price:,} تومان"),
                                                             centered=True))
                self.table.setItem(row, 6, self._create_cell(item.remarks, tooltip=item.remarks))

        vertical_headers = [to_persian_numbers(i + 1) for i in range(self.table.rowCount())]
        self.table.setVerticalHeaderLabels(vertical_headers)

        self.table.resizeRowsToContents()
        self._is_updating_table = False

    def _on_table_item_changed(self, item: QTableWidgetItem):
        """
        Handles user edits for manual items, now with a check to prevent recursion.
        """
        # If the table is being programmatically redrawn, do nothing.
        if self._is_updating_table:
            return

        row = item.row()
        col = item.column()

        # Get the backend data object for this row
        data_item = self.table.item(row, 0)
        if not data_item: return
        invoice_item = data_item.data(Qt.ItemDataRole.UserRole)

        # This handler should only work for manual "Other Service" items
        if not isinstance(invoice_item, InvoiceItem) or invoice_item.service.type != "خدمات دیگر":
            return

        # Handle Price changes
        if col == 5:
            try:
                price_text = item.text().replace(" تومان", "").replace(",", "").strip()
                new_price = int(price_text)

                # Only send an update if the price has actually changed.
                if new_price != invoice_item.total_price:
                    self.manual_item_updated.emit(invoice_item, new_price, invoice_item.remarks)
                # If the user types invalid text, the _logic layer won't be called,
                # and the next full redraw will fix the cell's text automatically.

            except (ValueError, TypeError):
                # If user types garbage, revert the cell text immediately without a signal loop.
                self._is_updating_table = True
                item.setText(f"{invoice_item.total_price:,} تومان")
                self._is_updating_table = False

        # Handle Remarks changes
        elif col == 6:
            new_remarks = item.text()

            # Only send an update if the remarks have actually changed.
            if new_remarks != invoice_item.remarks:
                self.manual_item_updated.emit(invoice_item, invoice_item.total_price, new_remarks)

    def _create_cell(self, text, editable=False, centered=False, right_aligned=False, data=None,
                     tooltip=None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if centered:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if right_aligned:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if data:
            item.setData(Qt.ItemDataRole.UserRole, data)
        if tooltip:
            item.setToolTip(tooltip)
        return item

    def _on_selection_changed(self):
        """Enables/disables edit and delete buttons based on row selection."""
        is_row_selected = len(self.table.selectedIndexes()) > 0
        self.delete_button.setEnabled(is_row_selected)
        self.edit_button.setEnabled(is_row_selected)

    def _show_table_context_menu(self, position):
        """Creates and shows the right-click context menu."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()

        menu = QMenu()
        edit_action = QAction("ویرایش آیتم", self)
        delete_action = QAction("حذف آیتم", self)

        edit_action.triggered.connect(lambda: self.edit_button_clicked.emit(row))
        delete_action.triggered.connect(lambda: self.delete_button_clicked.emit(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _delete_selected_row(self):
        """Deletes the currently selected row. More robust now."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.delete_button_clicked.emit(current_row)

    def clear_service_input(self):
        """A public slot to clear the line edit and reset button state."""
        self.service_edit.clear()
        self.add_button.setEnabled(False)
