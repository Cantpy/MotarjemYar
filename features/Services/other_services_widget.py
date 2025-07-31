"""other_services.py"""

import sqlite3

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton, QLineEdit,
                               QTableWidget, QDialog, QTableWidgetItem, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from modules.helper_functions import (show_question_message_box, show_error_message_box, show_warning_message_box,
                                      show_information_message_box, to_persian_number, persian_to_english_number,
                                      return_resource)
from modules.Documents.helper_functions import InputDialog
from typing import Dict, Optional, List


documents_database = return_resource('databases', 'documents.db')


class OtherServicesWidget(QWidget):
    """Widget for managing other services with CRUD operations and search functionality."""

    COLUMN_HEADERS = ["انتخاب", "خدمات", "هزینه"]
    COLUMN_WIDTHS = [15, 55, 30]  # Percentage widths

    def __init__(self):
        super().__init__()
        # Store ID mapping: row_index -> database_id
        self.row_to_id_mapping = {}

        self._setup_ui()
        self._connect_signals()
        self.load_other_services()

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

        # Buttons
        self._setup_buttons()

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

    def _create_checkbox_widget(self):
        """Create a checkbox widget for table cells."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(checkbox)

        return widget

    def _on_checkbox_changed(self):
        """Handle individual checkbox state change."""
        self._update_selection_ui()

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

    def _get_selected_count(self):
        """Get count of selected rows."""
        return len(self._get_selected_rows())

    def _get_visible_count(self):
        """Get count of visible rows."""
        visible_count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                visible_count += 1
        return visible_count

    def _bulk_delete_selected(self):
        """Delete all selected services."""
        selected_rows = self._get_selected_rows()

        if not selected_rows:
            show_warning_message_box(self, "خطا", "هیچ مورد انتخاب نشده است.")
            return

        # Get service names for confirmation
        service_names = []
        service_ids = []

        for row in selected_rows:
            name_item = self.table.item(row, 1)  # Name is in column 1
            if name_item:
                service_name = name_item.text()
                service_names.append(service_name)
                service_id = self._get_service_id_from_row(row)
                if service_id:
                    service_ids.append(service_id)

        if not service_ids:
            show_warning_message_box(self, "خطا", "خطا در دریافت اطلاعات موارد انتخابی.")
            return

        def bulk_delete_selected():
            try:
                with sqlite3.connect(documents_database) as conn:
                    cursor = conn.cursor()
                    # Delete non-default items only
                    placeholders = ','.join(['?'] * len(service_ids))
                    cursor.execute(f"DELETE FROM other_services WHERE id IN ({placeholders}) AND is_default = 0",
                                   service_ids)

                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        self.load_other_services()  # Reload table
                        title = "موفق"
                        message = f"{deleted_count} مورد با موفقیت حذف شد!"
                        show_information_message_box(self, title, message)
                    else:
                        title = "خطا"
                        message = "هیچ موردی حذف نشد. ممکن است موارد انتخابی از نوع پیش‌فرض باشند."
                        show_warning_message_box(self, title, message)

            except sqlite3.Error as e:
                title = "خطای پایگاه داده"
                message = f"خطا در حذف موارد:\n{str(e)}"
                show_error_message_box(self, title, message)

            finally:
                self.load_other_services()

        # Show confirmation dialog
        services_text = "\n".join(service_names)
        title = "حذف چندگانه"
        message = f"آیا مطمئن هستید که می‌خواهید موارد زیر را حذف کنید؟\n\n{services_text}"
        button1 = "بله، مطمئنم"
        button2 = "خیر"
        show_question_message_box(self, title, message, button1, bulk_delete_selected, button2)

    def _get_service_id_from_row(self, row):
        """Get service ID from row using the mapping."""
        return self.row_to_id_mapping.get(row)

    def _toggle_select_all(self):
        """Toggle all checkboxes based on select all checkbox state."""
        is_checked = self.select_all_checkbox.isChecked()

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):  # Only affect visible rows
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
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

    def _setup_search_bar(self):
        """Set up the search functionality."""
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجوی سایر خدمات...")
        self.search_bar.textChanged.connect(self._filter_costs)
        self.main_layout.addWidget(self.search_bar)

    def _setup_table(self):
        """Configure the fixed costs table."""
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Make the checkbox column non-sortable
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().setSectionsClickable(True)

        self.main_layout.addWidget(self.table)

    def _setup_buttons(self):
        """Create and configure action buttons."""
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ اضافه کردن خدمت")
        self.edit_btn = QPushButton("✏️ ویرایش خدمت")
        self.delete_btn = QPushButton("🗑️ حذف خدمت")

        buttons = [self.add_btn, self.edit_btn, self.delete_btn]
        for button in buttons:
            button_layout.addWidget(button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        self.add_btn.clicked.connect(self._show_add_other_services_dialog)
        self.edit_btn.clicked.connect(self._show_edit_other_services_dialog)
        self.delete_btn.clicked.connect(self.delete_other_service)

    def _filter_costs(self, search_text):
        """Filter table rows based on search text."""
        search_text = search_text.strip().lower()
        for row in range(self.table.rowCount()):
            cost_name_item = self.table.item(row, 1)  # Name is now in column 1
            if cost_name_item:
                cost_name = cost_name_item.text().lower()
                self.table.setRowHidden(row, search_text not in cost_name)

        # Update selection UI when filtering
        self._update_selection_ui()

    def _show_context_menu(self, position):
        """Display context menu for table row operations."""
        selected_row = self.table.indexAt(position).row()
        if selected_row == -1:
            return

        context_menu = QMenu(self)

        edit_action = QAction("ویرایش", self)
        edit_action.triggered.connect(self._show_edit_other_services_dialog)
        context_menu.addAction(edit_action)

        remove_action = QAction("حذف", self)
        remove_action.triggered.connect(self._delete_selected_services)
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
        if hasattr(self, 'table'):
            table_width = self.table.width()
            for i, percentage in enumerate(self.COLUMN_WIDTHS):
                self.table.setColumnWidth(i, table_width * percentage // 100)

    def load_other_services(self):
        """Load fixed costs from database and populate the table."""
        # Disable sorting temporarily to avoid issues during population
        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)
        self.row_to_id_mapping.clear()  # Clear the mapping

        try:
            with sqlite3.connect(documents_database) as connection:
                cursor = connection.cursor()
                # Modified to also fetch the id
                cursor.execute("SELECT id, name, price FROM other_services ORDER BY name")
                costs = cursor.fetchall()

                for row_number, (cost_id, name, price) in enumerate(costs):
                    self.table.insertRow(row_number)

                    # Store the ID mapping
                    self.row_to_id_mapping[row_number] = cost_id

                    # Add checkbox in first column
                    checkbox_widget = self._create_checkbox_widget()
                    self.table.setCellWidget(row_number, 0, checkbox_widget)

                    # Add name and price items
                    name_item = QTableWidgetItem(str(name))
                    price_item = QTableWidgetItem(str(price))

                    # Set data for proper sorting
                    price_item.setData(Qt.ItemDataRole.UserRole, price)  # Store numeric value for sorting

                    self.table.setItem(row_number, 1, name_item)
                    self.table.setItem(row_number, 2, price_item)

        except sqlite3.Error as e:
            title = "خطای پایگاده داده"
            message = ("خطا در بارگذاری سایر خدمات.\n"
                       f"{str(e)}")
            show_warning_message_box(self, title, message)

        finally:
            # Re-enable sorting
            self.table.setSortingEnabled(True)
            # Update selection UI
            self._update_selection_ui()

    def _get_cost_id_by_row(self, row):
        """Get the database ID for a given table row."""
        return self.row_to_id_mapping.get(row)

    def _show_add_other_services_dialog(self) -> Optional[Dict[str, str]]:
        dialog = InputDialog("OtherServicesWidget", self)
        dialog.setWindowTitle("افزودن سایر خدمات جدید")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_values()
            self.add_other_services(data)
        return None

    def _show_edit_other_services_dialog(self) -> Optional[Dict[str, str]]:
        dialog = InputDialog("OtherServicesWidget", self)
        dialog.setWindowTitle("ویرایش سایر خدمات")
        row = self.table.currentRow()
        service_id = self._get_service_id_from_row(row)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_values()
            self.edit_other_services(service_id, data)
        return None

    def add_other_services(self, service_data: Dict[str, str]) -> bool:
        """
            Add a new service to the other_services table.

            Args:
                service_data (Dict[str, str]): Dictionary with 'service_name' and 'cost' keys

            Returns:
                bool: True if successful, False otherwise
            """
        try:
            with sqlite3.connect(documents_database) as conn:
                cursor = conn.cursor()

                # Extract data from dictionary
                name = service_data.get('service_name', '').strip()
                cost = service_data.get('cost', '0')

                # Validate input
                if not name:
                    title = "خطا"
                    message = "نام خدمت نمی‌تواند خالی باشد"
                    show_warning_message_box(self, title, message)
                    return False

                # Convert cost to integer
                try:
                    price = int(cost)
                except ValueError:
                    title = "خطا"
                    message = (f"قیمت وارد شده {cost} نامعتبر است.\n"
                               f"لطفا هزینه را به صورت رقمی و بدون کاما وارد کنید."
                               f"\nهنگام وارد کردن هزینه مطمئن شوید از کیبورد انگلیسی یا فارسی FA استفاده می‌کنید (نه FAS).")
                    show_warning_message_box(self, title, message)
                    return False

                # Insert into database
                cursor.execute("""
                        INSERT INTO other_services (name, price) 
                        VALUES (?, ?)
                    """, (name, price))

                formatted_price = f"{price:,}"
                persian_price = f"{to_persian_number(formatted_price)}"
                title = "موفق"
                message = (f"اطلاعات زیر با موفقیت به پایگاه داده اضافه شد:\n"
                           f"نام خدمت: {name}\n"
                           f"هزینه خدمت: {persian_price} تومان")
                show_information_message_box(self, title, message)
                return True

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                title = "خطا"
                message = f"خدمتی با نام '{name}' قبلا در پایگاه داده ثبت شده است."
                show_warning_message_box(self, title, message)
            else:
                title = "خطا"
                message = f"{e}"
                show_error_message_box(self, title, message)
            return False

        except sqlite3.Error as e:
            title = "خطا"
            message = (f"خطا در افزودن خدمت به پایگاه داده:\n"
                       f"{e}")
            show_error_message_box(self, title, message)
            return False
        finally:
            self.load_other_services()

    def edit_other_services(self, service_id: int, service_data: Dict[str, str]) -> bool:
        """
            Edit an existing service in the other_services table.

            Args:
                service_id (int): ID of the service to update
                service_data (Dict[str, str]): Dictionary with 'service_name' and 'cost' keys

            Returns:
                bool: True if successful, False otherwise
            """
        try:
            with sqlite3.connect(documents_database) as conn:
                cursor = conn.cursor()

                # Extract data from dictionary
                name = service_data.get('service_name', '').strip()
                cost = service_data.get('cost', '0')

                # Validate input
                if not name:
                    title = "خطا"
                    message = "نام خدمت نمی‌تواند خالی باشد"
                    show_warning_message_box(self, title, message)
                    return False

                # Convert cost to integer
                try:
                    price = int(cost)
                except ValueError:
                    title = "خطا"
                    message = (f"قیمت وارد شده {cost} نامعتبر است.\n"
                               f"لطفا هزینه را به صورت رقمی و بدون کاما وارد کنید."
                               f"\nهنگام وارد کردن هزینه مطمئن شوید از کیبورد انگلیسی یا فارسی FA استفاده می‌کنید (نه FAS).")
                    show_warning_message_box(self, title, message)
                    return False

                # Check if service exists
                cursor.execute("SELECT id FROM other_services WHERE id = ?", (service_id,))
                if not cursor.fetchone():
                    title = "خطا"
                    message = (f"این سرویس در پایگاه داده پیدا نشد.\n"
                               f"شناسه در پایگاه داده: {service_id}")
                    show_error_message_box(self, title, message)
                    return False

                # Update the service
                cursor.execute("""
                        UPDATE other_services 
                        SET name = ?, price = ? 
                        WHERE id = ?
                    """, (name, price, service_id))

                if cursor.rowcount > 0:
                    formatted_price = f"{price:,}"
                    persian_price = f"{to_persian_number(formatted_price)}"
                    title = "موفق"
                    message = (f"خدمت شما با شناسه {service_id} در پایگاه داده بروزرسانی شد.\n"
                               f"نام جدید خدمت: {name}، هزینه جدید خدمت: {persian_price}")
                    show_information_message_box(self, title, message)
                    return True
                else:
                    return False  # User cancelled

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                title = "خطا"
                message = f"خدمتی با نام '{name}' قبلا در پایگاه داده ثبت شده است."
                show_warning_message_box(self, title, message)
            else:
                title = "خطا"
                message = f"{e}"
                show_error_message_box(self, title, message)
            return False
        except sqlite3.Error as e:
            title = "خطا"
            message = (f"خطا در افزودن خدمت به پایگاه داده:\n"
                       f"{e}")
            show_error_message_box(self, title, message)
            return False
        finally:
            self.load_other_services()

    def _delete_selected_services(self):
        """Delete the currently selected fixed cost."""
        selected_row = self.table.currentRow()
        if selected_row != -1:
            self._delete_services_by_row(selected_row)

    def _delete_services_by_row(self, row):
        """Deletes a service by table row index."""
        if row == -1:
            title = "خطا"
            message = "لطفا هزینه ثابتی که می‌خواهید حذف کنید را انتخاب کنید"
            show_warning_message_box(self, title, message)
            return

        # Check if it's a default cost
        if self._is_default_cost(row):
            title = "خطا"
            message = "نمی‌توانید هزینه‌های ثابت پیش‌فرض را حذف کنید!"
            show_warning_message_box(self, title, message)
            return

        cost_id = self._get_cost_id_by_row(row)
        if cost_id is None:
            title = "خطا"
            message = "شناسه هزینه ثابت پیدا نشد"
            show_error_message_box(self, title, message)
            return

        name_item = self.table.item(row, 1)  # Name is now in column 1
        if not name_item:
            title = "خطا"
            message = "ردیف انتخاب شده نامعتبر است"
            show_warning_message_box(self, title, message)
            return

        cost_name = name_item.text()

        def delete_other_service():
            try:
                with sqlite3.connect(documents_database) as conn:
                    cursor = conn.cursor()
                    # Use ID instead of name for deletion
                    cursor.execute("DELETE FROM other_services WHERE id = ? AND is_default = 0", (cost_id,))

                    if cursor.rowcount > 0:
                        self.load_other_services()  # Reload to update the table and ID mapping
                        title = "موفق"
                        message = f"هزینه ثابت '{cost_name}' با موفقیت حذف شد!"
                        show_information_message_box(self, title, message)
                    else:
                        title = "خطا"
                        message = "هزینه ثابت حذف نشد. ممکن است هزینه پیش‌فرض باشد."
                        show_warning_message_box(self, title, message)

            except sqlite3.Error as e:
                title = "خطای پایگاه داده"
                message = ("خطا در حذف هزینه ثابت:\n"
                           f" {str(e)}")
                show_error_message_box(self, title, message)
            finally:
                self.load_other_services()

        # Confirm deletion
        title = "حذف"
        message = f"آیا مطمئن هستید که می‌خواهید '{cost_name}' را حذف کنید؟"
        button1 = "بله، مطمئنم"
        button2 = "خیر"
        show_question_message_box(self, title, message, button1, delete_other_service, button2)

    def _is_default_cost(self, row):
        """Check if the cost at given row is a default cost."""
        name_item = self.table.item(row, 1)  # Name is now in column 1
        if not name_item:
            return False

    def delete_other_service(self, service_id: int) -> bool:
        """
            Delete a service from the other_services table.

            Args:
                service_id (int): ID of the service to delete

            Returns:
                bool: True if successful, False otherwise
            """
        try:
            with sqlite3.connect(documents_database) as conn:
                cursor = conn.cursor()

                # Check if service exists and get its name for confirmation
                cursor.execute("SELECT name FROM other_services WHERE id = ?", (service_id,))
                result = cursor.fetchone()

                if not result:
                    title = "خطا"
                    message = "این خدمت در پایگاه داده وجود ندارد"
                    show_error_message_box(self, title, message)
                    return False

                service_name = result[0]

                # Delete the service
                cursor.execute("DELETE FROM other_services WHERE id = ?", (service_id,))

                if cursor.rowcount > 0:
                    title = "موفق"
                    message = f"خدمت '{service_name}' با موفقیت حذف شد"
                    show_information_message_box(self, title, message)
                    return True
                else:
                    title = "خطا"
                    message = ("خطا در حذف خدمت.\n"
                               f"شناسه خدمت در پایگاه داده: {service_id}")
                    show_error_message_box(self, title, message)
                    return False

        except sqlite3.Error as e:
            title = "خطا"
            message = ("خطا در حذف خدمت:\n"
                       f"{e}")
            show_error_message_box(self, title, message)
            return False
