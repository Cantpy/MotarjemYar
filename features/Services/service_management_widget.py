"""service_management_widget.py"""


import sqlite3

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton, QLineEdit,
                               QTableWidget, QDialog, QTableWidgetItem, QMenu, QHeaderView)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from modules.helper_functions import (show_question_message_box, show_error_message_box, show_warning_message_box,
                                      show_information_message_box, to_persian_number, persian_to_english_number,
                                      return_resource)
from modules.Documents.helper_functions import (InputDialog, OutputWindow, delete_all_services,
                                                import_excel_to_services, check_for_duplicates, _create_table_item)
from typing import Dict, Optional, List

documents_database = return_resource('databases', 'documents.db')


class ServicesManagerWidget(QWidget):
    """Widget for managing services with CRUD operations and search functionality."""

    COLUMN_HEADERS = ["انتخاب", "نام مدرک", "هزینه ترجمه", "نام متغیر ۱", "هزینه متغیر ۱", "نام متغیر ۲",
                      "هزینه متغیر ۲"]
    COLUMN_WIDTHS = [8, 37, 10, 12, 9, 10, 10]  # Percentage widths (adjusted for checkbox column)

    def __init__(self, parent):
        super().__init__()

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self.load_services()

    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("مدیریت اسناد")
        self.setGeometry(100, 100, 800, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _setup_ui(self):
        """Initialize and configure UI components."""
        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Search bar
        self._setup_search_bar()

        # Selection controls
        self._setup_selection_controls()

        # Table
        self._setup_table()
        self.row_to_id_mapping = {}

        # Buttons
        self._setup_buttons()

    def _setup_search_bar(self):
        """Set up the search functionality."""
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی خدمات...")
        self.search_bar.textChanged.connect(self._filter_services)
        self.main_layout.addWidget(self.search_bar)

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

        # Bulk delete button
        self.bulk_delete_btn = QPushButton("🗑️ حذف موارد انتخابی")
        self.bulk_delete_btn.setEnabled(False)
        self.bulk_delete_btn.clicked.connect(self._bulk_delete_selected)
        selection_layout.addWidget(self.bulk_delete_btn)

        self.main_layout.addLayout(selection_layout)

    def _setup_table(self):
        """Configure the services table."""
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Enable sorting for all columns except checkbox column
        for i in range(1, len(self.COLUMN_HEADERS)):
            self.table.horizontalHeader().setSortIndicatorShown(True)

        # Disable sorting for checkbox column
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

        self.main_layout.addWidget(self.table)

    def _setup_buttons(self):
        """Create and configure action buttons."""
        button_layout = QHBoxLayout()

        self.add_by_database_btn = QPushButton("افزودن با اکسل")
        self.add_btn = QPushButton("➕ اضافه کردن مدرک")
        self.edit_btn = QPushButton("✏️ ویرایش مدرک")
        self.delete_btn = QPushButton("🗑️ حذف مدرک")

        buttons = [self.add_by_database_btn, self.add_btn, self.edit_btn, self.delete_btn]
        for button in buttons:
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        self.add_btn.clicked.connect(self.add_service)
        self.edit_btn.clicked.connect(self.edit_services)
        self.delete_btn.clicked.connect(self._delete_selected_service)
        self.add_by_database_btn.clicked.connect(self._load_services_from_excel)

    def _create_checkbox_widget(self, row):
        """Create a checkbox widget for a table row."""
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(lambda state, r=row: self._on_row_checkbox_changed(r, state))

        # Center the checkbox in the cell
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        return widget, checkbox

    def _on_row_checkbox_changed(self, row, state):
        """Handle individual row checkbox state change."""
        self._update_selection_ui()

    def _toggle_select_all(self):
        """Toggle all checkboxes based on select all checkbox state."""
        is_checked = self.select_all_checkbox.isChecked()

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):  # Only affect visible rows
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    # Get the checkbox from the layout
                    layout = checkbox_widget.layout()
                    if layout and layout.count() > 0:
                        checkbox = layout.itemAt(0).widget()
                        if isinstance(checkbox, QCheckBox):
                            checkbox.blockSignals(True)  # Prevent recursive calls
                            checkbox.setChecked(is_checked)
                            checkbox.blockSignals(False)

        self._update_selection_ui()

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

    def _get_selected_count(self):
        """Get the number of selected visible rows."""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        count += 1
        return count

    def _get_visible_count(self):
        """Get the number of visible rows."""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                count += 1
        return count

    def _get_selected_rows(self):
        """Get list of selected row indices."""
        selected_rows = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_rows.append(row)
        return selected_rows

    def _bulk_delete_selected(self):
        """Delete all selected services."""
        selected_rows = self._get_selected_rows()

        if not selected_rows:
            show_warning_message_box(self, "خطا", "هیچ مدرکی انتخاب نشده است.")
            return

        # Get service names for confirmation
        service_names = []
        service_ids = []

        for row in selected_rows:
            name_item = self.table.item(row, 1)  # Name is now in column 1
            if name_item:
                service_name = name_item.text()
                service_names.append(service_name)
                service_id = self._get_service_id_from_row(row)
                if service_id:
                    service_ids.append(service_id)

        if not service_ids:
            show_warning_message_box(self, "خطا", "خطا در دریافت اطلاعات مدارک انتخابی.")
            return

        def delete_bulk():
            try:
                # Delete all selected services
                with sqlite3.connect(documents_database) as conn:
                    cursor = conn.cursor()
                    cursor.executemany("DELETE FROM Services WHERE id = ?", [(sid,) for sid in service_ids])

                self._refresh_table()

                title = "موفق"
                message = f"{len(service_ids)} مدرک با موفقیت حذف شدند!"
                show_information_message_box(self, title, message)

            except sqlite3.Error as e:
                title = "خطا"
                message = f"خطا در حذف مدارک:\n{str(e)}"
                show_error_message_box(self, title, message)

        # Show confirmation dialog
        title = "حذف گروهی"
        message = f"آیا مطمئن هستید که می‌خواهید {len(selected_rows)} مدرک انتخابی را حذف کنید؟\n\nمدارک انتخابی:\n" + "\n".join(
            f"• {name}" for name in service_names[:5])
        if len(service_names) > 5:
            message += f"\n... و {len(service_names) - 5} مورد دیگر"

        button1_text = "بله، حذف کن"
        button2_text = "خیر"
        show_question_message_box(
            parent=self,
            title=title,
            message=message,
            button_1=button1_text,
            button_2=button2_text,
            yes_func=delete_bulk
        )

    def _filter_services(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.strip().lower()
        for row in range(self.table.rowCount()):
            service_name_item = self.table.item(row, 1)  # Name is now in column 1
            if service_name_item:
                service_name = service_name_item.text().lower()
                self.table.setRowHidden(row, search_text not in service_name)

        # Update selection UI when filtering
        self._update_selection_ui()

    def _show_context_menu(self, position):
        """Display context menu for table row operations."""
        selected_row = self.table.indexAt(position).row()
        if selected_row == -1:
            return

        context_menu = QMenu(self)

        edit_action = QAction("ویرایش", self)
        edit_action.triggered.connect(self.edit_services)
        context_menu.addAction(edit_action)

        remove_action = QAction("حذف", self)
        remove_action.triggered.connect(lambda: self._delete_service_by_row(selected_row))
        context_menu.addAction(remove_action)

        # Add bulk operations to context menu if multiple rows are selected
        selected_count = self._get_selected_count()
        if selected_count > 1:
            context_menu.addSeparator()
            bulk_delete_action = QAction(f"حذف {selected_count} مورد انتخابی", self)
            bulk_delete_action.triggered.connect(self._bulk_delete_selected)
            context_menu.addAction(bulk_delete_action)

        context_menu.exec(self.table.viewport().mapToGlobal(position))

    def resizeEvent(self, event):
        """Adjust column widths dynamically on window resize."""
        super().resizeEvent(event)
        table_width = self.table.width()
        for i, percentage in enumerate(self.COLUMN_WIDTHS):
            if i == 0:  # Checkbox column - fixed width
                self.table.setColumnWidth(i, 60)
            else:
                self.table.setColumnWidth(i, table_width * percentage // 100)

    def _load_services_from_excel(self):
        """Loads services from the Excel file and then reloads the table"""
        self.output_window = OutputWindow(self)

        def run():
            try:
                delete_all_services()
                self.output_window.show()
                import_excel_to_services()
                check_for_duplicates()
                self.load_services()
            except:
                print("Unknown Error")

        title = "بارگذاری از طریق فایل اکسل"
        message = ("با بارگذاری مدارک از طریق اکسل تغییرات قبلی که در این جدول انجام داده‌اید از بین خواهد رفت.\n"
                   "آیا از انجام این کار مطمئن هستید؟\n\n"
                   "توجه: تمامی تغییرات اعمال شده در فایل اکسل با انجام این‌کار اعمال خواهند شد.")
        button1_text = "بله، مطمئنم"
        button2_text = "خیر"
        show_question_message_box(parent=self,
                                  title=title, message=message, button_1=button1_text, button_2=button2_text,
                                  yes_func=lambda: QTimer.singleShot(100, run))

    def load_services(self):
        """Load services from database and populate the table."""
        # Temporarily disable sorting while populating
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        try:
            with sqlite3.connect(documents_database) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM Services")
                services = cursor.fetchall()

                for row_number, row_data in enumerate(services):
                    self.table.insertRow(row_number)

                    # Add checkbox in first column
                    checkbox_widget, checkbox = self._create_checkbox_widget(row_number)
                    self.table.setCellWidget(row_number, 0, checkbox_widget)

                    # Add data in remaining columns (shifted by 1 due to checkbox)
                    for column_number, data in enumerate(row_data[1:]):
                        self.table.setItem(row_number, column_number + 1, _create_table_item(data))

        except sqlite3.Error as e:
            title = "خطا"
            message = f"خطا در بارکذاری مدارک:\n{str(e)}"
            show_error_message_box(self, title, message)

        finally:
            # Re-enable sorting
            self.table.setSortingEnabled(True)
            # Update selection UI
            self._update_selection_ui()

    def get_row_data(self, row: int) -> List[str]:
        """Return all cell text values in a specific row (excluding checkbox column)."""
        column_count = self.table.columnCount()
        row_data = []

        # Start from column 1 to skip checkbox column
        for col in range(1, column_count):
            item = self.table.item(row, col)
            value = item.text().strip() if item else ""
            row_data.append(value)

        return row_data

    def edit_services(self) -> Optional[Dict[str, str]]:
        """Show edit dialog with current data pre-filled."""
        row = self.table.currentRow()

        if row == -1:
            title = "خطا"
            message = "لطفا مدرکی که می‌خواهید ویرایش کنید را انتخاب کنید."
            show_warning_message_box(self, title, message)
            return None

        # Get current row data
        row_data = self.get_row_data(row)

        # Create dialog
        dialog = InputDialog("ServicesManagerWidget", self)
        dialog.setWindowTitle("ویرایش مدرک")

        # Pre-fill the dialog fields with current data
        # Map table columns to dialog field keys (adjusted for checkbox column)
        field_mapping = {
            0: "document_name",  # نام مدرک (column 1 in table)
            1: "base_cost",  # هزینه ترجمه (column 2 in table)
            2: "variable_name_1",  # نام متغیر ۱ (column 3 in table)
            3: "variable_cost_1",  # هزینه متغیر ۱ (column 4 in table)
            4: "variable_name_2",  # نام متغیر ۲ (column 5 in table)
            5: "variable_cost_2"  # هزینه متغیر ۲ (column 6 in table)
        }

        # Fill the dialog inputs with current row data
        for col_index, field_key in field_mapping.items():
            if col_index < len(row_data) and field_key in dialog.inputs:
                dialog.inputs[field_key].setText(str(row_data[col_index]))

        # Show dialog and handle result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            # Extract values
            name = values.get("document_name", "")
            base_price = values.get("base_cost", "")
            dynamic_price_name_1 = values.get("variable_name_1", "")
            dynamic_price_1 = values.get("variable_cost_1", "")
            dynamic_price_name_2 = values.get("variable_name_2", "")
            dynamic_price_2 = values.get("variable_cost_2", "")

            # Validate required fields
            if not name or not base_price:
                title = "خطا"
                message = "نام مدرک و هزینه پایه الزامی هستند."
                show_warning_message_box(self, title, message)
                return None

            # Get service ID for update
            service_id = self._get_service_id_from_row(row)
            if service_id is None:
                return None

            try:
                # Update service in database
                self._update_service_in_db(
                    service_id,
                    name,
                    base_price,
                    dynamic_price_name_1 if dynamic_price_1 else "",
                    int(dynamic_price_1) if dynamic_price_1 else 0,
                    dynamic_price_name_2 if dynamic_price_2 else "",
                    int(dynamic_price_2) if dynamic_price_2 else 0
                )

                # Refresh table
                self.load_services()

                # Show success message
                title = "موفق"
                message = f"مدرک '{name}' با موفقیت ویرایش شد!"
                show_information_message_box(self, title, message)

                return values

            except sqlite3.Error as e:
                title = "خطا"
                message = f"خطا در ویرایش مدرک:\n{str(e)}"
                show_error_message_box(self, title, message)
                return None

        return None

    def add_service(self):
        """Add a new service through dialog input."""
        service_data = self._get_add_service_details()

        # Check if dialog was cancelled
        if service_data is None or service_data[0] is None:
            return

        name, base_price, dynamic_price_name_1, dynamic_price_1, dynamic_price_name_2, dynamic_price_2 = service_data

        # Validate required fields
        if not name or not name.strip():
            show_warning_message_box(self, "خطا", "نام سرویس الزامی است!")
            return

        if not base_price or not str(base_price).strip():
            show_warning_message_box(self, "خطا", "قیمت پایه الزامی است!")
            return

        # Convert base_price to appropriate type if needed
        try:
            base_price = float(base_price) if base_price else 0
        except ValueError:
            show_warning_message_box(self, "خطا", "قیمت پایه باید عدد باشد!")
            return

        if self._service_exists(name):
            title = "خطا"
            message = f"مدرک '{name}' قبلاً اضافه شده است!"
            show_warning_message_box(self, title, message)
            return

        try:
            self._save_service_to_db(name, base_price, dynamic_price_name_1, dynamic_price_1,
                                     dynamic_price_name_2, dynamic_price_2)
            self._refresh_table()
            title = "موفق"
            message = f"مدرک '{name}' با موفقیت اضافه شد!"
            show_information_message_box(self, title, message)
        except sqlite3.Error as e:
            title = "خطا"
            message = (f"خطا در افزودن مدرک:\n"
                       f" {str(e)}")
            show_error_message_box(self, title, message)

    def _delete_selected_service(self):
        """Delete the currently selected service."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            self._delete_service_by_row(selected_row)

    def _delete_service_by_row(self, row):
        """Delete a service by table row index."""
        if row == -1:
            title = "خطا"
            message = "لطفا مدرکی که می‌خواهید حذف کنید را انتخاب کنید"
            show_warning_message_box(self, title, message)
            return

        document_name_item = self.table.item(row, 1)  # Name is now in column 1
        if not document_name_item:
            title = "خطا"
            message = "ردیف انتخاب شده نامعتبر است"
            show_warning_message_box(self, title, message)
            return

        document_name = document_name_item.text()
        service_id = self._get_service_id_from_row(row)

        if service_id is None:
            return

        # Confirm deletion
        def delete():
            try:
                self._delete_service_from_db(service_id)
                self._refresh_table()
                title = "موفق"
                message = f"مدرک {document_name} با موفقیت حذف شد!"
                show_information_message_box(self, title, message)
            except sqlite3.Error as e:
                title = "خطا"
                message = ("خطا در حذف مدرک از پایگاه داده:\n"
                           f"{str(e)}")
                show_error_message_box(self, title, message)

        title = "حذف"
        message = (f"آیا مطمئن هستید که می‌خواهید '{document_name}' را حذف کنید؟")
        button1_text = "بله"
        button2_text = "خیر"
        show_question_message_box(parent=self,
                                  title=title, message=message, button_1=button1_text, button_2=button2_text,
                                  yes_func=delete)

    def _service_exists(self, name):
        """Check if a service with the given name already exists."""
        with sqlite3.connect(documents_database) as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM Services WHERE name = ?", (name,))
                result = cursor.fetchone()
                return result and result[0] > 0
            except sqlite3.Error:
                title = "خطا"
                message = "این مدرک در پایگاه داده وجود ندارد!"
                show_error_message_box(self, title, message)

    def _get_service_id_from_row(self, row):
        """Get service ID from database based on service name in the row."""
        name_item = self.table.item(row, 1)  # Name is now in column 1
        if not name_item:
            return None

        service_name = name_item.text()
        try:
            with sqlite3.connect(documents_database) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT id FROM Services WHERE name = ?", (service_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error:
            title = "خطا"
            message = "این مدرک در پایگاه داده وجود ندارد!"
            show_error_message_box(self, title, message)
            return None

    def _get_add_service_details(self):
        """Get service details from add dialog."""
        dialog = InputDialog("ServicesManagerWidget", self)
        dialog.setWindowTitle("افزودن سایر خدمات جدید")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()

            # Use the correct keys that match your InputDialog
            name = values.get("document_name", "")  # ← Changed from "name"
            base_price = values.get("base_cost", "")  # ← Changed from "base_price"
            dynamic_price_name_1 = values.get("variable_name_1", "")  # ← Changed
            dynamic_price_1 = values.get("variable_cost_1", "")  # ← Changed
            dynamic_price_name_2 = values.get("variable_name_2", "")  # ← Changed
            dynamic_price_2 = values.get("variable_cost_2", "")  # ← Changed

            # Always return the tuple, even if some values are empty
            return (
                name,
                base_price,
                dynamic_price_name_1 if dynamic_price_1 else "",
                int(dynamic_price_1) if dynamic_price_1 else 0,
                dynamic_price_name_2 if dynamic_price_2 else "",
                int(dynamic_price_2) if dynamic_price_2 else 0,
            )

        # Only return None values when dialog is cancelled
        return None, None, None, None, None, None

    def _save_service_to_db(self, name, base_price, dynamic_price_name_1="", dynamic_price_1=0,
                            dynamic_price_name_2="", dynamic_price_2=0):
        """Save a new service to the database."""
        with sqlite3.connect(documents_database) as conn:
            cursor = conn.cursor()
            try:
                query = """
                    INSERT INTO Services (name,
                    base_price,
                    dynamic_price_name_1,
                    dynamic_price_1,
                    dynamic_price_name_2,
                    dynamic_price_2)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (name, base_price, dynamic_price_name_1,
                                       dynamic_price_1, dynamic_price_name_2, dynamic_price_2))
            except sqlite3.Error as e:
                title = "خطا"
                message = ("خطای پایگاه داده:\n"
                           f"{str(e)}")
                show_error_message_box(self, title, message)

    def _update_service_in_db(self, service_id, name, base_price, dynamic_price_name_1,
                              dynamic_price_1, dynamic_price_name_2, dynamic_price_2):
        """Update an existing service in the database."""
        with sqlite3.connect(documents_database) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE Services
                    SET name = ?, base_price = ?, dynamic_price_name_1 = ?, dynamic_price_1 = ?,
                    dynamic_price_name_2 = ?, dynamic_price_2 = ?
                    WHERE id = ?
                """, (name, base_price, dynamic_price_name_1, dynamic_price_1,
                      dynamic_price_name_2, dynamic_price_2, service_id))
            except sqlite3.Error as e:
                title = "خطا"
                message = ("خطای در ویرایش خدمت:\n"
                           f"{str(e)}")
                show_error_message_box(self, title, message)

    def _delete_service_from_db(self, service_id):
        """Delete a service from the database."""
        with sqlite3.connect(documents_database) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM Services WHERE id = ?", (service_id,))
            except sqlite3.Error as e:
                title = "خطا"
                message = ("خطای در حذف خدمت از پایگاه داده:\n"
                           f"{str(e)}")
                show_error_message_box(self, title, message)

    def _refresh_table(self):
        """Refresh the table by reloading data from database."""
        self.load_services()
