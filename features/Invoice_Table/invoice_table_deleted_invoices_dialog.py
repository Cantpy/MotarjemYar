# features/Invoice_Table/invoice_table_deleted_dialog.py

from typing import List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QDialogButtonBox, QHeaderView)
from shared.orm_models.invoices_models import DeletedInvoiceData
from shared.utils.date_utils import to_jalali
from shared.utils.persian_tools import to_persian_numbers


class DeletedInvoicesDialog(QDialog):
    """
    A read-only dialog to display a list of deleted invoices.
    """

    def __init__(self, deleted_invoices: List[DeletedInvoiceData], parent=None):
        super().__init__(parent)
        self.setWindowTitle("فاکتورهای حذف شده")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumSize(900, 600)

        self._deleted_invoices = deleted_invoices
        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        """Initializes the UI layout and widgets."""
        main_layout = QVBoxLayout(self)

        # Create the table
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        headers = [
            "شماره فاکتور", "نام مشتری", "تاریخ صدور",
            "مبلغ نهایی", "تاریخ حذف", "حذف شده توسط"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        main_layout.addWidget(self.table)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.button(QDialogButtonBox.StandardButton.Close).setText("بستن")
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_table(self):
        """Fills the table with data from the deleted invoices."""
        self.table.setRowCount(len(self._deleted_invoices))

        for row, invoice in enumerate(self._deleted_invoices):
            final_amount = to_persian_numbers(f"{invoice.final_amount:,}")
            issue_date = to_persian_numbers(to_jalali(invoice.issue_date, include_time=False))
            deleted_at = to_persian_numbers(to_jalali(invoice.deleted_at, include_time=True))

            self.table.setItem(row, 0, QTableWidgetItem(to_persian_numbers(invoice.invoice_number)))
            self.table.setItem(row, 1, QTableWidgetItem(invoice.name))
            self.table.setItem(row, 2, QTableWidgetItem(issue_date))
            self.table.setItem(row, 3, QTableWidgetItem(final_amount))
            self.table.setItem(row, 4, QTableWidgetItem(deleted_at))
            self.table.setItem(row, 5, QTableWidgetItem(invoice.deleted_by or "نامشخص"))

        # Resize columns to fit content
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.resizeColumnsToContents()
