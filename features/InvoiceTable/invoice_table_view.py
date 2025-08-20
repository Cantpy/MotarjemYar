import sys
from typing import List, Optional, Dict, Any
from functools import partial
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QPushButton, QCheckBox, QLabel, QComboBox, QHeaderView,
    QMenu, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, QUrl, QPoint, Signal
from PySide6.QtGui import QAction, QDesktopServices
from features.InvoiceTable.invoice_table_models import InvoiceData, InvoiceSummary
from features.InvoiceTable.invoice_table_controller import MainController
from features.InvoiceTable.invoice_table_logic import NumberFormatLogic
import logging

from shared import return_resource

invoices_db_path = return_resource('databases', 'invoices.db')
users_db_path = return_resource('databases', 'users.db')

logger = logging.getLogger(__name__)


class InvoiceTableView(QWidget):
    """Main view for the invoice table"""

    # Signals
    add_invoice_requested = Signal()
    edit_invoice_requested = Signal(str)  # invoice_number

    def __init__(self, invoices_db_url: str, users_db_url: str, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Initialize controller
        self.controller = MainController(invoices_db_url, users_db_url, self)

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

        # Data
        self.invoices = []
        self.translator_names = []

        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._load_initial_data()

    def _setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("فاکتورها صادر شده")
        self.setGeometry(100, 100, 800, 600)
        self.setLayoutDirection(Qt.RightToLeft)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Initialize components
        self._create_search_bar()
        self._create_selection_controls()
        self._create_column_checkboxes()
        self._create_table()
        self._create_action_buttons()

    def _create_search_bar(self):
        """Create the search bar"""
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجو بر اساس نام، کد ملی، شماره تماس، یا غیره ...")
        search_layout.addWidget(self.search_bar)
        self.layout.addLayout(search_layout)

    def _create_table(self):
        """Create and configure the main table"""
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

    def _create_selection_controls(self):
        """Set up bulk selection controls"""
        selection_layout = QHBoxLayout()

        # Select all checkbox
        self.select_all_checkbox = QCheckBox("انتخاب همه")
        selection_layout.addWidget(self.select_all_checkbox)

        # Selected count label
        self.selected_count_label = QLabel("0 مورد انتخاب شده")
        selection_layout.addWidget(self.selected_count_label)

        selection_layout.addStretch()

        # Filter button
        self.filter_button = QPushButton("فیلتر کردن ستونها")
        selection_layout.addWidget(self.filter_button)

        # Bulk delete button
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        selection_layout.addWidget(self.bulk_delete_btn)

        # Export button
        self.export_btn = QPushButton("📊 صادرات انتخابی")
        self.export_btn.setEnabled(False)
        selection_layout.addWidget(self.export_btn)

        self.layout.addLayout(selection_layout)

    def _create_column_checkboxes(self):
        """Create column visibility checkboxes"""
        self.column_checkboxes_layout = QHBoxLayout()
        self.column_checkboxes = []

        column_names = self.controller.get_invoice_controller().get_column_names()

        for i, name in enumerate(column_names):
            checkbox = QCheckBox(name)
            checkbox.setVisible(False)
            checkbox.setChecked(True)  # Default visible
            self.column_checkboxes.append(checkbox)
            self.column_checkboxes_layout.addWidget(checkbox)

        self.layout.insertLayout(-1, self.column_checkboxes_layout)

    def _create_action_buttons(self):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(50, 0, 50, 0)
        button_layout.setSpacing(20)

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

    def _connect_signals(self):
        """Connect signals to slots"""
        # Controller signals
        invoice_controller = self.controller.get_invoice_controller()
        invoice_controller.data_loaded.connect(self._on_data_loaded)
        invoice_controller.data_filtered.connect(self._on_data_filtered)
        invoice_controller.selection_changed.connect(self._on_selection_changed)
        invoice_controller.error_occurred.connect(self.controller.show_error_dialog)
        invoice_controller.success_message.connect(self.controller.show_success_dialog)

        file_controller = self.controller.get_file_controller()
        file_controller.pdf_found.connect(self._open_pdf_file)
        file_controller.pdf_not_found.connect(self._handle_missing_pdf)

        # UI signals
        self.search_bar.textChanged.connect(self._on_search_changed)
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        self.filter_button.clicked.connect(self._toggle_column_checkboxes)
        self.bulk_delete_btn.clicked.connect(self._on_bulk_delete)
        self.export_btn.clicked.connect(self._on_export_selected)

        # Action buttons
        self.add_invoice_btn.clicked.connect(self._on_add_invoice)
        self.edit_invoice_btn.clicked.connect(self._on_edit_invoice)
        self.delete_invoice_btn.clicked.connect(self._on_delete_invoice)
        self.summary_btn.clicked.connect(self._on_show_summary)
        self.refresh_btn.clicked.connect(self._on_refresh)

        # Table signals
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Column checkboxes
        for i, checkbox in enumerate(self.column_checkboxes):
            checkbox.stateChanged.connect(
                lambda state, col=i: self._on_column_visibility_changed(col, state)
            )

    def _load_initial_data(self):
        """Load initial data and settings"""
        # Load column settings
        self.controller.get_invoice_controller().load_column_settings()
        self._restore_column_visibility()

        # Load translator names
        self.translator_names = self.controller.get_invoice_controller().get_translator_names()

        # trigger data loading
        self.controller.get_invoice_controller().load_data()

    def _on_data_loaded(self, invoices: List[InvoiceData]):
        """Handle data loaded signal"""
        self.invoices = invoices
        self._populate_table(invoices)

    def _on_data_filtered(self, filtered_invoices: List[InvoiceData]):
        """Handle data filtered signal"""
        self._populate_table(filtered_invoices)

    def _populate_table(self, invoices: List[InvoiceData]):
        """Populate the table with invoice data"""
        self.table.setRowCount(len(invoices))
        self.table.setColumnCount(11)  # Including checkbox column

        headers = [
            "انتخاب", "شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
            "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزینه فاکتور", "مشاهده فاکتور"
        ]
        self.table.setHorizontalHeaderLabels(headers)

        # Set header resize mode
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        for row_idx, invoice in enumerate(invoices):
            self._populate_row(row_idx, invoice)

        self._apply_column_visibility()
        self._update_selection_ui()

    def _populate_row(self, row_idx: int, invoice: InvoiceData):
        """Populate a single table row"""
        # Checkbox for selection
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._on_row_selection_changed)
        self.table.setCellWidget(row_idx, 0, checkbox)

        # Invoice data columns
        data_columns = [
            NumberFormatLogic.to_persian_number(str(invoice.invoice_number)),
            invoice.name,
            invoice.national_id,
            invoice.phone,
            invoice.issue_date,
            invoice.delivery_date or "",
        ]

        for col_idx, value in enumerate(data_columns):
            item = self._create_table_item(str(value))
            self.table.setItem(row_idx, col_idx + 1, item)

        # Translator column (combo box or text)
        self._setup_translator_column(row_idx, invoice)

        # Document count
        doc_count = self.controller.get_invoice_controller().get_document_count(invoice.invoice_number)
        doc_count_item = self._create_table_item(NumberFormatLogic.to_persian_number(str(doc_count)))
        self.table.setItem(row_idx, 8, doc_count_item)

        # Price column
        formatted_price = NumberFormatLogic.format_currency(invoice.total_amount)
        price_item = self._create_table_item(formatted_price)
        self.table.setItem(row_idx, 9, price_item)

        # PDF button
        pdf_button = QPushButton("مشاهده فاکتور")
        pdf_button.clicked.connect(partial(self._on_open_pdf, invoice.invoice_number))
        self.table.setCellWidget(row_idx, 10, pdf_button)

    def _create_table_item(self, text: str) -> QTableWidgetItem:
        """Create a table item with center alignment"""
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def _setup_translator_column(self, row_idx: int, invoice: InvoiceData):
        """Setup translator column (combo box or text item)"""
        if not invoice.translator or invoice.translator == "نامشخص":
            translator_combo = QComboBox()
            translator_combo.addItems(self.translator_names)
            translator_combo.currentTextChanged.connect(
                lambda name, inv_num=invoice.invoice_number: self._on_translator_changed(inv_num, name)
            )
            self.table.setCellWidget(row_idx, 7, translator_combo)
        else:
            translator_item = self._create_table_item(invoice.translator)
            self.table.setItem(row_idx, 7, translator_item)

    def _apply_column_visibility(self):
        """Apply column visibility settings"""
        invoice_controller = self.controller.get_invoice_controller()

        for col_index in range(len(self.column_checkboxes)):
            is_visible = invoice_controller.is_column_visible(col_index)
            self.table.setColumnHidden(col_index + 1, not is_visible)

        # Always show checkbox column
        self.table.setColumnHidden(0, False)

    def _restore_column_visibility(self):
        """Restore column visibility from settings"""
        invoice_controller = self.controller.get_invoice_controller()

        for i, checkbox in enumerate(self.column_checkboxes):
            is_visible = invoice_controller.is_column_visible(i)
            checkbox.blockSignals(True)
            checkbox.setChecked(is_visible)
            checkbox.blockSignals(False)

    def _on_search_changed(self, text: str):
        """Handle search text changed"""
        self.controller.get_invoice_controller().search_invoices(text)

    def _on_select_all_changed(self, state: int):
        """Handle select all checkbox state changed"""
        is_checked = (state == Qt.CheckState.Checked.value)

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if isinstance(checkbox, QCheckBox):
                    checkbox.blockSignals(True)
                    checkbox.setChecked(is_checked)
                    checkbox.blockSignals(False)

        self._update_selection()

    def _on_row_selection_changed(self):
        """Handle individual row selection changed"""
        self._update_selection()

    def _update_selection(self):
        """Update selection state and UI"""
        selected_invoices = []

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                    invoice_item = self.table.item(row, 1)
                    if invoice_item:
                        invoice_number = NumberFormatLogic.to_english_number(invoice_item.text())
                        selected_invoices.append(invoice_number)

        self.controller.get_invoice_controller().update_selection(selected_invoices)

    def _on_selection_changed(self, selected_count: int):
        """Handle selection changed signal from controller"""
        self._update_selection_ui(selected_count)

    def _update_selection_ui(self, selected_count: int = None):
        """Update the selection UI elements"""
        if selected_count is None:
            selected_count = self._get_selected_count()

        total_visible = self._get_visible_count()

        self.selected_count_label.setText(f"{NumberFormatLogic.to_persian_number(str(selected_count))} مورد انتخاب شده")
        self.bulk_delete_btn.setEnabled(selected_count > 0)
        self.export_btn.setEnabled(selected_count > 0)

        # Update select all checkbox state
        self.select_all_checkbox.blockSignals(True)
        if selected_count == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        elif selected_count == total_visible:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        self.select_all_checkbox.blockSignals(False)

    def _get_selected_count(self) -> int:
        """Get the number of selected visible rows"""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                    count += 1
        return count

    def _get_visible_count(self) -> int:
        """Get the number of visible rows"""
        return sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))

    def _toggle_column_checkboxes(self):
        """Toggle visibility of column checkboxes"""
        self.checkboxes_visible = not self.checkboxes_visible

        for checkbox in self.column_checkboxes:
            checkbox.setVisible(self.checkboxes_visible)

        self.filter_button.setText(
            "پنهان کردن فیلتر" if self.checkboxes_visible else "فیلتر ستون‌ها"
        )

    def _on_column_visibility_changed(self, column_index: int, state: int):
        """Handle column visibility checkbox changed"""
        is_visible = (state == Qt.CheckState.Checked.value)
        self.controller.get_invoice_controller().set_column_visibility(column_index, is_visible)
        self.table.setColumnHidden(column_index + 1, not is_visible)

    def _on_bulk_delete(self):
        """Handle bulk delete button clicked"""
        self.controller.get_invoice_controller().delete_selected_invoices(
            self.controller.show_confirmation_dialog
        )

    def _on_export_selected(self):
        """Handle export selected button clicked"""

        def get_file_path():
            return self.controller.show_save_dialog(
                "صادرات داده‌های انتخابی",
                f"selected_invoices.csv",
                "CSV Files (*.csv)"
            )

        self.controller.get_invoice_controller().export_selected_to_csv(get_file_path)

    def _on_add_invoice(self):
        """Handle add invoice button clicked"""
        self.add_invoice_requested.emit()

    def _on_edit_invoice(self):
        """Handle edit invoice button clicked"""
        row = self.table.currentRow()
        if row == -1:
            self.controller.show_error_dialog("هشدار", "هیچ فاکتوری انتخاب نشده است.")
            return

        invoice_item = self.table.item(row, 1)
        if invoice_item:
            invoice_number = NumberFormatLogic.to_english_number(invoice_item.text())
            self._show_edit_dialog(invoice_number)

    def _on_delete_invoice(self):
        """Handle delete invoice button clicked"""
        row = self.table.currentRow()
        if row == -1:
            self.controller.show_error_dialog("هشدار", "هیچ فاکتوری انتخاب نشده است.")
            return

        invoice_item = self.table.item(row, 1)
        if invoice_item:
            invoice_number = NumberFormatLogic.to_english_number(invoice_item.text())
            self.controller.get_invoice_controller().delete_single_invoice(
                invoice_number, self.controller.show_confirmation_dialog
            )

    def _on_show_summary(self):
        """Handle show summary button clicked"""
        summary = self.controller.get_invoice_controller().get_invoice_summary()
        if summary:
            self._show_summary_dialog(summary)

    def _on_refresh(self):
        """Handle refresh button clicked"""
        self.controller.get_invoice_controller().refresh_data()
        self.search_bar.clear()

    def _on_translator_changed(self, invoice_number: str, translator_name: str):
        """Handle translator selection changed"""
        if translator_name and translator_name != "نامشخص":
            self.controller.get_invoice_controller().update_translator(
                invoice_number, translator_name, self.controller.show_confirmation_dialog
            )

    def _on_open_pdf(self, invoice_number: str):
        """Handle open PDF button clicked"""
        self.controller.get_file_controller().open_pdf(invoice_number)

    def _open_pdf_file(self, file_path: str):
        """Open PDF file in default application"""
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            self.controller.show_error_dialog("خطا", f"خطا در باز کردن فایل: {e}")

    def _handle_missing_pdf(self, invoice_number: str):
        """Handle missing PDF file"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("فایل پیدا نشد")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(
            f"فایل PDF فاکتور شماره {NumberFormatLogic.to_persian_number(invoice_number)} پیدا نشد.\n"
            "آیا می‌خواهید مسیر جدید را انتخاب کنید؟"
        )

        browse_button = msg_box.addButton("انتخاب فایل", QMessageBox.ButtonRole.ActionRole)
        cancel_button = msg_box.addButton("انصراف", QMessageBox.ButtonRole.RejectRole)
        msg_box.exec()

        if msg_box.clickedButton() == browse_button:
            def get_file_path():
                return self.controller.show_file_dialog(
                    f"انتخاب فایل PDF برای فاکتور شماره {NumberFormatLogic.to_persian_number(invoice_number)}",
                    "PDF Files (*.pdf)"
                )

            self.controller.get_file_controller().browse_for_pdf(invoice_number, get_file_path)

    def _show_context_menu(self, position: QPoint):
        """Show context menu for table rows"""
        if self.table.itemAt(position) is None:
            return

        menu = QMenu(self)

        edit_action = QAction("ویرایش فاکتور", self)
        edit_action.triggered.connect(self._on_edit_invoice)
        menu.addAction(edit_action)

        delete_action = QAction("حذف فاکتور", self)
        delete_action.triggered.connect(self._on_delete_invoice)
        menu.addAction(delete_action)

        menu.exec(self.table.mapToGlobal(position))

    def _show_edit_dialog(self, invoice_number: str):
        """Show edit invoice dialog"""
        dialog = EditInvoiceDialog(invoice_number, self.controller, self)
        if dialog.exec():
            # Refresh data after successful edit
            self.controller.get_invoice_controller().refresh_data()

    def _show_summary_dialog(self, summary: InvoiceSummary):
        """Show invoice summary dialog"""
        dialog = SummaryDialog(summary, self)
        dialog.exec()

    def closeEvent(self, event):
        """Handle window close event"""
        self.controller.get_invoice_controller().save_column_settings()
        event.accept()

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Delete:
            self._on_delete_invoice()
        elif event.key() == Qt.Key_F5:
            self._on_refresh()
        elif event.key() == Qt.Key_Escape:
            self.search_bar.clear()
        else:
            super().keyPressEvent(event)


class EditInvoiceDialog(QDialog):
    """Dialog for editing invoice data"""

    def __init__(self, invoice_number: str, controller: MainController, parent=None):
        super().__init__(parent)
        self.invoice_number = invoice_number
        self.controller = controller

        self.setWindowTitle("ویرایش اطلاعات فاکتور")
        self.setModal(True)
        self.resize(400, 300)

        # Get current invoice data
        self.invoice_data = (controller.get_invoice_controller().repo_manager.get_invoice_repository()
                             .get_invoice_by_number(invoice_number))

        if not self.invoice_data:
            self.reject()
            return

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
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

    def accept(self):
        """Handle dialog accept"""
        updates = {
            'name': self.fields['name'].text().strip(),
            'national_id': self.fields['national_id'].text().strip(),
            'phone': self.fields['phone'].text().strip(),
            'delivery_date': self.fields['delivery_date'].text().strip(),
            'translator': self.fields['translator'].text().strip()
        }

        # Validate data
        validation_controller = self.controller.get_validation_controller()

        if not updates['name']:
            self.controller.show_error_dialog("خطا", "نام الزامی است")
            return

        if not updates['national_id']:
            self.controller.show_error_dialog("خطا", "کد ملی الزامی است")
            return

        if not validation_controller.validate_national_id(updates['national_id']):
            self.controller.show_error_dialog("خطا", "کد ملی معتبر نیست")
            return

        if not updates['phone']:
            self.controller.show_error_dialog("خطا", "شماره تماس الزامی است")
            return

        if not validation_controller.validate_phone_number(updates['phone']):
            self.controller.show_error_dialog("خطا", "شماره تماس معتبر نیست")
            return

        # Update invoice
        self.controller.get_invoice_controller().update_invoice_data(self.invoice_number, updates)
        super().accept()


class SummaryDialog(QDialog):
    """Dialog for showing invoice summary"""

    def __init__(self, summary: InvoiceSummary, parent=None):
        super().__init__(parent)
        self.summary = summary

        self.setWindowTitle("خلاصه فاکتورها")
        self.setModal(True)
        self.resize(400, 300)

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
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
