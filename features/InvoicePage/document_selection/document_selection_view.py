from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QCompleter, QLabel, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont
from typing import List, Optional
from features.InvoicePage.document_selection.document_selection_models import DocumentItem


class DocumentSelectionView(QWidget):
    """Main widget for document selection and invoice management"""

    # Signals
    document_selected = Signal(str)  # document name
    add_document_requested = Signal(str)  # document name
    remove_document_requested = Signal(int)  # row index
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("انتخاب اسناد")
        self.resize(800, 600)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Document selection section
        selection_frame = self._create_selection_frame()
        main_layout.addWidget(selection_frame)

        # Invoice table section
        table_frame = self._create_table_frame()
        main_layout.addWidget(table_frame)

        # Action buttons section
        buttons_frame = self._create_buttons_frame()
        main_layout.addWidget(buttons_frame)

    def _create_selection_frame(self) -> QWidget:
        """Create document selection frame"""
        frame = QWidget()
        layout = QHBoxLayout(frame)

        # Document name label
        label = QLabel("نام سند:")
        label.setFont(self._get_font(12))
        layout.addWidget(label)

        # Document name input with autocomplete
        self.document_input = QLineEdit()
        self.document_input.setFont(self._get_font(11))
        self.document_input.setPlaceholderText("نام سند را وارد کنید...")
        layout.addWidget(self.document_input)

        # Add button
        self.add_button = QPushButton("افزودن")
        self.add_button.setFont(self._get_font(11))
        self.add_button.setMinimumSize(100, 35)
        layout.addWidget(self.add_button)

        return frame

    def _create_table_frame(self) -> QWidget:
        """Create invoice table frame"""
        frame = QWidget()
        layout = QVBoxLayout(frame)

        # Table label
        label = QLabel("اسناد انتخاب شده:")
        label.setFont(self._get_font(12, bold=True))
        layout.addWidget(label)

        # Invoice table
        self.invoice_table = QTableWidget()
        self.invoice_table.setFont(self._get_font(10))
        self._setup_table()
        layout.addWidget(self.invoice_table)

        return frame

    def _create_buttons_frame(self) -> QWidget:
        """Create action buttons frame"""
        frame = QWidget()
        layout = QHBoxLayout(frame)

        # Add stretch to push buttons to the right
        layout.addStretch()

        # Remove selected button
        self.remove_button = QPushButton("حذف انتخاب شده")
        self.remove_button.setFont(self._get_font(11))
        self.remove_button.setEnabled(False)
        layout.addWidget(self.remove_button)

        # Clear all button
        self.clear_button = QPushButton("پاک کردن همه")
        self.clear_button.setFont(self._get_font(11))
        self.clear_button.setEnabled(False)
        layout.addWidget(self.clear_button)

        return frame

    def _setup_table(self):
        """Setup the invoice table"""
        # Set column count and headers
        headers = ["نام سند", "نوع", "تعداد", "داد", "اخ", "قیمت کل", "توضیحات"]
        self.invoice_table.setColumnCount(len(headers))
        self.invoice_table.setHorizontalHeaderLabels(headers)

        # Configure table properties
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.horizontalHeader().setStretchLastSection(True)

        # Set column widths
        header = self.invoice_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # نام سند
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # نوع
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # تعداد
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # داد
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # اخ
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # قیمت کل
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # توضیحات

    def _get_font(self, size: int = 11, bold: bool = False) -> QFont:
        """Get font with specified parameters"""
        font = QFont()
        font.setFamilies(["IRANSans"])
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def setup_connections(self):
        """Setup signal connections"""
        # Document input connections
        self.document_input.returnPressed.connect(self._on_add_requested)
        self.add_button.clicked.connect(self._on_add_requested)

        # Table connections
        self.invoice_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.invoice_table.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Button connections
        self.remove_button.clicked.connect(self._on_remove_requested)
        self.clear_button.clicked.connect(self._on_clear_requested)

    def setup_autocomplete(self, suggestions: List[str]):
        """Setup autocomplete for document input"""
        if not suggestions:
            return

        # Create completer
        completer = QCompleter(suggestions)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)

        # Set completer to input
        self.document_input.setCompleter(completer)

    def get_document_input_text(self) -> str:
        """Get current document input text"""
        return self.document_input.text().strip()

    def clear_document_input(self):
        """Clear document input field"""
        self.document_input.clear()
        self.document_input.setFocus()

    def add_document_to_table(self, document: DocumentItem, row_index: Optional[int] = None):
        """Add document item to the invoice table"""
        if row_index is None:
            row_index = self.invoice_table.rowCount()
            self.invoice_table.insertRow(row_index)

        # Create table items
        items = [
            self._create_table_item(document.name),
            self._create_table_item(document.document_type.value),
            self._create_table_item(str(document.count)),
            self._create_table_item(document.judiciary_display),
            self._create_table_item(document.foreign_affairs_display),
            self._create_table_item(f"{document.total_price:,}"),
            self._create_table_item(document.remarks)
        ]

        # Set items in table
        for col, item in enumerate(items):
            self.invoice_table.setItem(row_index, col, item)

        # Update button states
        self._update_button_states()

    def _create_table_item(self, text: str) -> QTableWidgetItem:
        """Create table widget item with center alignment"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
        return item

    def remove_document_from_table(self, row_index: int) -> bool:
        """Remove document from table by row index"""
        if 0 <= row_index < self.invoice_table.rowCount():
            self.invoice_table.removeRow(row_index)
            self._update_button_states()
            return True
        return False

    def clear_table(self):
        """Clear all items from the table"""
        self.invoice_table.setRowCount(0)
        self._update_button_states()

    def get_selected_row(self) -> int:
        """Get currently selected row index (-1 if none selected)"""
        current_row = self.invoice_table.currentRow()
        return current_row if current_row >= 0 else -1

    def get_table_row_count(self) -> int:
        """Get number of rows in table"""
        return self.invoice_table.rowCount()

    def get_total_amount(self) -> int:
        """Calculate total amount from all items in table"""
        total = 0
        for row in range(self.invoice_table.rowCount()):
            price_item = self.invoice_table.item(row, 5)  # قیمت کل column
            if price_item:
                try:
                    # Remove comma formatting and convert to int
                    price_text = price_item.text().replace(',', '')
                    total += int(price_text)
                except ValueError:
                    continue
        return total

    def show_total_amount(self):
        """Show total amount in a message box"""
        total = self.get_total_amount()
        from shared import to_persian_number

        message = f"مجموع کل: {to_persian_number(total)} تومان"
        QMessageBox.information(self, "مجموع فاکتور", message)

    def _update_button_states(self):
        """Update button enabled states based on table content"""
        has_items = self.invoice_table.rowCount() > 0
        has_selection = self.get_selected_row() >= 0

        self.remove_button.setEnabled(has_selection)
        self.clear_button.setEnabled(has_items)

    def _on_add_requested(self):
        """Handle add document request"""
        document_name = self.get_document_input_text()
        if document_name:
            self.add_document_requested.emit(document_name)

    def _on_remove_requested(self):
        """Handle remove document request"""
        selected_row = self.get_selected_row()
        if selected_row >= 0:
            self.remove_document_requested.emit(selected_row)

    def _on_clear_requested(self):
        """Handle clear all request"""
        reply = QMessageBox.question(
            self,
            "تایید پاک کردن",
            "آیا از پاک کردن همه اسناد مطمئن هستید؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.clear_requested.emit()

    def _on_selection_changed(self):
        """Handle table selection change"""
        self._update_button_states()

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """Handle table item double click"""
        row = item.row()
        document_name = self.invoice_table.item(row, 0).text()
        self.document_selected.emit(document_name)

    def show_error_message(self, title: str, message: str):
        """Show error message box"""
        QMessageBox.warning(self, title, message)

    def show_info_message(self, title: str, message: str):
        """Show information message box"""
        QMessageBox.information(self, title, message)

    def update_autocomplete_suggestions(self, suggestions: List[str]):
        """Update autocomplete suggestions"""
        self.setup_autocomplete(suggestions)

    def focus_document_input(self):
        """Set focus to document input field"""
        self.document_input.setFocus()

    def set_document_input_text(self, text: str):
        """Set document input text"""
        self.document_input.setText(text)

    def get_document_at_row(self, row: int) -> Optional[str]:
        """Get document name at specific row"""
        if 0 <= row < self.invoice_table.rowCount():
            item = self.invoice_table.item(row, 0)
            return item.text() if item else None
        return None
