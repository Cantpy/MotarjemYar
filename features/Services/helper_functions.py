"""helper_functions.py"""

import sqlite3
import os
import sys
import pandas as pd
from modules.helper_functions import return_resource, show_error_message_box
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QTableWidgetItem, QWidget, QVBoxLayout, QTextEdit, QPushButton, QDialog, QFormLayout,
                               QHBoxLayout, QLabel, QLineEdit)
from io import StringIO
from modules.helper_functions import to_persian_number
from typing import Dict


DB_PATH = return_resource('databases', 'documents.db')
EXCEL_FILE_PATH = return_resource('databases', 'services_data.xlsx')


class InputDialog(QDialog):
    def __init__(self, widget_type: str, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.inputs = {}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("اضافه کردن آیتم جدید")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main layout
        layout = QVBoxLayout()

        # Form layout for inputs
        form_layout = QFormLayout()

        # Define fields based on widget type
        if self.widget_type == "ServicesManagerWidget":
            fields = [
                ("نام مدرک", "document_name"),
                ("هزینه پایه", "base_cost"),
                ("نوع هزینه متغیر ۱", "variable_name_1"),
                ("هزینه متغیر ۱", "variable_cost_1"),
                ("نوع هزینه متغیر ۲", "variable_name_2"),
                ("هزینه متغیر ۲", "variable_cost_2")
            ]
        elif self.widget_type in ["FixedCostsWidget", "OtherServicesWidget"]:
            fields = [
                ("نام خدمت", "service_name"),
                ("هزینه", "cost")
            ]
        else:
            raise ValueError(f"Unknown widget type: {self.widget_type}")

        # Create input fields
        for label_text, field_key in fields:
            label = QLabel(label_text)
            line_edit = QLineEdit()

            # Set input mask for cost fields (numbers only)
            if "هزینه" in label_text or "cost" in field_key:
                line_edit.setPlaceholderText("مثال: 10000")

            if "نوع" in label_text:
                line_edit.setPlaceholderText("مثال: تعداد درس/ تعداد سطر توضیحات")

            self.inputs[field_key] = line_edit
            form_layout.addRow(label, line_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("تایید")
        self.cancel_button = QPushButton("انصراف")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Set focus to first input
        if self.inputs:
            first_input = list(self.inputs.values())[0]
            first_input.setFocus()

    def get_values(self) -> Dict[str, str]:
        """Return the values from all input fields"""
        return {key: widget.text().strip() for key, widget in self.inputs.items()}


def create_backup_database(database):
    """Create a backup of the invoices database."""
    import shutil
    from datetime import datetime

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"invoices_backup_{timestamp}.db"
        backup_path = os.path.join(os.path.dirname(database), backup_name)

        shutil.copy2(database, backup_path)
        return backup_path

    except Exception as e:
        print(f"Error creating backup: {e}")
        return None


class OutputWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle("Console Output")
        self.resize(700, 500)

        self.layout = QVBoxLayout(self)
        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

        self.output_buffer = StringIO()
        sys.stdout = self.output_buffer  # Redirect stdout

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_output)
        self.timer.start(200)

    def update_output(self):
        self.output_text.setPlainText(self.output_buffer.getvalue())
        self.output_text.moveCursor(QTextCursor.End)

    def closeEvent(self, event):
        sys.stdout = sys.__stdout__  # Restore stdout
        event.accept()


def delete_all_services() -> bool:
    """Delete all rows from the Services table in the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Services")
            conn.commit()
            print("✅ همه‌ی رکوردهای جدول Services حذف شدند.")
            return True
    except sqlite3.Error as e:
        print(f"❌ خطا در حذف رکوردها از جدول Services:\n{str(e)}")
        return False


def import_excel_to_services():
    """Import data from Excel file to Services table."""
    try:
        if not os.path.exists(EXCEL_FILE_PATH):
            print(f"در مسیر زیر فایل اکسلی وجود ندارد:\n{EXCEL_FILE_PATH}")
            return False

        print(f"در حال خواندن فایل اکسل در مسیر: {EXCEL_FILE_PATH}")
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Sheet1')

        expected_columns = ['name', 'base_price', 'dynamic_price_name_1', 'dynamic_price_1',
                            'dynamic_price_name_2', 'dynamic_price_2']

        # Validate and rename
        if len(df.columns) >= 6:
            df = df.iloc[:, :6].copy()
            df.columns = expected_columns
        else:
            print("تعداد ستون‌های فایل اکسل کمتر از ۶ تاست!")
            return False

        df = df.dropna(subset=['name'])

        # Convert prices to int safely
        for col in ['base_price', 'dynamic_price_1', 'dynamic_price_2']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Nullify dynamic_price_name_* if price is 0
        df.loc[df['dynamic_price_1'] == 0, 'dynamic_price_name_1'] = None
        df.loc[df['dynamic_price_2'] == 0, 'dynamic_price_name_2'] = None

        print(f"تعداد {to_persian_number(len(df))} مدرک برای افزودن پیدا شد")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM Services")
            existing_names = {row[0] for row in cursor.fetchall()}

            df_unique = df.drop_duplicates(subset=['name'], keep='first')
            df_new = df_unique[~df_unique['name'].isin(existing_names)]

            duplicates_in_excel = len(df) - len(df_unique)
            duplicates_in_db = len(df_unique) - len(df_new)

            if duplicates_in_excel > 0:
                print(f"{to_persian_number(duplicates_in_excel)} مدرک تکراری در فایل اکسل یافت شد.")
            if duplicates_in_db > 0:
                print(f"{to_persian_number(duplicates_in_db)} مدرک تکراری در پایگاه داده یافت شد.")

            print(f"تعداد {to_persian_number(len(df_new))} مدرک جدید پیدا شد")

            if len(df_new) == 0:
                print("مدرک جدیدی برای افزودن وجود ندارد.")
                return True

            insert_query = """
            INSERT OR IGNORE INTO Services 
            (name, base_price, dynamic_price_name_1, dynamic_price_1, dynamic_price_name_2, dynamic_price_2)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            records_inserted = 0
            records_skipped = 0

            for _, row in df_new.iterrows():
                try:
                    cursor.execute(insert_query, (
                        str(row['name']),
                        int(row['base_price']),
                        row['dynamic_price_name_1'],
                        int(row['dynamic_price_1']),
                        row['dynamic_price_name_2'],
                        int(row['dynamic_price_2']),
                    ))
                    if cursor.rowcount > 0:
                        records_inserted += 1
                    else:
                        records_skipped += 1
                except sqlite3.Error as e:
                    print(f"خطا در افزودن مدرک {row['name']}: {str(e)}")
                    records_skipped += 1

            conn.commit()
            print(f"تعداد {to_persian_number(records_inserted)} مدرک با موفقیت افزوده شد.")
            if records_skipped > 0:
                print(f"{to_persian_number(records_skipped)} مدرک نادیده گرفته شد (تکراری یا مشکل‌دار).")

            cursor.execute("SELECT COUNT(*) FROM Services")
            total_count = cursor.fetchone()[0]
            print(f"تعداد کل مدارک در پایگاه داده: {to_persian_number(total_count)}")

        return True

    except Exception as e:
        print(f"خطا در بارگذاری مدارک از طریق فایل اکسل:\n{str(e)}")
        return False


def check_for_duplicates():
    """Check for duplicate service names in the database and remove duplicates (keeping first occurrence)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check for any duplicate names
            cursor.execute("""
                SELECT name, COUNT(*) as count 
                FROM Services 
                GROUP BY name 
                HAVING COUNT(*) > 1
            """)

            duplicates = cursor.fetchall()
            if duplicates:
                print(f"تعداد {to_persian_number(len(duplicates))} مدرک تکراری با نام‌های زیر پیدا شد:")
                for name, count in duplicates:
                    print(f"  - '{name}' {to_persian_number(count)} بار تکرار شده")

                # Remove duplicates, keeping only the first occurrence (lowest ID)
                total_removed = 0
                for name, count in duplicates:
                    # Delete all but the first occurrence (keep the one with minimum ID)
                    cursor.execute("""
                        DELETE FROM Services 
                        WHERE name = ? AND id NOT IN (
                            SELECT MIN(id) FROM Services WHERE name = ?
                        )
                    """, (name, name))

                    removed_count = cursor.rowcount
                    total_removed += removed_count
                    print(f"  - حذف شد {to_persian_number(removed_count)} مدرک تکراری با نام '{name}'")

                conn.commit()
                print(f"تعداد مدارک تکراری حذف شده: {to_persian_number(total_removed)}")

                # Verify cleanup
                cursor.execute("SELECT COUNT(*) FROM Services")
                final_count = cursor.fetchone()[0]
                print(f"پایگاه داده اکنون {to_persian_number(final_count)} مدرک دارد!")

            else:
                print("هیچ مدرک تکراری در پایگاه داده پیدا نشد!")

    except sqlite3.Error as e:
        print(f"خطا در پیدا کردن مدارک تکراری: {str(e)}")


def load_services_into_table(table_name: str, table_widget, widget_name: str) -> bool:
    """
    Load services from database table into QTableWidget based on widget type.

    Args:
        table_name (str): Database table name (e.g., 'Services', 'other_services', 'fixed_costs')
        table_widget (QTableWidget): The table widget to populate
        widget_name (str): Widget name to determine column structure

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            if widget_name in ["OtherServicesWidget", "FixedCostsWidget"]:
                cursor.execute(f"SELECT id, name, price FROM {table_name} ORDER BY name")
                column_count = 2
                headers = ["نام خدمت", "قیمت"]

            elif widget_name == "ServicesManagerWidget":
                cursor.execute(f"""
                    SELECT id, name, base_price, dynamic_price_name_1, dynamic_price_1, 
                           dynamic_price_name_2, dynamic_price_2 
                    FROM {table_name} ORDER BY name
                """)
                column_count = 6
                headers = [
                    "نام مدرک", "قیمت پایه",
                    "عنوان متغیر ۱", "قیمت متغیر ۱",
                    "عنوان متغیر ۲", "قیمت متغیر ۲"
                ]
            else:
                print(f"Unknown widget type: {widget_name}")
                return False

            results = cursor.fetchall()

            table_widget.setRowCount(len(results))
            table_widget.setColumnCount(column_count)
            table_widget.setHorizontalHeaderLabels(headers)

            for row_idx, row_data in enumerate(results):
                service_id = row_data[0]

                if widget_name in ["OtherServicesWidget", "FixedCostsWidget"]:
                    # name
                    name_item = QTableWidgetItem(str(row_data[1]))
                    name_item.setData(Qt.ItemDataRole.UserRole, service_id)
                    table_widget.setItem(row_idx, 0, name_item)

                    # price
                    price_item = QTableWidgetItem(str(row_data[2]))
                    table_widget.setItem(row_idx, 1, price_item)

                elif widget_name == "ServicesManagerWidget":
                    name_item = QTableWidgetItem(str(row_data[1]))
                    name_item.setData(Qt.ItemDataRole.UserRole, service_id)
                    table_widget.setItem(row_idx, 0, name_item)

                    base_price_item = QTableWidgetItem(str(row_data[2]))
                    table_widget.setItem(row_idx, 1, base_price_item)

                    dynamic_name_1_item = QTableWidgetItem(row_data[3] or "")
                    table_widget.setItem(row_idx, 2, dynamic_name_1_item)

                    dynamic_price_1_item = QTableWidgetItem(str(row_data[4]))
                    table_widget.setItem(row_idx, 3, dynamic_price_1_item)

                    dynamic_name_2_item = QTableWidgetItem(row_data[5] or "")
                    table_widget.setItem(row_idx, 4, dynamic_name_2_item)

                    dynamic_price_2_item = QTableWidgetItem(str(row_data[6]))
                    table_widget.setItem(row_idx, 5, dynamic_price_2_item)

            table_widget.resizeColumnsToContents()
            return True

    except sqlite3.Error as e:
        show_error_message_box(
            parent=None,
            title="خطا",
            message=f"خطا در بارگذاری خدمات و اسناد:\n{str(e)}"
        )
        return False

    except Exception as e:
        show_error_message_box(
            parent=None,
            title="خطا",
            message=f"خطا در بارگذاری خدمات و اسناد:\n{str(e)}"
        )
        return False


def _create_table_item(value, editable: bool = False) -> QTableWidgetItem:
    if value is None:
        display_text = ""
    elif isinstance(value, int):
        # Format integers with thousand separators and convert to Persian
        display_text = to_persian_number(f"{value:,}")
    else:
        display_text = str(value)

    item = QTableWidgetItem(display_text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item

