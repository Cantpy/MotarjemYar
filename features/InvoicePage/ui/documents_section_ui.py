# -*- coding: utf-8 -*-
"""
Documents Section UI - Fixed to match the expected interface
"""
import sys

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy,
    QAbstractItemView, QHeaderView, QFrame
)


class DocumentsSectionUI(QWidget):
    """Documents section widget for invoice creation."""

    # Add missing signals
    data_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocumentsPage")
        self.customer_data = {}
        self.documents_list = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the user interface for documents section."""
        self.resize(932, 776)
        self.setFont(self._get_font())
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setStyleSheet("background-color: rgb(240, 240, 240);")

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(50, 20, 50, 20)

        # Create header section
        self._create_header_section()

        # Create documents section
        self._create_documents_section()

        # Create navigation section
        self._create_navigation_section()

        # Add to main layout
        self.main_layout.addWidget(self.header_frame)
        self.main_layout.addWidget(self.documents_section)
        self.main_layout.addWidget(self.navigation_frame)

    def _create_header_section(self):
        """Create header section with customer summary."""
        self.header_frame = QFrame()
        self.header_frame.setObjectName("header_frame")
        self.header_frame.setMaximumHeight(100)
        self.header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.header_frame.setStyleSheet(
            "QFrame { background-color: rgb(250, 250, 250); border: 1px solid rgb(200, 200, 200); border-radius: 5px; }")

        header_layout = QVBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # Title
        title_label = QLabel("مرحله دوم: اطلاعات اسناد")
        title_label.setFont(self._get_bold_font(14))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: rgb(0, 85, 255);")

        # Customer summary
        self.customer_summary_label = QLabel("مشتری: در حال بارگذاری...")
        self.customer_summary_label.setObjectName("customer_summary_label")
        self.customer_summary_label.setFont(self._get_font(10))
        self.customer_summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.customer_summary_label.setStyleSheet("color: rgb(100, 100, 100);")

        header_layout.addWidget(title_label)
        header_layout.addWidget(self.customer_summary_label)

    def _create_documents_section(self):
        """Create documents section with table and controls."""
        self.documents_section = QGroupBox("اطلاعات اسناد")
        self.documents_section.setObjectName("documents_section")
        self.documents_section.setMinimumSize(QSize(0, 500))
        self.documents_section.setFont(self._get_bold_font(10))
        self.documents_section.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Documents section layout
        documents_layout = QVBoxLayout(self.documents_section)
        documents_layout.setSpacing(20)

        # Document controls
        self._create_document_controls()
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

        # Add document button
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.add_document_to_invoice_button)

        # Document name input
        name_layout = QVBoxLayout()
        name_layout.setSpacing(10)

        documents_label = QLabel("نام سند")
        documents_label.setMaximumSize(QSize(16777215, 15))
        documents_label.setFont(self._get_font(9, bold=True))

        name_layout.addWidget(documents_label)
        name_layout.addWidget(self.documents_le)

        controls_layout.addLayout(button_layout)
        controls_layout.addLayout(name_layout)

        # Table
        self._create_documents_table()

        # Action buttons
        self._create_action_buttons()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(10, 5, 10, -1)
        actions_layout.addWidget(self.clear_table_button)
        actions_layout.addWidget(self.delete_item_button)
        actions_layout.addWidget(self.edit_item_button)
        actions_layout.addItem(QSpacerItem(60, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))

        # Total amount label
        self.total_amount_label = QLabel("مجموع: 0 تومان")
        self.total_amount_label.setObjectName("total_amount_label")
        self.total_amount_label.setFont(self._get_bold_font(12))
        self.total_amount_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.total_amount_label.setStyleSheet(
            "color: rgb(0, 128, 0); padding: 10px; background-color: rgb(245, 255, 245); border: 1px solid rgb(200, 255, 200); border-radius: 5px;")

        # Main layout assembly
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.addLayout(controls_layout)
        content_layout.addWidget(self.tableWidget)
        content_layout.addWidget(self.total_amount_label)

        documents_layout.addLayout(content_layout)
        documents_layout.addLayout(actions_layout)

    def _create_document_controls(self):
        """Create document input controls."""
        self.add_document_to_invoice_button = QPushButton("افزودن سند")
        self.add_document_to_invoice_button.setObjectName("add_document_to_invoice_button")
        self.add_document_to_invoice_button.setMinimumSize(QSize(150, 40))
        self.add_document_to_invoice_button.setMaximumSize(QSize(16777215, 40))
        self.add_document_to_invoice_button.setFont(self._get_font(10))
        self.add_document_to_invoice_button.setToolTip("افزودن سند به فاکتور")
        self.add_document_to_invoice_button.setStyleSheet(
            "QPushButton { background-color: rgb(0, 120, 215); color: white; border: none; border-radius: 5px; padding: 8px; }"
            "QPushButton:hover { background-color: rgb(0, 100, 180); }"
            "QPushButton:pressed { background-color: rgb(0, 80, 150); }"
        )

        self.documents_le = QLineEdit()
        self.documents_le.setObjectName("documents_le")
        self.documents_le.setMinimumSize(QSize(0, 35))
        self.documents_le.setMaximumSize(QSize(16777215, 35))
        self.documents_le.setFont(self._get_font())
        self.documents_le.setToolTip("نام سند را وارد کنید")
        self.documents_le.setStyleSheet(
            "QLineEdit { padding: 5px; border: 1px solid rgb(200, 200, 200); border-radius: 3px; }")

    def _create_documents_table(self):
        """Create documents table."""
        self.tableWidget = QTableWidget()
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setMinimumSize(QSize(0, 250))
        self.tableWidget.setFont(self._get_font(9))
        self.tableWidget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(5)

        # Configure headers
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget.verticalHeader().setStretchLastSection(False)
        self.tableWidget.verticalHeader().setVisible(False)

        # Setup table headers
        headers = ["ردیف", "نام سند", "تعداد", "قیمت واحد", "قیمت کل"]
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            item.setFont(self._get_bold_font(9))
            self.tableWidget.setHorizontalHeaderItem(i, item)

        # Set column widths
        self.tableWidget.setColumnWidth(0, 60)  # ردیف
        self.tableWidget.setColumnWidth(1, 200)  # نام سند
        self.tableWidget.setColumnWidth(2, 100)  # تعداد
        self.tableWidget.setColumnWidth(3, 120)  # قیمت واحد
        # قیمت کل will stretch

        # Set scrollbar policy
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Style the table
        self.tableWidget.setStyleSheet(
            "QTableWidget { border: 1px solid rgb(200, 200, 200); border-radius: 5px; }"
            "QTableWidget::item { padding: 5px; border-bottom: 1px solid rgb(230, 230, 230); }"
            "QTableWidget::item:selected { background-color: rgb(230, 240, 255); }"
            "QHeaderView::section { background-color: rgb(240, 240, 240); padding: 8px; border: 1px solid rgb(200, 200, 200); font-weight: bold; }"
        )

    def _create_action_buttons(self):
        """Create action buttons."""
        button_style = (
            "QPushButton { background-color: rgb(245, 245, 245); border: 1px solid rgb(200, 200, 200); border-radius: 5px; padding: 8px 15px; }"
            "QPushButton:hover { background-color: rgb(230, 230, 230); }"
            "QPushButton:pressed { background-color: rgb(215, 215, 215); }"
        )

        self.clear_table_button = QPushButton("پاکسازی جدول")
        self.clear_table_button.setObjectName("clear_table_button")
        self.clear_table_button.setMaximumSize(QSize(200, 16777215))
        self.clear_table_button.setFont(self._get_font(9))
        self.clear_table_button.setStyleSheet(button_style)

        self.delete_item_button = QPushButton("حذف آیتم")
        self.delete_item_button.setObjectName("delete_item_button")
        self.delete_item_button.setFont(self._get_font(9))
        self.delete_item_button.setStyleSheet(button_style)

        self.edit_item_button = QPushButton("ویرایش آیتم")
        self.edit_item_button.setObjectName("edit_item_button")
        self.edit_item_button.setFont(self._get_font(9))
        self.edit_item_button.setStyleSheet(button_style)

    def _create_navigation_section(self):
        """Create navigation section with back and next buttons."""
        self.navigation_frame = QFrame()
        self.navigation_frame.setObjectName("navigation_frame")
        self.navigation_frame.setMaximumHeight(80)
        self.navigation_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.navigation_frame.setStyleSheet(
            "QFrame { background-color: rgb(250, 250, 250); border: 1px solid rgb(200, 200, 200); border-radius: 5px; }")

        navigation_layout = QHBoxLayout(self.navigation_frame)
        navigation_layout.setContentsMargins(20, 15, 20, 15)

        # Back button
        self.back_button = QPushButton("بازگشت به مشتری")
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(150, 40))
        self.back_button.setFont(self._get_font(10))
        self.back_button.setStyleSheet(
            "QPushButton { background-color: rgb(108, 117, 125); color: white; border: none; border-radius: 5px; padding: 8px; }"
            "QPushButton:hover { background-color: rgb(90, 98, 104); }"
            "QPushButton:pressed { background-color: rgb(73, 80, 87); }"
        )

        # Spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Preview invoice button
        self.preview_invoice_button = QPushButton("نمایش فاکتور (F1)")
        self.preview_invoice_button.setObjectName("preview_invoice_button")
        self.preview_invoice_button.setMinimumSize(QSize(150, 40))
        self.preview_invoice_button.setFont(self._get_font(10))
        self.preview_invoice_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.preview_invoice_button.setStyleSheet(
            "QPushButton { background-color: rgb(40, 167, 69); color: white; border: none; border-radius: 5px; padding: 8px; }"
            "QPushButton:hover { background-color: rgb(33, 136, 56); }"
            "QPushButton:pressed { background-color: rgb(25, 104, 43); }"
        )

        navigation_layout.addWidget(self.back_button)
        navigation_layout.addItem(spacer)
        navigation_layout.addWidget(self.preview_invoice_button)

        # Set tab order
        QWidget.setTabOrder(self.documents_le, self.add_document_to_invoice_button)

    def _connect_signals(self):
        """Connect signals."""
        self.documents_le.textChanged.connect(self._on_data_changed)
        self.add_document_to_invoice_button.clicked.connect(self._add_document)
        self.clear_table_button.clicked.connect(self._clear_table)
        self.delete_item_button.clicked.connect(self._delete_item)
        self.edit_item_button.clicked.connect(self._edit_item)

    def _on_data_changed(self):
        """Handle data change."""
        self.data_changed.emit(self.get_data())

    def _add_document(self):
        """Add document to table."""
        errors = self.validate_form()
        if errors:
            return

        # Get values
        name = self.documents_le.text().strip()

        # Add to table
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)

        self.tableWidget.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.tableWidget.setItem(row, 1, QTableWidgetItem(name))

        # Clear form
        self.documents_le.clear()

        # Update total
        self._update_total()

    def _clear_table(self):
        """Clear table."""
        self.tableWidget.setRowCount(0)
        self._update_total()

    def _delete_item(self):
        """Delete selected item."""
        current_row = self.tableWidget.currentRow()
        if current_row >= 0:
            self.tableWidget.removeRow(current_row)
            self._update_row_numbers()
            self._update_total()

    def _edit_item(self):
        """Edit selected item."""
        current_row = self.tableWidget.currentRow()
        if current_row >= 0:
            name = self.tableWidget.item(current_row, 1).text()
            quantity = self.tableWidget.item(current_row, 2).text()
            unit_price = self.tableWidget.item(current_row, 3).text()

            self.documents_le.setText(name)

            self.tableWidget.removeRow(current_row)
            self._update_row_numbers()
            self._update_total()

    def _update_row_numbers(self):
        """Update row numbers."""
        for i in range(self.tableWidget.rowCount()):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(i + 1)))

    def _update_total(self):
        """Update total amount."""
        total = 0
        for i in range(self.tableWidget.rowCount()):
            total += float(self.tableWidget.item(i, 4).text())
        self.total_amount_label.setText(f"مجموع: {total:,.0f} تومان")

    def _get_font(self, size=None, bold=False):
        """Get standard font for the application."""
        font = QFont("IRANSans")
        if size:
            font.setPointSize(size)
        else:
            font.setPointSize(10)
        if bold:
            font.setBold(True)
        return font

    def _get_bold_font(self, size):
        """Get bold font."""
        return self._get_font(size, bold=True)

    # Missing methods that main invoice page expects
    def set_customer_data(self, customer_data):
        """Set customer data and update display."""
        self.customer_data = customer_data
        self.update_customer_summary(customer_data)

    def update_customer_summary(self, customer_data):
        """Update the customer summary display."""
        if customer_data:
            summary_text = f"مشتری: {customer_data.get('full_name', 'نامشخص')} - کد ملی: {customer_data.get('national_id', 'نامشخص')} - تلفن: {customer_data.get('phone', 'نامشخص')}"
            self.customer_summary_label.setText(summary_text)
        else:
            self.customer_summary_label.setText("مشتری: اطلاعات در دسترس نیست")

    def get_data(self):
        """Get documents data."""
        documents = []
        for i in range(self.tableWidget.rowCount()):
            doc = {
                'name': self.tableWidget.item(i, 1).text(),
                'quantity': float(self.tableWidget.item(i, 2).text()),
                'unit_price': float(self.tableWidget.item(i, 3).text()),
                'total_price': float(self.tableWidget.item(i, 4).text())
            }
            documents.append(doc)
        return documents

    def reset(self):
        """Reset the form."""
        self.clear_form()
        self.customer_data = {}

    def clear_form(self):
        """Clear all form inputs."""
        self.documents_le.clear()
        self.tableWidget.setRowCount(0)
        self.total_amount_label.setText("مجموع: 0 تومان")

    def get_form_data(self):
        """Get current form data."""
        return {
            'document_name': self.documents_le.text(),
        }

    def set_form_data(self, data):
        """Set form data."""
        self.documents_le.setText(data.get('document_name', ''))

    def validate_form(self):
        """Validate the current form input."""
        errors = []

        if not self.documents_le.text().strip():
            errors.append("نام سند الزامی است")

        return errors


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    window = DocumentsSectionUI()
    window.show()
    sys.exit(app.exec())
