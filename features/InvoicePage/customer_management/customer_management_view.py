from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLineEdit, QLabel, QHeaderView, QAbstractItemView,
    QMessageBox, QMenu, QToolTip
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QAction, QFont, QColor, QBrush
from typing import List, Optional
from features.InvoicePage.customer_management.customer_managemnet_models import CustomerDisplayData


class CustomerManagementView(QDialog):
    """Customer management dialog view."""

    # Signals
    search_requested = Signal(str)
    add_customer_requested = Signal()
    edit_customer_requested = Signal(str)  # national_id
    delete_customer_requested = Signal(str)  # national_id
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_data = []
        self.init_ui()
        self._set_stylesheet()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("مدیریت مشتریان")
        self.setModal(True)
        self.resize(1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("جستجو:")
        search_label.setFont(self.get_font(weight='bold', size=10))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو در نام، کد ملی، تلفن مشتری یا همراه...")
        self.search_input.setFont(self.get_font())
        self.search_input.textChanged.connect(self.on_search_text_changed)

        self.search_button = QPushButton("جستجو")
        self.search_button.clicked.connect(self.on_search_clicked)
        self.search_button.setFont(self.get_font(size=12))

        self.clear_search_button = QPushButton("پاک کردن")
        self.clear_search_button.clicked.connect(self.on_clear_search_clicked)
        self.clear_search_button.setFont(self.get_font(size=12))

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_search_button)
        search_layout.addStretch()

        layout.addLayout(search_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("افزودن مشتری")
        self.add_button.clicked.connect(self.on_add_customer_clicked)
        self.add_button.setFont(self.get_font())

        self.edit_button = QPushButton("ویرایش مشتری")
        self.edit_button.clicked.connect(self.on_edit_customer_clicked)
        self.edit_button.setFont(self.get_font())
        self.edit_button.setEnabled(False)

        self.delete_button = QPushButton("حذف مشتری")
        self.delete_button.clicked.connect(self.on_delete_customer_clicked)
        self.delete_button.setFont(self.get_font())
        self.delete_button.setEnabled(False)

        self.refresh_button = QPushButton("بروزرسانی")
        self.refresh_button.setFont(self.get_font())
        self.refresh_button.clicked.connect(self.on_refresh_clicked)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel("آماده")
        self.status_label.setStyleSheet("QLabel { color: blue; }")
        self.status_label.setFont(self.get_font())
        layout.addWidget(self.status_label)

        # Close button
        close_layout = QHBoxLayout()
        self.close_button = QPushButton("بستن")
        self.close_button.clicked.connect(self.close)
        self.close_button.setFont(self.get_font())
        close_layout.addStretch()
        close_layout.addWidget(self.close_button)
        layout.addLayout(close_layout)

    def setup_table(self):
        """Setup the customer table."""
        # Define columns
        self.columns = [
            "کد ملی",  # 0
            "نام",  # 1
            "تلفن",  # 2
            "ایمیل",  # 3
            "آدرس",  # 4
            "تلگرام",  # 5
            "تعداد فاکتور",  # 6
            "همراهان"  # 7
        ]

        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)

        # Table settings
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        # Header settings
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # National ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Phone
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Email
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Address
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Telegram
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Invoice count
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Companions

        # Connect selection change
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Double-click to edit
        self.table.doubleClicked.connect(self.on_edit_customer_clicked)

    def populate_table(self, customers: List[CustomerDisplayData]):
        """Populate the table with customer data."""
        self.customers_data = customers
        self.table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            # National ID
            self.table.setItem(row, 0, QTableWidgetItem(customer.national_id))

            # Name
            name_item = QTableWidgetItem(customer.name)
            name_item.setFont(QFont("IranSANS", 9))
            self.table.setItem(row, 1, name_item)

            # Phone
            self.table.setItem(row, 2, QTableWidgetItem(customer.phone))

            # Email
            self.table.setItem(row, 3, QTableWidgetItem(customer.email))

            # Address
            address_item = QTableWidgetItem(customer.address)
            address_item.setToolTip(customer.address)
            self.table.setItem(row, 4, address_item)

            # Telegram
            self.table.setItem(row, 5, QTableWidgetItem(customer.telegram_id))

            # Invoice count
            invoice_item = QTableWidgetItem(str(customer.invoice_count))
            invoice_item.setTextAlignment(Qt.AlignCenter)
            if customer.invoice_count > 0:
                invoice_item.setBackground(QBrush(QColor(200, 255, 200)))  # Light green
            self.table.setItem(row, 6, invoice_item)

            # Companions
            companions_text = self.format_companions_text(customer.companions)
            companions_item = QTableWidgetItem(companions_text)
            companions_item.setToolTip(self.format_companions_tooltip(customer.companions))
            if customer.companions:
                companions_item.setBackground(QBrush(QColor(255, 255, 200)))  # Light yellow
            self.table.setItem(row, 7, companions_item)

        # Update status
        self.update_status(f"تعداد مشتریان: {len(customers)}")

    def format_companions_text(self, companions) -> str:
        """Format companions for display in table cell."""
        if not companions:
            return "ندارد"

        if len(companions) == 1:
            return companions[0].name
        else:
            return f"{companions[0].name} و {len(companions) - 1} نفر دیگر"

    def format_companions_tooltip(self, companions) -> str:
        """Format companions for tooltip."""
        if not companions:
            return "این مشتری همراه ندارد"

        tooltip = f"همراهان ({len(companions)}):\n"
        for i, comp in enumerate(companions, 1):
            tooltip += f"{i}. {comp.name} (کد ملی: {comp.national_id})\n"

        return tooltip.strip()

    def get_selected_customer(self) -> Optional[CustomerDisplayData]:
        """Get the currently selected customer."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if 0 <= row < len(self.customers_data):
                return self.customers_data[row]
        return None

    def get_selected_national_id(self) -> Optional[str]:
        """Get the national ID of the selected customer."""
        customer = self.get_selected_customer()
        return customer.national_id if customer else None

    def update_status(self, message: str):
        """Update status label."""
        self.status_label.setText(message)

    def show_error(self, title: str, message: str):
        """Show error message box."""
        QMessageBox.critical(self, title, message)

    def show_info(self, title: str, message: str):
        """Show info message box."""
        QMessageBox.information(self, title, message)

    def show_warning(self, title: str, message: str) -> bool:
        """Show warning message box with Yes/No buttons."""
        reply = QMessageBox.warning(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def show_context_menu(self, position: QPoint):
        """Show context menu on right-click."""
        if self.table.itemAt(position) is None:
            return

        menu = QMenu(self)

        edit_action = QAction("ویرایش مشتری", self)
        edit_action.triggered.connect(self.on_edit_customer_clicked)
        edit_action.setEnabled(self.edit_button.isEnabled())
        menu.addAction(edit_action)

        delete_action = QAction("حذف مشتری", self)
        delete_action.triggered.connect(self.on_delete_customer_clicked)
        delete_action.setEnabled(self.delete_button.isEnabled())
        menu.addAction(delete_action)

        menu.addSeparator()

        refresh_action = QAction("بروزرسانی", self)
        refresh_action.triggered.connect(self.on_refresh_clicked)
        menu.addAction(refresh_action)

        menu.exec(self.table.mapToGlobal(position))

    # Event handlers
    def on_search_text_changed(self, text: str):
        """Handle search text change."""
        if len(text) >= 2 or text == "":
            self.search_requested.emit(text)

    def on_search_clicked(self):
        """Handle search button click."""
        self.search_requested.emit(self.search_input.text())

    def on_clear_search_clicked(self):
        """Handle clear search button click."""
        self.search_input.clear()
        self.search_requested.emit("")

    def on_add_customer_clicked(self):
        """Handle add customer button click."""
        self.add_customer_requested.emit()

    def on_edit_customer_clicked(self):
        """Handle edit customer button click."""
        national_id = self.get_selected_national_id()
        if national_id:
            self.edit_customer_requested.emit(national_id)

    def on_delete_customer_clicked(self):
        """Handle delete customer button click."""
        national_id = self.get_selected_national_id()
        if national_id:
            self.delete_customer_requested.emit(national_id)

    def on_refresh_clicked(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()

    def on_selection_changed(self):
        """Handle table selection change."""
        has_selection = self.get_selected_customer() is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def clear_selection(self):
        """Clear table selection."""
        self.table.clearSelection()

    def select_customer_by_national_id(self, national_id: str):
        """Select a customer by national ID."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # National ID column
            if item and item.text() == national_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                break

    def _set_stylesheet(self):
        self.setStyleSheet(""""
           /* --- Base Styles --- */

                QDialog {
                    background-color: #f0f2f5; /* Light gray background */
                }
                
                /* --- Headers and Labels --- */
                
                QLabel {
                    color: #333; /* Dark gray for text */
                    font-size: 10pt;
                }
                
                QDialog QLabel#status_label {
                    font-weight: bold;
                    color: #4a7dff; /* A clean blue for status messages */
                }
                
                /* --- Buttons --- */
                
                QPushButton {
                    font-family: "IranSANS", sans-serif;
                    font-size: 10pt;
                    padding: 8px 16px;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    background-color: #ffffff;
                    color: #333;
                    outline: none;
                    transition: background-color 0.2s, color 0.2s;
                }
                
                QPushButton:hover {
                    background-color: #e6e6e6;
                }
                
                QPushButton:pressed {
                    background-color: #dcdcdc;
                    border-color: #a0a0a0;
                }
                
                QPushButton:disabled {
                    background-color: #f5f5f5;
                    color: #aaa;
                    border-color: #e0e0e0;
                }
                
                /* Highlighted Action Buttons (e.g., "Add") */
                QPushButton#add_button {
                    background-color: #4CAF50; /* Green for success/add */
                    color: #ffffff;
                    border-color: #45a049;
                }
                
                QPushButton#add_button:hover {
                    background-color: #45a049;
                }
                
                QPushButton#add_button:pressed {
                    background-color: #3e8e41;
                }
                
                /* Danger Action Buttons (e.g., "Delete") */
                QPushButton#delete_button {
                    background-color: #f44336; /* Red for danger/delete */
                    color: #ffffff;
                    border-color: #da332a;
                }
                
                QPushButton#delete_button:hover {
                    background-color: #da332a;
                }
                
                QPushButton#delete_button:pressed {
                    background-color: #c9302c;
                }
                
                /* --- Line Edits (Input Fields) --- */
                
                QLineEdit {
                    font-family: "IranSANS", sans-serif;
                    font-size: 10pt;
                    padding: 6px 10px;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    background-color: #ffffff;
                    selection-background-color: #4a7dff;
                    selection-color: #ffffff;
                }
                
                QLineEdit:focus {
                    border: 1px solid #4a7dff;
                }
                
                /* --- Table View --- */
                
                QTableWidget {
                    font-family: "IranSANS", sans-serif;
                    font-size: 9pt;
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    gridline-color: #e0e0e0;
                    selection-background-color: #cfe2ff; /* Light blue for selection */
                    selection-color: #000000;
                }
                
                QHeaderView::section {
                    background-color: #f7f7f7;
                    color: #333;
                    padding: 5px;
                    border-right: 1px solid #e0e0e0;
                    border-bottom: 1px solid #e0e0e0;
                    font-weight: bold;
                }
                
                QTableWidget QTableCornerButton::section {
                    background-color: #f7f7f7;
                    border-right: 1px solid #e0e0e0;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                QTableWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #f0f0f0;
                }
                
                QTableWidget::item:selected {
                    background-color: #cfe2ff;
                } 
        """)

    @staticmethod
    def get_font(weight: str = 'normal', size: int = 10, italic: bool = False) -> QFont:
        """
        Returns a QFont object for the IranSANS font with specified options.

        Args:
            weight (str): The font weight. Accepts 'ultralight', 'light', 'normal',
                          'medium', 'bold', 'black'. Defaults to 'normal'.
            size (int): The font size in points. Defaults to 10.
            italic (bool): If True, returns an italic font. Defaults to False.

        Returns:
            QFont: A QFont object configured with the specified options.
        """
        # Map friendly names to QFont.Weight constants.
        weight_map = {
            'ultralight': QFont.Weight.Thin,
            'light': QFont.Weight.Light,
            'normal': QFont.Weight.Normal,
            'medium': QFont.Weight.DemiBold,
            'bold': QFont.Weight.Bold,
            'black': QFont.Weight.Black,
        }

        # Retrieve the correct QFont.Weight constant, defaulting to Normal if not found.
        font_weight = weight_map.get(weight.lower(), QFont.Weight.Normal)

        font = QFont("IranSANS", size, font_weight, italic)
        return font
