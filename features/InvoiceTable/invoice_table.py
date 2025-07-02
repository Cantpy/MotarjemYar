from PySide6.QtGui import QDesktopServices, QAction
from PySide6.QtCore import Qt, QUrl, QSettings, QPoint
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QMessageBox,
    QHeaderView, QCheckBox, QComboBox, QFileDialog, QLabel, QDialog, QMenu
)
import sqlite3
import os
import sys
import json
from functools import partial
from modules.CalendadrPopup import DatePickerLineEdit, CalendarPopup
from modules.helper_functions import return_resource, to_persian_number
from modules.InvoiceTable.helper_functions import find_file_by_name, PricingDetailsDialog

invoices_database = return_resource('databases', 'invoices.db')
users_database = return_resource('databases', 'users.db')


class InvoiceTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._setup_ui()
        self._initialize_data()

    def _setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("فاکتورها صادر شده")
        self.setGeometry(100, 100, 800, 600)
        self.setLayoutDirection(Qt.RightToLeft)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Initialize components
        self._create_search_bar()
        self._create_table()
        self._create_buttons()

    def _initialize_data(self):
        """Initialize data and load content."""
        self.rows = []
        self.translator_names = self._load_translator_names()
        self.load_data()

    def _create_search_bar(self):
        """Create the search bar."""
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجو بر اساس نام، کد ملی، شماره تماس، یا غیره ...")
        self.search_bar.textChanged.connect(self.filter_data)
        search_layout.addWidget(self.search_bar)
        self.layout.addLayout(search_layout)

    def _create_column_checkboxes(self):
        """Create column visibility checkboxes."""
        self.column_checkboxes_layout = QHBoxLayout()
        self.checkbox_settings = QSettings("CheckBoxes", "STATUS")
        self.column_names = [
            "شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
            "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزیته فاکتور", "مشاهده فاکتور"
        ]
        self.visible_columns = self._load_column_settings()
        self.column_checkboxes = []
        self.checkboxes_visible = False
        self._setup_checkboxes()

    def _create_table(self):
        """Create and configure the main table."""
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.setSortingEnabled(True)
        self._create_column_checkboxes()
        self._setup_selection_controls()
        self.layout.addWidget(self.table)

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

        # Filter button
        self.filter_button = QPushButton("فیلتر کردن ستونها")
        self.filter_button.clicked.connect(self._toggle_column_checkboxes)
        selection_layout.addWidget(self.filter_button)

        # Bulk delete button
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        self.bulk_delete_btn.clicked.connect(self._handle_bulk_delete)
        selection_layout.addWidget(self.bulk_delete_btn)

        self.layout.addLayout(selection_layout)

    def _create_buttons(self):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(50, 0, 50, 0)
        button_layout.setSpacing(20)

        self.add_invoice_btn = QPushButton("افزودن فاکتور")
        self.edit_invoice_btn = QPushButton("ویرایش فاکتور")
        self.delete_invoice_btn = QPushButton("حذف فاکتور")

        button_layout.addWidget(self.add_invoice_btn)
        button_layout.addWidget(self.edit_invoice_btn)
        button_layout.addWidget(self.delete_invoice_btn)

        self.layout.addLayout(button_layout)

        # Connect buttons
        self.add_invoice_btn.clicked.connect(self._handle_add_invoice)
        self.delete_invoice_btn.clicked.connect(self._handle_delete_invoice)
        self.edit_invoice_btn.clicked.connect(self._handle_edit_invoice)

    def _show_context_menu(self, position):
        """Show context menu for table rows."""
        if self.table.itemAt(position) is None:
            return

        menu = QMenu(self)

        edit_action = QAction("ویرایش فاکتور", self)
        edit_action.triggered.connect(self._handle_edit_invoice)
        menu.addAction(edit_action)

        delete_action = QAction("حذف فاکتور", self)
        delete_action.triggered.connect(self._handle_delete_invoice)
        menu.addAction(delete_action)

        menu.exec(self.table.mapToGlobal(position))

    def _load_translator_names(self):
        """Load translator names from users and user_profiles tables."""
        translator_names = ["نامشخص"]

        try:
            with sqlite3.connect(users_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.username 
                    FROM users u 
                    WHERE u.role = 'translator' AND u.active = 1
                """)
                translator_usernames = cursor.fetchall()

                for (username,) in translator_usernames:
                    cursor.execute("""
                        SELECT full_name 
                        FROM user_profiles 
                        WHERE username = ?
                    """, (username,))
                    result = cursor.fetchone()
                    if result and result[0]:
                        translator_names.append(result[0])

        except sqlite3.Error as e:
            print(f"Error loading translator names: {e}")
            translator_names.extend(["مریم", "علی", "رضا"])

        return translator_names

    def _toggle_column_checkboxes(self):
        """Toggle visibility of column checkboxes."""
        self.checkboxes_visible = not self.checkboxes_visible

        for checkbox in self.column_checkboxes:
            checkbox.setVisible(self.checkboxes_visible)

        self.filter_button.setText(
            "پنهان کردن فیلتر" if self.checkboxes_visible else "فیلتر ستون‌ها"
        )

    def _toggle_select_all(self, state):
        """Toggle all checkboxes based on select all checkbox state."""
        is_checked = (state == Qt.CheckState.Checked.value)

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if isinstance(checkbox, QCheckBox):
                    checkbox.blockSignals(True)
                    checkbox.setChecked(is_checked)
                    checkbox.blockSignals(False)

        self._update_selection_ui()

    def _update_selection_ui(self):
        """Update the selection UI elements."""
        selected_count = self._get_selected_count()
        total_visible = self._get_visible_count()

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

    def _get_selected_count(self):
        """Get the number of selected visible rows."""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                    count += 1
        return count

    def _get_visible_count(self):
        """Get the number of visible rows."""
        return sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))

    def _handle_bulk_delete(self):
        """Handle bulk deletion of selected invoices."""
        selected_invoices = []

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                invoice_number = self.table.item(row, 1).text()
                selected_invoices.append((row, invoice_number))

        if not selected_invoices:
            QMessageBox.warning(self, "هشدار", "هیچ فاکتوری انتخاب نشده است.")
            return

        confirm = QMessageBox.question(
            self, "حذف گروهی",
            f"آیا از حذف {len(selected_invoices)} فاکتور انتخاب شده مطمئن هستید؟"
        )

        if confirm == QMessageBox.Yes:
            self._delete_invoices([invoice for _, invoice in selected_invoices])

    def _delete_invoices(self, invoice_numbers):
        """Delete multiple invoices from database."""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                for invoice_number in invoice_numbers:
                    cursor.execute("DELETE FROM issued_invoices WHERE invoice_number = ?",
                                   (invoice_number,))
                conn.commit()

            QMessageBox.information(
                self, "حذف انجام شد",
                f"{len(invoice_numbers)} فاکتور با موفقیت حذف شد."
            )
            self.load_data()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطا", f"خطا در حذف فاکتورها: {e}")

    def _parse_document_count(self, items_json):
        """Parse JSON items and count documents."""
        try:
            items_list = json.loads(items_json)
            doc_count = 0

            for item in items_list:
                if isinstance(item, list) and len(item) > 2:
                    try:
                        doc_count += int(item[2])
                    except (ValueError, TypeError):
                        doc_count += 1

            return doc_count
        except json.JSONDecodeError:
            return 0

    def _get_document_count(self, invoice_number):
        """Get the count of documents for a specific invoice."""
        total_docs = 0
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ii.items, i.invoice_status
                    FROM invoice_items ii 
                    JOIN issued_invoices i ON ii.invoice_number = i.invoice_number
                    WHERE ii.invoice_number = ?
                """, (invoice_number,))
                rows = cursor.fetchall()

                for row in rows:
                    items_json, invoice_status = row
                    doc_count = self._parse_document_count(items_json)
                    total_docs += doc_count

                return total_docs
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"Error getting document count for invoice {invoice_number}: {e}")
            return 0

    def _handle_add_invoice(self):
        """Handle add invoice button click."""
        if hasattr(self.parent, 'setCurrentIndex'):
            self.parent.setCurrentIndex(3)

    def _handle_delete_invoice(self):
        """Handle delete invoice button click."""
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "هشدار", "هیچ فاکتوری انتخاب نشده است.")
            return

        invoice_number = self.table.item(row, 1).text()
        confirm = QMessageBox.question(
            self, "حذف فاکتور",
            f"آیا از حذف فاکتور شماره {invoice_number} مطمئن هستید؟"
        )

        if confirm == QMessageBox.Yes:
            self._delete_invoices([invoice_number])

    def _handle_edit_invoice(self):
        """Handle edit invoice button click."""
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.warning(self, "هشدار", "هیچ فاکتوری انتخاب نشده است.")
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("ویرایش فاکتور")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(
            "چطور می‌خواهید این فاکتور را ویرایش کنید؟\n\n"
            "توجه: برای ویرایش مترجم، تاریخ تحویل، شماره تماس و اطلاعات جدول "
            "از گزینه‌ی ویرایش اطلاعات استفاده کنید."
        )

        edit_items_button = msg_box.addButton("ویرایش آیتم‌های فاکتور", QMessageBox.ButtonRole.ActionRole)
        edit_data_button = msg_box.addButton("ویرایش اطلاعات فاکتور", QMessageBox.ButtonRole.YesRole)
        cancel_button = msg_box.addButton("انصراف", QMessageBox.ButtonRole.NoRole)

        msg_box.exec()
        clicked_button = msg_box.clickedButton()

        if clicked_button == edit_items_button:
            pass  # To be implemented
        elif clicked_button == edit_data_button:
            self._show_edit_invoice_data_dialog(row)

    def _show_edit_invoice_data_dialog(self, row):
        """Show dialog for editing invoice data."""
        invoice_number = self.table.item(row, 1).text()
        name = self.table.item(row, 2).text()
        national_id = self.table.item(row, 3).text()
        phone = self.table.item(row, 4).text()
        delivery_date = self.table.item(row, 6).text()
        translator = self.table.item(row, 7).text() if self.table.item(row, 7) else ""

        dialog = QDialog(self)
        dialog.setWindowTitle("ویرایش اطلاعات فاکتور")
        layout = QVBoxLayout(dialog)

        # Create form fields
        fields = {
            "name": self._create_field(layout, "نام", name),
            "national_id": self._create_field(layout, "کد ملی", national_id),
            "phone": self._create_field(layout, "شماره تماس", phone),
            "translator": self._create_field(layout, "مترجم", translator)
        }

        # Date picker field
        layout.addWidget(QLabel("تاریخ تحویل"))
        delivery_date_field = DatePickerLineEdit()
        delivery_date_field.setText(delivery_date)
        layout.addWidget(delivery_date_field)

        self._setup_calendar_popup(delivery_date_field)

        # Buttons
        self._create_dialog_buttons(layout, dialog)

        if dialog.exec():
            self._update_invoice_data(invoice_number, row, fields, delivery_date_field)

    def _create_field(self, layout, label_text, default_value):
        """Create a labeled input field."""
        layout.addWidget(QLabel(label_text))
        field = QLineEdit()
        field.setText(default_value)
        layout.addWidget(field)
        return field

    def _setup_calendar_popup(self, date_field):
        """Setup calendar popup for date field."""
        calendar_popup = CalendarPopup(self)
        calendar_popup.date_selected.connect(
            lambda date: date_field.setText(to_persian_number(date))
        )
        calendar_popup.hide()

        def show_calendar_popup(event):
            pos = date_field.mapToGlobal(QPoint(0, date_field.height()))
            calendar_popup.move(pos)
            calendar_popup.show()
            calendar_popup.raise_()
            event.accept()

        date_field.mousePressEvent = show_calendar_popup

    def _create_dialog_buttons(self, layout, dialog):
        """Create dialog buttons."""
        btn_save = QPushButton("ذخیره")
        btn_cancel = QPushButton("لغو")
        btn_save.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_cancel)
        layout.addLayout(button_layout)

    def _update_invoice_data(self, invoice_number, row, fields, delivery_date_field):
        """Update invoice data in database and table."""
        new_data = {
            "name": fields["name"].text(),
            "national_id": fields["national_id"].text(),
            "phone": fields["phone"].text(),
            "delivery_date": delivery_date_field.text(),
            "translator": fields["translator"].text()
        }

        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE issued_invoices SET
                        name = ?, national_id = ?, phone = ?, delivery_date = ?, translator = ?
                    WHERE invoice_number = ?
                """, (new_data["name"], new_data["national_id"], new_data["phone"],
                      new_data["delivery_date"], new_data["translator"], invoice_number))
                conn.commit()

            # Update table items
            self.table.item(row, 2).setText(new_data["name"])
            self.table.item(row, 3).setText(new_data["national_id"])
            self.table.item(row, 4).setText(new_data["phone"])
            self.table.item(row, 6).setText(new_data["delivery_date"])
            self.table.item(row, 7).setText(new_data["translator"])

            QMessageBox.information(self, "موفق", "اطلاعات با موفقیت به‌روزرسانی شد.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطا", f"خطا در به‌روزرسانی اطلاعات: {e}")

    def _setup_checkboxes(self):
        """Create and setup column visibility checkboxes."""
        for i, name in enumerate(self.column_names):
            checkbox = QCheckBox(name)
            checkbox.setVisible(False)
            self.column_checkboxes.append(checkbox)
            self.column_checkboxes_layout.addWidget(checkbox)

        self.layout.addLayout(self.column_checkboxes_layout)
        self._restore_checkbox_states()

        for checkbox in self.column_checkboxes:
            checkbox.stateChanged.connect(self._update_settings)

    def _update_settings(self):
        """Update QSettings and column visibility."""
        for i, checkbox in enumerate(self.column_checkboxes):
            is_checked = checkbox.isChecked()
            self.visible_columns[i] = is_checked
            self.checkbox_settings.setValue(f"column_visible_{i}", is_checked)
            self.table.setColumnHidden(i + 1, not is_checked)

    def _restore_checkbox_states(self):
        """Restore checkbox states from settings."""
        for i, checkbox in enumerate(self.column_checkboxes):
            saved_value = self.checkbox_settings.value(f"column_visible_{i}", True, type=bool)
            checkbox.setChecked(saved_value)
            self.table.setColumnHidden(i + 1, not saved_value)

    def _load_column_settings(self):
        """Load column visibility settings."""
        visible_columns = []
        for i in range(len(self.column_names)):
            value = self.checkbox_settings.value(f"column_visible_{i}")
            visible_columns.append(True if value is None else str(value).lower() in ("true", "1"))
        return visible_columns

    def load_data(self):
        """Load data from database and populate table."""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT invoice_number, name, national_id, phone, issue_date, delivery_date, 
                           translator, total_amount, pdf_file_path 
                    FROM issued_invoices
                """)
                self.rows = cursor.fetchall()

            self._populate_table()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Error loading data: {e}")

    def _populate_table(self):
        """Populate the table with data."""
        self.table.setRowCount(len(self.rows))
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "انتخاب", "شماره فاکتور", "نام", "کد ملی", "شماره تماس", "تاریخ صدور",
            "تاریخ تحویل", "مترجم", "تعداد اسناد", "هزینه فاکتور", "مشاهده فاکتور"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        for row_idx, row in enumerate(self.rows):
            self._populate_row(row_idx, row)

        self._apply_column_visibility()

    def _populate_row(self, row_idx, row):
        """Populate a single table row."""
        # Checkbox for selection
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._update_selection_ui)
        self.table.setCellWidget(row_idx, 0, checkbox)

        # Data columns
        for col_idx, value in enumerate(row[:-1]):
            if col_idx == 0:  # Invoice number - convert to Persian
                text = to_persian_number(str(value))
            else:
                text = str(value)

            item = self._create_table_item(text)
            self.table.setItem(row_idx, col_idx + 1, item)

        # Document count column (Persian numbers)
        doc_count = self._get_document_count(row[0])
        doc_count_item = self._create_table_item(to_persian_number(str(doc_count)))
        self.table.setItem(row_idx, 8, doc_count_item)

        # Translator column
        self._setup_translator_column(row_idx, row[6], row[0])

        # Price column (formatted)
        self._setup_price_column(row_idx, row[7])

        # PDF button
        pdf_button = QPushButton("مشاهده فاکتور")
        pdf_button.clicked.connect(partial(self._open_pdf, row[0]))
        self.table.setCellWidget(row_idx, 10, pdf_button)

    def _create_table_item(self, text):
        """Create a table item with center alignment."""
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def _setup_translator_column(self, row_idx, translator_name, invoice_number):
        """Setup translator column (combo box or text item)."""
        if translator_name in (None, "", "نامشخص"):
            translator_combo = QComboBox()
            translator_combo.addItems(self.translator_names)
            translator_combo.currentTextChanged.connect(
                lambda name, inv=invoice_number: self._update_translator_in_db(inv, name)
            )
            self.table.setCellWidget(row_idx, 7, translator_combo)
        else:
            translator_item = self._create_table_item(translator_name)
            self.table.setItem(row_idx, 7, translator_item)

    def _setup_price_column(self, row_idx, price_value):
        """Setup price column with formatting."""
        try:
            value = float(price_value)
            formatted_value = f"{int(value):,}"
            price_item = self._create_table_item(to_persian_number(formatted_value))
            self.table.setItem(row_idx, 9, price_item)
        except (ValueError, TypeError):
            price_item = self._create_table_item("0")
            self.table.setItem(row_idx, 9, price_item)

    def _apply_column_visibility(self):
        """Apply column visibility settings."""
        for col_index, visible in enumerate(self.visible_columns):
            self.table.setColumnHidden(col_index + 1, not visible)
        self.table.setColumnHidden(0, False)  # Always show checkbox column

    def _update_translator_in_db(self, invoice_number, translator_name):
        """Update translator in database after confirmation."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("تایید مترجم")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(
            f"آیا مطمئن هستید که می‌خواهید '{translator_name}' را "
            f"به‌عنوان مترجم این فاکتور انتخاب کنید؟"
        )

        yes_button = msg_box.addButton("بله", QMessageBox.ButtonRole.YesRole)
        no_button = msg_box.addButton("خیر", QMessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            try:
                with sqlite3.connect(invoices_database) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE issued_invoices 
                        SET translator = ? 
                        WHERE invoice_number = ?
                    """, (translator_name, invoice_number))
                    conn.commit()

                # Replace combo box with text item
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, 1)
                    if item and item.text() == str(invoice_number):
                        self.table.removeCellWidget(row, 7)
                        translator_item = self._create_table_item(translator_name)
                        self.table.setItem(row, 7, translator_item)
                        break

            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در ذخیره نام مترجم: {e}")

    def _open_pdf(self, invoice_number):
        """Open PDF file for the given invoice number."""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT pdf_file_path FROM issued_invoices WHERE invoice_number = ?",
                    (invoice_number,)
                )
                result = cursor.fetchone()

                if result and result[0]:
                    pdf_path = result[0]
                    if os.path.exists(pdf_path):
                        QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
                    else:
                        self._handle_missing_file(invoice_number)
                else:
                    QMessageBox.warning(
                        self, "فایل وجود ندارد",
                        f"هیچ فایل PDF برای فاکتور شماره {invoice_number} ثبت نشده است."
                    )

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در دسترسی به اطلاعات فاکتور: {e}")

    def _handle_missing_file(self, invoice_number):
        """Handle missing PDF file."""
        recovered_path = self._recover_lost_file(invoice_number)
        if recovered_path and os.path.exists(recovered_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(recovered_path))
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("فایل پیدا نشد")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(
                f"فایل PDF فاکتور شماره {invoice_number} پیدا نشد.\n"
                "آیا می‌خواهید مسیر جدید را انتخاب کنید؟"
            )

            browse_button = msg_box.addButton("انتخاب فایل", QMessageBox.ButtonRole.ActionRole)
            cancel_button = msg_box.addButton("انصراف", QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()

            if msg_box.clickedButton() == browse_button:
                self._browse_for_pdf(invoice_number)

    def _recover_lost_file(self, invoice_number):
        """Try to recover lost PDF file by searching in common directories."""
        common_paths = [
            os.path.join(os.getcwd(), "invoices"),
            os.path.join(os.getcwd(), "pdfs"),
            os.path.join(os.getcwd(), "documents"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents")
        ]

        filename_patterns = [
            f"invoice_{invoice_number}.pdf",
            f"فاکتور_{invoice_number}.pdf",
            f"{invoice_number}.pdf"
        ]

        for path in common_paths:
            if os.path.exists(path):
                for pattern in filename_patterns:
                    found_file = find_file_by_name(pattern, path)
                    if found_file:
                        self._update_pdf_path(invoice_number, found_file)
                        return found_file

        return None

    def _browse_for_pdf(self, invoice_number):
        """Open file dialog to browse for PDF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"انتخاب فایل PDF برای فاکتور شماره {invoice_number}",
            "",
            "PDF Files (*.pdf)"
        )

        if file_path:
            self._update_pdf_path(invoice_number, file_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def _update_pdf_path(self, invoice_number, new_path):
        """Update PDF path in database."""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE issued_invoices 
                    SET pdf_file_path = ? 
                    WHERE invoice_number = ?
                """, (new_path, invoice_number))
                conn.commit()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در به‌روزرسانی مسیر فایل: {e}")

    def filter_data(self):
        """Filter table data based on search text."""
        search_text = self.search_bar.text().lower()

        for row in range(self.table.rowCount()):
            should_show = False

            # Check all text columns for matches
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break

                # Also check combo box widgets
                widget = self.table.cellWidget(row, col)
                if isinstance(widget, QComboBox):
                    if search_text in widget.currentText().lower():
                        should_show = True
                        break

            self.table.setRowHidden(row, not should_show)

        # Update selection UI after filtering
        self._update_selection_ui()

    def refresh_data(self):
        """Refresh table data from database."""
        self.load_data()
        self.search_bar.clear()

        # Reset selection
        self.select_all_checkbox.setChecked(False)
        self._update_selection_ui()

    def get_selected_invoices(self):
        """Get list of selected invoice numbers."""
        selected_invoices = []

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                invoice_number = self.table.item(row, 1).text()
                selected_invoices.append(invoice_number)

        return selected_invoices

    def export_selected_data(self):
        """Export selected invoices data to CSV file."""
        selected_invoices = self.get_selected_invoices()

        if not selected_invoices:
            QMessageBox.warning(self, "هشدار", "هیچ فاکتوری انتخاب نشده است.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره داده‌های انتخابی",
            f"selected_invoices_{len(selected_invoices)}.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            self._write_csv_export(file_path, selected_invoices)

    def _write_csv_export(self, file_path, invoice_numbers):
        """Write selected invoice data to CSV file."""
        try:
            import csv

            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                placeholders = ','.join(['?' for _ in invoice_numbers])
                cursor.execute(f"""
                    SELECT invoice_number, name, national_id, phone, issue_date, 
                           delivery_date, translator, total_amount
                    FROM issued_invoices
                    WHERE invoice_number IN ({placeholders})
                """, invoice_numbers)

                data = cursor.fetchall()

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow([
                    'شماره فاکتور', 'نام', 'کد ملی', 'شماره تماس',
                    'تاریخ صدور', 'تاریخ تحویل', 'مترجم', 'مبلغ کل'
                ])

                # Write data
                writer.writerows(data)

            QMessageBox.information(
                self, "موفق",
                f"داده‌های {len(invoice_numbers)} فاکتور با موفقیت در فایل ذخیره شد."
            )

        except Exception as e:
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره فایل: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        # Save current settings
        self.checkbox_settings.sync()
        event.accept()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            self._handle_delete_invoice()
        elif event.key() == Qt.Key_F5:
            self.refresh_data()
        elif event.key() == Qt.Key_Escape:
            self.search_bar.clear()
        else:
            super().keyPressEvent(event)

    def get_invoice_summary(self):
        """Get summary statistics of invoices."""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()

                # Total invoices
                cursor.execute("SELECT COUNT(*) FROM issued_invoices")
                total_count = cursor.fetchone()[0]

                # Total amount
                cursor.execute("SELECT SUM(total_amount) FROM issued_invoices")
                total_amount = cursor.fetchone()[0] or 0

                # Invoices by translator
                cursor.execute("""
                    SELECT translator, COUNT(*) 
                    FROM issued_invoices 
                    WHERE translator IS NOT NULL AND translator != 'نامشخص'
                    GROUP BY translator
                """)
                translator_stats = cursor.fetchall()

                return {
                    'total_count': total_count,
                    'total_amount': total_amount,
                    'translator_stats': translator_stats
                }

        except sqlite3.Error as e:
            print(f"Error getting invoice summary: {e}")
            return None

    def show_invoice_summary(self):
        """Show invoice summary dialog."""
        summary = self.get_invoice_summary()
        if not summary:
            QMessageBox.warning(self, "خطا", "خطا در دریافت اطلاعات خلاصه.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("خلاصه فاکتورها")
        dialog.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout(dialog)

        # Total statistics
        layout.addWidget(QLabel(f"تعداد کل فاکتورها: {to_persian_number(str(summary['total_count']))}"))
        layout.addWidget(QLabel(f"مجموع مبلغ: {to_persian_number(f'{int(summary['total_amount']):,}')} تومان"))

        layout.addWidget(QLabel("\nآمار مترجمان:"))

        for translator, count in summary['translator_stats']:
            layout.addWidget(QLabel(f"  {translator}: {to_persian_number(str(count))} فاکتور"))

        # Close button
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    window = InvoiceTable(parent=None)
    window.show()
    sys.exit(app.exec())
