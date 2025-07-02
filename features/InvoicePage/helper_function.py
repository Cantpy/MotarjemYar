import sqlite3
from modules.helper_functions import return_resource
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QTableWidget, QHeaderView

documents_database = return_resource('databases', 'documents.db')


def get_all_fixed_prices():
    """Get all fixed prices with their labels."""
    try:
        with sqlite3.connect(documents_database) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label_name, name, price, is_default 
                FROM fixed_prices 
                ORDER BY id
            """)

            return cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Error fetching fixed prices: {e}")
        return []

def get_fixed_price_by_label(label_name):
    """Get fixed price by label name."""
    try:
        with sqlite3.connect(documents_database) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT price FROM fixed_prices 
                WHERE label_name = ? AND is_default = 1
            """, (label_name,))

            result = cursor.fetchone()
            return result[0] if result else 0

    except sqlite3.Error as e:
        print(f"Error fetching fixed price: {e}")
        return 0

def no_edit_table_items(table: QTableWidget):
    row_count = table.rowCount()
    column_count = table.columnCount()

    for row in range(row_count):
        for col in range(column_count):
            item = table.item(row, col)
            if item:  # Ensure the item exists
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)


def block_column_zero_selection(table: QTableWidget):
    table.setSelectionBehavior(QTableWidget.SelectItems)

    def on_item_selection_changed():
        selected_items = table.selectedItems()
        for item in selected_items:
            if item.column() == 0:
                item.setSelected(False)

    table.itemSelectionChanged.connect(on_item_selection_changed)


def clear_table_selection(table_widget: QTableWidget):
    """Deselects all selected items and removes focus from the QTableWidget."""
    table_widget.clearSelection()
    table_widget.clearFocus()
    table_widget.setCurrentCell(-1, -1)  # Removes current cell highlight