# features/Invoice_Table/invoice_table_edit_dialog.py

"""

"""

import getpass
import jdatetime
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QWidget, QFormLayout, QLineEdit, QDialogButtonBox, QTextEdit)

from shared.orm_models.invoices_models import InvoiceData, InvoiceItemData, EditedInvoiceData
from shared.utils.persian_tools import to_english_numbers
from shared.utils.date_utils import to_jalali
from shared.session_provider import SessionManager
from shared.widgets.persian_calendar import InvoiceDatePicker


class EditInvoiceDialog(QDialog):
    """
    A focused dialog for editing an invoice's delivery date, translator, and remarks.
    """

    def __init__(self, invoice: InvoiceData, items: List[InvoiceItemData], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"ویرایش فاکتور شماره {invoice.invoice_number}")
        self.setMinimumSize(500, 350)  # Smaller size is more appropriate now
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._original_invoice = invoice
        self.invoice_number = invoice.invoice_number

        # --- UI Components ---
        self.delivery_date_picker: Optional[InvoiceDatePicker] = None
        self.translator_edit: Optional[QLineEdit] = None
        self.remarks_edit: Optional[QTextEdit] = None

        self._setup_ui()
        self._populate_data()

    def _setup_ui(self):
        """Initializes the UI layout and widgets without tabs."""
        main_layout = QVBoxLayout(self)

        # --- Create a single form widget instead of a tab widget ---
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(form_widget)

        # --- Initialize and add the three editable fields ---
        self.delivery_date_picker = InvoiceDatePicker()
        self.translator_edit = QLineEdit()
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMinimumHeight(80)  # Give it some space

        form_layout.addRow("تاریخ تحویل:", self.delivery_date_picker)
        form_layout.addRow("مترجم:", self.translator_edit)
        form_layout.addRow("توضیحات:", self.remarks_edit)

        # --- Dialog buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره تغییرات")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_data(self):
        """Fills the UI fields with the initial invoice data."""
        # Delivery Date
        delivery_date_val = self._original_invoice.delivery_date
        if isinstance(delivery_date_val, datetime):
            jalali_str = to_jalali(delivery_date_val, include_time=True)
            self.delivery_date_picker.setText(jalali_str)

        # Translator
        self.translator_edit.setText(self._original_invoice.translator or "")

        # Remarks
        self.remarks_edit.setText(self._original_invoice.remarks or "")

    def get_changes(self) -> Tuple[dict, List[EditedInvoiceData]]:
        """
        Compares original data with current UI data and returns the changes.
        """
        updates = {}
        history_records = []

        # Get editor's name once
        session_data = SessionManager().get_session()
        edited_by = (session_data.full_name if session_data and session_data.full_name
                     else session_data.username if session_data else getpass.getuser())

        # --- 1. Check Delivery Date ---
        original_date = self._original_invoice.delivery_date
        new_date_text = self.delivery_date_picker.text().strip()
        original_date_str = original_date.strftime('%Y-%m-%d %H:%M:%S') if original_date else ""
        new_date_for_db = None
        new_date_for_history = ""

        if new_date_text:
            try:
                jdt_obj = jdatetime.datetime.strptime(to_english_numbers(new_date_text), '%Y/%m/%d - %H:%M')
                greg_datetime = jdt_obj.togregorian()
                new_date_for_db = greg_datetime
                new_date_for_history = greg_datetime.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass  # Ignore invalid date formats

        if original_date_str != new_date_for_history:
            updates['delivery_date'] = new_date_for_db
            history_records.append(
                EditedInvoiceData(id=None,
                                  invoice_number=self.invoice_number,
                                  edited_field='delivery_date',
                                  old_value=original_date_str,
                                  new_value=new_date_for_history,
                                  edited_by=edited_by,
                                  edited_at=datetime.now(timezone.utc),
                                  remarks="Updated"))

        # --- 2. Check Translator ---
        original_translator = self._original_invoice.translator or ""
        new_translator = self.translator_edit.text().strip()
        if original_translator != new_translator:
            updates['translator'] = new_translator
            history_records.append(
                EditedInvoiceData(id=None,
                                  invoice_number=self.invoice_number,
                                  edited_field='translator',
                                  old_value=original_translator,
                                  new_value=new_translator,
                                  edited_by=edited_by,
                                  edited_at=datetime.now(timezone.utc),
                                  remarks="Updated"))

        # --- 3. Check Remarks ---
        original_remarks = self._original_invoice.remarks or ""
        new_remarks = self.remarks_edit.toPlainText().strip()
        if original_remarks != new_remarks:
            updates['remarks'] = new_remarks
            history_records.append(
                EditedInvoiceData(id=None,
                                  invoice_number=self.invoice_number,
                                  edited_field='remarks',
                                  old_value=original_remarks,
                                  new_value=new_remarks,
                                  edited_by=edited_by,
                                  edited_at=datetime.now(timezone.utc),
                                  remarks="Updated"))

        return updates, history_records
