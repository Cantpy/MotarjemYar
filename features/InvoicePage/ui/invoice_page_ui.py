# -*- coding: utf-8 -*-
"""
Clean and modular PySide6 UI for Invoice Page
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy,
    QAbstractItemView, QHeaderView
)


class InvoicePageUI(object):
    """Main invoice page widget with customer information and document management."""

    def setupUi(self, InvoicePage):
        """Setup the user interface to match controller expectations."""
        if not InvoicePage.objectName():
            InvoicePage.setObjectName("InvoicePage")

        InvoicePage.resize(932, 776)
        InvoicePage.setFont(self._get_font())
        InvoicePage.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        InvoicePage.setStyleSheet("background-color: rgb(240, 240, 240);")

        # Main layout
        self.main_layout = QVBoxLayout(InvoicePage)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(50, 20, 50, 20)

        # Create customer section
        self._create_customer_section()

        # Create documents section
        self._create_documents_section()

        # Add to main layout
        self.main_layout.addWidget(self.customer_gb)
        self.main_layout.addWidget(self.documents_section)

        # Set tab order as expected by controller
        QWidget.setTabOrder(self.national_id_le, self.full_name_le)
        QWidget.setTabOrder(self.full_name_le, self.phone_le)
        QWidget.setTabOrder(self.phone_le, self.address_le)

    def _create_customer_section(self):
        """Create customer information section with correct object names."""
        self.customer_gb = QGroupBox("اطلاعات مشتری")
        self.customer_gb.setObjectName("customer_gb")
        self.customer_gb.setMinimumSize(QSize(0, 230))
        self.customer_gb.setMaximumSize(QSize(16777215, 350))
        self.customer_gb.setFont(self._get_bold_font(10))
        self.customer_gb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Customer group layout
        customer_layout = QHBoxLayout(self.customer_gb)
        customer_layout.setContentsMargins(1, 20, 1, 20)

        # Action buttons
        self._create_customer_buttons()
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.invoice_button_add_customer)
        buttons_layout.addWidget(self.invoice_button_delete_customer)
        buttons_layout.addWidget(self.invoice_button_customer_affairs)

        # Input fields
        self._create_customer_fields()
        fields_layout = QVBoxLayout()

        # First row: National ID, Full Name, Phone
        first_row = QHBoxLayout()
        first_row.addLayout(self._create_field_layout("شماره تماس", self.phone_le))
        first_row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum))
        first_row.addLayout(self._create_field_layout("نام و نام خانوادگی", self.full_name_le))
        first_row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum))
        first_row.addLayout(self._create_field_layout("کد ملی", self.national_id_le))

        # Second row: Address
        address_layout = self._create_field_layout("آدرس", self.address_le)

        fields_layout.addLayout(first_row)
        fields_layout.addLayout(address_layout)

        # Combine layouts
        customer_layout.addLayout(buttons_layout)
        customer_layout.addItem(QSpacerItem(50, 13, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum))
        customer_layout.addLayout(fields_layout)

    def _create_customer_buttons(self):
        """Create customer action buttons with correct object names."""
        self.invoice_button_add_customer = QPushButton()
        self.invoice_button_add_customer.setObjectName("invoice_button_add_customer")
        self.invoice_button_add_customer.setMinimumSize(QSize(80, 0))
        self.invoice_button_add_customer.setFont(self._get_font(10))
        self.invoice_button_add_customer.setToolTip(
            '<html><head/><body><p align="right"><span style=" color:#0055ff;">افزودن مشتری</span></p></body></html>')
        self.invoice_button_add_customer.setIconSize(QSize(45, 45))

        self.invoice_button_delete_customer = QPushButton()
        self.invoice_button_delete_customer.setObjectName("invoice_button_delete_customer")
        self.invoice_button_delete_customer.setMinimumSize(QSize(80, 0))
        self.invoice_button_delete_customer.setFont(self._get_font(10))
        self.invoice_button_delete_customer.setToolTip(
            '<html><head/><body><p align="right"><span style=" color:#0055ff;">حذف مشتری</span></p></body></html>')
        self.invoice_button_delete_customer.setIconSize(QSize(45, 45))

        self.invoice_button_customer_affairs = QPushButton()
        self.invoice_button_customer_affairs.setObjectName("invoice_button_customer_affairs")
        self.invoice_button_customer_affairs.setMinimumSize(QSize(80, 0))
        self.invoice_button_customer_affairs.setFont(self._get_font(10))
        self.invoice_button_customer_affairs.setToolTip(
            '<html><head/><body><p align="right"><span style=" color:#0055ff;">امور مشتریان</span></p></body></html>')
        self.invoice_button_customer_affairs.setIconSize(QSize(45, 45))

    def _create_customer_fields(self):
        """Create customer input fields with correct object names."""
        # National ID field
        self.national_id_le = QLineEdit()
        self.national_id_le.setObjectName("national_id_le")
        self.national_id_le.setFont(self._get_font())
        self.national_id_le.setToolTip('<html><head/><body><p>کد ملی مشتری را وارد کنید</p></body></html>')
        self.national_id_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Full name field
        self.full_name_le = QLineEdit()
        self.full_name_le.setObjectName("full_name_le")
        self.full_name_le.setFont(self._get_font())
        self.full_name_le.setToolTip('<html><head/><body><p>نام کامل مشتری را وارد کنید</p></body></html>')
        self.full_name_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.full_name_le.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Phone field
        self.phone_le = QLineEdit()
        self.phone_le.setObjectName("phone_le")
        self.phone_le.setFont(self._get_font())
        self.phone_le.setToolTip('<html><head/><body><p>شماره تلفن مشتری را وارد کنید</p></body></html>')
        self.phone_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Address field
        self.address_le = QLineEdit()
        self.address_le.setObjectName("address_le")
        self.address_le.setFont(self._get_font())
        self.address_le.setToolTip('<html><head/><body><p>آدرس مشتری را وارد کنید</p></body></html>')
        self.address_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _create_documents_section(self):
        """Create documents section with correct object names."""
        self.documents_section = QGroupBox("اطلاعات اسناد")
        self.documents_section.setObjectName("documents_section")
        self.documents_section.setMinimumSize(QSize(0, 476))
        self.documents_section.setFont(self._get_bold_font(10))
        self.documents_section.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Documents section layout
        documents_layout = QVBoxLayout(self.documents_section)

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
        actions_layout.addWidget(self.preview_invoice_button, 0, Qt.AlignmentFlag.AlignVCenter)

        # Total amount label
        self.total_amount_label = QLabel("مجموع: 0 تومان")
        self.total_amount_label.setObjectName("total_amount_label")
        self.total_amount_label.setFont(self._get_bold_font(12))
        self.total_amount_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Main layout assembly
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.addLayout(controls_layout)
        content_layout.addWidget(self.tableWidget)
        content_layout.addWidget(self.total_amount_label)

        documents_layout.addLayout(content_layout)
        documents_layout.addLayout(actions_layout)

    def _create_document_controls(self):
        """Create document input controls with correct object names."""
        self.add_document_to_invoice_button = QPushButton()
        self.add_document_to_invoice_button.setObjectName("add_document_to_invoice_button")
        self.add_document_to_invoice_button.setMinimumSize(QSize(150, 0))
        self.add_document_to_invoice_button.setMaximumSize(QSize(16777215, 35))
        self.add_document_to_invoice_button.setToolTip(
            '<html><head/><body><p align="right"><span style=" color:#0055ff;">افزودن سند به فاکتور</span></p></body></html>'
        )
        self.add_document_to_invoice_button.setIconSize(QSize(60, 60))

        self.documents_le = QLineEdit()
        self.documents_le.setObjectName("documents_le")
        self.documents_le.setMaximumSize(QSize(16777215, 35))
        self.documents_le.setFont(self._get_font())
        self.documents_le.setToolTip(
            '<html><head/><body><p align="right">نام سند را وارد کنید</p></body></html>'
        )

    def _create_documents_table(self):
        """Create documents table with correct object name."""
        self.tableWidget = QTableWidget()
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setMinimumSize(QSize(0, 300))
        self.tableWidget.setFont(self._get_font(8))
        self.tableWidget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(5)

        # Configure headers
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget.verticalHeader().setStretchLastSection(False)

        # Setup table headers to match controller expectations
        headers = ["ردیف", "نام سند", "تعداد", "قیمت واحد", "قیمت کل"]
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            self.tableWidget.setHorizontalHeaderItem(i, item)

        # Set horizontal scrollbar policy as expected by controller
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _create_action_buttons(self):
        """Create action buttons with correct object names."""
        self.clear_table_button = QPushButton("پاکسازی جدول")
        self.clear_table_button.setObjectName("clear_table_button")
        self.clear_table_button.setMaximumSize(QSize(200, 16777215))

        self.delete_item_button = QPushButton("حذف آیتم")
        self.delete_item_button.setObjectName("delete_item_button")

        self.edit_item_button = QPushButton("ویرایش آیتم")
        self.edit_item_button.setObjectName("edit_item_button")

        self.preview_invoice_button = QPushButton("نمایش فاکتور (F1)")
        self.preview_invoice_button.setObjectName("preview_invoice_button")
        self.preview_invoice_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _create_field_layout(self, label_text, field):
        """Create a vertical layout for label and field."""
        layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setFont(self._get_font(9, bold=True))
        layout.addWidget(label)
        layout.addWidget(field)
        return layout

    def _get_font(self, size=None, bold=False):
        """Get standard font for the application."""
        font = QFont("IRANSans")
        if size:
            font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font

    def _get_bold_font(self, size):
        """Get bold font."""
        return self._get_font(size, bold=True)


class CustomerInfoGroup(QGroupBox):
    """Customer information section with input fields and action buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("customer_info_group")
        self.setTitle("اطلاعات مشتری")
        self._setup_ui()

    def _setup_ui(self):
        """Initialize customer section UI."""
        self._configure_group()
        self._create_components()
        self._setup_layout()

    def _configure_group(self):
        """Configure group box properties."""
        self.setMinimumSize(QSize(0, 230))
        self.setMaximumSize(QSize(16777215, 350))
        self.setFont(self._get_bold_font(10))
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _create_components(self):
        """Create all customer section components."""
        self._create_action_buttons()
        self._create_input_fields()

    def _create_action_buttons(self):
        """Create customer action buttons."""
        self.add_customer_btn = self._create_icon_button(
            "add_customer_btn",
            "افزودن مشتری"
        )
        self.delete_customer_btn = self._create_icon_button(
            "delete_customer_btn",
            "حذف مشتری"
        )
        self.customer_affairs_btn = self._create_icon_button(
            "customer_affairs_btn",
            "امور مشتریان"
        )

    def _create_input_fields(self):
        """Create customer information input fields."""
        # National ID field
        self.national_id_label = QLabel("کد ملی")
        self.national_id_input = self._create_input_field(
            "national_id_input",
            "کد ملی مشتری را وارد کنید"
        )

        # Full name field
        self.full_name_label = QLabel("نام و نام خانوادگی")
        self.full_name_input = self._create_input_field(
            "full_name_input",
            "نام کامل مشتری را وارد کنید"
        )
        self.full_name_input.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Phone field
        self.phone_label = QLabel("شماره تماس")
        self.phone_input = self._create_input_field(
            "phone_input",
            "شماره تلفن مشتری را وارد کنید"
        )

        # Address field
        self.address_label = QLabel("آدرس")
        self.address_input = self._create_input_field(
            "address_input",
            "آدرس مشتری را وارد کنید"
        )

    def _setup_layout(self):
        """Organize components in layouts."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(1, 20, 1, 20)

        # Action buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.add_customer_btn)
        buttons_layout.addWidget(self.delete_customer_btn)
        buttons_layout.addWidget(self.customer_affairs_btn)

        # Input fields layout
        fields_layout = QVBoxLayout()

        # First row: National ID, Full Name, Phone
        first_row = QHBoxLayout()
        first_row.addLayout(self._create_field_layout(self.phone_label, self.phone_input))
        first_row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum))
        first_row.addLayout(self._create_field_layout(self.full_name_label, self.full_name_input))
        first_row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum))
        first_row.addLayout(self._create_field_layout(self.national_id_label, self.national_id_input))

        # Second row: Address
        address_layout = self._create_field_layout(self.address_label, self.address_input)

        fields_layout.addLayout(first_row)
        fields_layout.addLayout(address_layout)

        # Combine layouts
        main_layout.addLayout(buttons_layout)
        main_layout.addItem(QSpacerItem(50, 13, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(fields_layout)

    def _create_icon_button(self, object_name, tooltip):
        """Create an icon button with tooltip."""
        button = QPushButton()
        button.setObjectName(object_name)
        button.setMinimumSize(QSize(80, 0))
        button.setFont(self._get_font(10))
        button.setToolTip(
            f'<html><head/><body><p align="right"><span style=" color:#0055ff;">{tooltip}</span></p></body></html>')
        button.setIconSize(QSize(30, 30))
        return button

    def _create_input_field(self, object_name, placeholder):
        """Create a standardized input field."""
        field = QLineEdit()
        field.setObjectName(object_name)
        field.setFont(self._get_font())
        field.setToolTip(f'<html><head/><body><p>{placeholder}</p></body></html>')
        field.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return field

    def _create_field_layout(self, label, field):
        """Create a vertical layout for label and field."""
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(field)
        return layout

    def _get_font(self, size=None, bold=False):
        """Get font for customer section."""
        font = QFont("IRANSans")
        if size:
            font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font

    def _get_bold_font(self, size):
        """Get bold font."""
        return self._get_font(size, bold=True)


class DocumentsGroup(QGroupBox):
    """Documents management section with table and controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("documents_group")
        self.setTitle("اطلاعات اسناد")
        self._setup_ui()

    def _setup_ui(self):
        """Initialize documents section UI."""
        self._configure_group()
        self._create_components()
        self._setup_layout()

    def _configure_group(self):
        """Configure group box properties."""
        self.setMinimumSize(QSize(0, 476))
        self.setFont(self._get_bold_font(10))
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _create_components(self):
        """Create all documents section components."""
        self._create_document_controls()
        self._create_documents_table()
        self._create_action_buttons()

    def _create_document_controls(self):
        """Create document input controls."""
        self.add_document_btn = QPushButton()
        self.add_document_btn.setObjectName("add_document_btn")
        self.add_document_btn.setMinimumSize(QSize(150, 0))
        self.add_document_btn.setMaximumSize(QSize(16777215, 35))
        self.add_document_btn.setToolTip(
            '<html><head/><body><p align="right"><span style=" color:#0055ff;">افزودن سند به فاکتور</span></p></body></html>'
        )
        self.add_document_btn.setIconSize(QSize(30, 30))

        self.document_name_label = QLabel("نام سند")
        self.document_name_label.setMaximumSize(QSize(16777215, 15))
        self.document_name_label.setFont(self._get_font(9, bold=True))

        self.document_name_input = QLineEdit()
        self.document_name_input.setObjectName("document_name_input")
        self.document_name_input.setMaximumSize(QSize(16777215, 35))
        self.document_name_input.setFont(self._get_font())
        self.document_name_input.setToolTip(
            '<html><head/><body><p align="right">نام سند را وارد کنید</p></body></html>'
        )

    def _create_documents_table(self):
        """Create and configure the documents table."""
        self.documents_table = QTableWidget()
        self.documents_table.setObjectName("documents_table")
        self._configure_table()
        self._setup_table_headers()

    def _configure_table(self):
        """Configure table properties."""
        self.documents_table.setMinimumSize(QSize(0, 300))
        self.documents_table.setFont(self._get_font(8))
        self.documents_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.documents_table.setAlternatingRowColors(False)
        self.documents_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.documents_table.setRowCount(0)
        self.documents_table.setColumnCount(8)

        # Configure headers
        self.documents_table.horizontalHeader().setStretchLastSection(False)
        self.documents_table.verticalHeader().setCascadingSectionResizes(False)
        self.documents_table.verticalHeader().setStretchLastSection(False)

    def _setup_table_headers(self):
        """Setup table column headers."""
        headers = [
            "نام سند",  # Document Name
            "نوع",  # Type
            "تعداد",  # Quantity
            "داد",  # Given
            "اخ",  # Received
            "قیمت کل",  # Total Price
            "توضیحات",  # Description
            ""  # Actions column
        ]

        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            self.documents_table.setHorizontalHeaderItem(i, item)

    def _create_action_buttons(self):
        """Create table action buttons."""
        self.clear_table_btn = QPushButton("پاکسازی جدول")
        self.clear_table_btn.setObjectName("clear_table_btn")
        self.clear_table_btn.setMaximumSize(QSize(200, 16777215))

        self.delete_item_btn = QPushButton("حذف آیتم")
        self.delete_item_btn.setObjectName("delete_item_btn")

        self.edit_item_btn = QPushButton("ویرایش آیتم")
        self.edit_item_btn.setObjectName("edit_item_btn")

        self.preview_invoice_btn = QPushButton("نمایش فاکتور (F1)")
        self.preview_invoice_btn.setObjectName("preview_invoice_btn")
        self.preview_invoice_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _setup_layout(self):
        """Organize components in layouts."""
        main_layout = QVBoxLayout(self)

        # Document controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

        # Add document button
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.add_document_btn)

        # Document name input
        name_layout = QVBoxLayout()
        name_layout.setSpacing(10)
        name_layout.addWidget(self.document_name_label)
        name_layout.addWidget(self.document_name_input)

        controls_layout.addLayout(button_layout)
        controls_layout.addLayout(name_layout)

        # Action buttons layout
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(10, 5, 10, -1)
        actions_layout.addWidget(self.clear_table_btn)
        actions_layout.addWidget(self.delete_item_btn)
        actions_layout.addWidget(self.edit_item_btn)
        actions_layout.addItem(QSpacerItem(60, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        actions_layout.addWidget(self.preview_invoice_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # Main layout assembly
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.addLayout(controls_layout)
        content_layout.addWidget(self.documents_table)

        main_layout.addLayout(content_layout)
        main_layout.addLayout(actions_layout)

    def _get_font(self, size=None, bold=False):
        """Get font for documents section."""
        font = QFont("IRANSans")
        if size:
            font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font

    def _get_bold_font(self, size):
        """Get bold font."""
        return self._get_font(size, bold=True)


# Example usage
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = InvoicePageUI()
    window.show()
    sys.exit(app.exec())
