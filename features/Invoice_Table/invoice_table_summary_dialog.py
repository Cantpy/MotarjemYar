# features/Invoice_Table/invoice_table_summary_dialog.py

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QDialogButtonBox, QTabWidget, QWidget,
                               QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView)

from features.Invoice_Table.invoice_table_repo import EditedInvoiceData
from features.Invoice_Table.invoice_table_models import InvoiceData, InvoiceItemData

from shared.utils.date_utils import to_jalali
from shared.utils.persian_tools import to_persian_numbers


class InvoiceSummaryDialog(QDialog):
    """A dialog to display a read-only summary of an invoice."""

    FIELD_NAME_MAP = {
        "name": "نام مشتری",
        "national_id": "کد ملی",
        "phone": "شماره تماس",
        "delivery_date": "تاریخ تحویل",
        "translator": "مترجم",
        "remarks": "توضیحات",
        # Add other fields here as they become editable
    }

    def __init__(self, invoice: InvoiceData, items: List[InvoiceItemData], history: List[EditedInvoiceData],
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"خلاصه فاکتور شماره {to_persian_numbers(invoice.invoice_number)}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumSize(800, 600)

        self._invoice_data = invoice
        self._invoice_items = items
        self._edit_history = history

        main_layout = QVBoxLayout(self)

        # Create Tab Widget
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Create the two tabs and add them
        tabs.addTab(self._create_main_info_tab(), "اطلاعات اصلی فاکتور")
        tabs.addTab(self._create_items_tab(), f"اقلام فاکتور ({to_persian_numbers(len(items))})")
        tabs.addTab(self._create_history_tab(), f"تاریخچه تغییرات ({to_persian_numbers(len(history))})")

        # Add a close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.button(QDialogButtonBox.StandardButton.Close).setText("بستن")
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _create_main_info_tab(self) -> QWidget:
        """Creates the tab with the main invoice details."""
        tab_widget = QWidget()
        layout = QFormLayout(tab_widget)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # --- Helper functions for formatting ---
        def _format_currency(amount):
            return f"{to_persian_numbers(f'{amount:,}')} ریال"

        def _map_payment_status(status):
            return "پرداخت شده" if status == 1 else "پرداخت نشده"

        def _map_delivery_status(status):
            statuses = {0: "در انتظار", 1: "آماده تحویل", 2: "تحویل داده شده", 3: "لغو شده", 4: "در حال انجام"}
            return statuses.get(status, "نامشخص")

        # --- Populate Form ---
        # Customer Info
        layout.addRow(QLabel("<b>اطلاعات مشتری</b>"), QLabel(""))
        layout.addRow("نام مشتری:", QLabel(self._invoice_data.name))
        layout.addRow("کد ملی:", QLabel(to_persian_numbers(self._invoice_data.national_id)))
        layout.addRow("شماره تماس:", QLabel(to_persian_numbers(self._invoice_data.phone)))

        # Dates and Status
        layout.addRow(QLabel("<b>جزئیات و وضعیت</b>"), QLabel(""))
        layout.addRow("تاریخ صدور:", QLabel(to_persian_numbers(to_jalali(self._invoice_data.issue_date, True))))
        layout.addRow("تاریخ تحویل:", QLabel(to_persian_numbers(to_jalali(self._invoice_data.delivery_date, True))))
        layout.addRow("وضعیت پرداخت:", QLabel(_map_payment_status(self._invoice_data.payment_status)))
        layout.addRow("وضعیت تحویل:", QLabel(_map_delivery_status(self._invoice_data.delivery_status)))

        # --- UPDATED: Financial Info Section ---
        layout.addRow(QLabel("<b>اطلاعات مالی</b>"), QLabel(""))
        layout.addRow("جمع کل هزینه ها (قبل از تخفیف):", QLabel(_format_currency(self._invoice_data.total_amount)))
        layout.addRow(" - هزینه ترجمه:", QLabel(_format_currency(self._invoice_data.total_translation_price)))
        layout.addRow(" - هزینه نسخه اضافی:", QLabel(_format_currency(self._invoice_data.total_certified_copy_price)))
        layout.addRow(" - هزینه ثبت:", QLabel(_format_currency(self._invoice_data.total_registration_price)))
        layout.addRow(" - هزینه تاییدات:", QLabel(_format_currency(self._invoice_data.total_confirmation_price)))
        layout.addRow(" - هزینه نسخ مازاد:", QLabel(_format_currency(self._invoice_data.total_additional_issues_price)))
        layout.addRow("تخفیف:", QLabel(_format_currency(self._invoice_data.discount_amount)))
        layout.addRow("هزینه فوریت:", QLabel(_format_currency(self._invoice_data.emergency_cost)))
        layout.addRow("پیش پرداخت:", QLabel(_format_currency(self._invoice_data.advance_payment)))
        layout.addRow("<b>مبلغ نهایی:</b>", QLabel(f"<b>{_format_currency(self._invoice_data.final_amount)}</b>"))

        # Other Info
        layout.addRow(QLabel("<b>سایر اطلاعات</b>"), QLabel(""))
        layout.addRow("مترجم:", QLabel(self._invoice_data.translator))
        layout.addRow("زبان مبدا:", QLabel(self._invoice_data.source_language))
        layout.addRow("زبان مقصد:", QLabel(self._invoice_data.target_language))
        layout.addRow("کاربر صادر کننده:", QLabel(self._invoice_data.username or "نامشخص"))

        remarks_text = QTextEdit(self._invoice_data.remarks or "ندارد")
        remarks_text.setReadOnly(True)
        layout.addRow("توضیحات کلی:", remarks_text)

        return tab_widget

    def _create_items_tab(self) -> QWidget:
        """Creates the tab with a table of all invoice items, now with more detail."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # --- UPDATED HEADERS ---
        headers = ["نام سرویس", "تعداد", "صفحات", "نسخه اضافی", "رسمی", "مهر دادگستری", "مهر خارجه", "جزئیات اضافی",
                   "مبلغ کل"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        def _format_boolean(value):
            return "بله" if value == 1 else "خیر"

        # --- Populate Table ---
        for row, item in enumerate(self._invoice_items):
            table.insertRow(row)

            # --- Build the "Additional Details" string ---
            details = []
            if item.dynamic_price_1 and item.dynamic_price_amount_1 > 0:
                price_str = to_persian_numbers(f"{item.dynamic_price_amount_1:,}")
                details.append(f"{item.dynamic_price_1} ({price_str})")

            if item.dynamic_price_2 and item.dynamic_price_amount_2 > 0:
                price_str = to_persian_numbers(f"{item.dynamic_price_amount_2:,}")
                details.append(f"{item.dynamic_price_2} ({price_str})")

            if item.remarks:
                details.append(f"توضیحات: {item.remarks}")

            details_str = " | ".join(details)

            print(f'Found details for item {item.service_name} with id {item.service_id}: {details_str}')

            # --- Set table cell values ---
            table.setItem(row, 0, QTableWidgetItem(item.service_name))
            table.setItem(row, 1, QTableWidgetItem(to_persian_numbers(str(item.quantity))))
            table.setItem(row, 2, QTableWidgetItem(to_persian_numbers(str(item.page_count))))
            table.setItem(row, 3, QTableWidgetItem(to_persian_numbers(str(item.additional_issues))))
            table.setItem(row, 4, QTableWidgetItem(_format_boolean(item.is_official)))
            table.setItem(row, 5, QTableWidgetItem(_format_boolean(item.has_judiciary_seal)))
            table.setItem(row, 6, QTableWidgetItem(_format_boolean(item.has_foreign_affairs_seal)))
            table.setItem(row, 7, QTableWidgetItem(details_str))
            table.setItem(row, 8, QTableWidgetItem(to_persian_numbers(f"{item.total_price:,}")))

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        return tab_widget

    def _create_history_tab(self) -> QWidget:
        """Creates the tab with a table of all invoice edits with full formatting."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        table = QTableWidget()
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        headers = ["فیلد تغییر یافته", "مقدار قدیمی", "مقدار جدید", "کاربر", "زمان تغییر"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        table.setRowCount(len(self._edit_history))
        for row, edit in enumerate(self._edit_history):
            # 1. Translate field name to Persian
            persian_field_name = self.FIELD_NAME_MAP.get(edit.edited_field, edit.edited_field)

            # 2. Prepare display values, assuming string by default
            old_value_display = str(edit.old_value or "")
            new_value_display = str(edit.new_value or "")

            # --- MODIFICATION START ---
            # 3. If the field is a date, re-format the string values for display
            from datetime import datetime
            if edit.edited_field == 'delivery_date':
                try:
                    # Format the old value if it exists
                    if edit.old_value:
                        dt_obj_old = datetime.strptime(edit.old_value, '%Y-%m-%d %H:%M:%S')
                        old_value_display = to_jalali(dt_obj_old, include_time=True)
                except (ValueError, TypeError):
                    # If parsing fails, just show the raw data
                    pass

                try:
                    # Format the new value if it exists
                    if edit.new_value:
                        dt_obj_new = datetime.strptime(edit.new_value, '%Y-%m-%d %H:%M:%S')
                        new_value_display = to_jalali(dt_obj_new, include_time=True)
                except (ValueError, TypeError):
                    pass
            # --- MODIFICATION END ---

            # 4. Format the final timestamp
            jalali_timestamp = to_jalali(edit.edited_at, include_time=True)

            # 5. Populate the table with fully formatted, Persian-numbered strings
            table.setItem(row, 0, QTableWidgetItem(persian_field_name))
            table.setItem(row, 1, QTableWidgetItem(to_persian_numbers(old_value_display)))
            table.setItem(row, 2, QTableWidgetItem(to_persian_numbers(new_value_display)))
            table.setItem(row, 3, QTableWidgetItem(edit.edited_by))
            table.setItem(row, 4, QTableWidgetItem(to_persian_numbers(jalali_timestamp)))

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        return tab_widget
