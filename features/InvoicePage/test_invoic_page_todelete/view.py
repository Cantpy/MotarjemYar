from typing import List, Dict, Any, Optional
from datetime import date
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QPalette, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QSpacerItem, QSizePolicy,
    QAbstractItemView, QHeaderView, QFrame, QDateEdit, QTextEdit,
    QComboBox, QSpinBox, QCheckBox, QTabWidget, QMessageBox,
    QCompleter as QCompleterBase, QApplication
)

from models import Customer, Service, Invoice, InvoiceItem, PaymentStatus, DeliveryStatus


class NumberConverter:
    """Utility class for converting between Persian and English numbers."""

    PERSIAN_TO_ENGLISH = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }

    ENGLISH_TO_PERSIAN = {v: k for k, v in PERSIAN_TO_ENGLISH.items()}

    @classmethod
    def to_persian(cls, text: str) -> str:
        """Convert English numbers to Persian."""
        result = str(text)
        for eng, per in cls.ENGLISH_TO_PERSIAN.items():
            result = result.replace(eng, per)
        return result

    @classmethod
    def to_english(cls, text: str) -> str:
        """Convert Persian numbers to English."""
        result = str(text)
        for per, eng in cls.PERSIAN_TO_ENGLISH.items():
            result = result.replace(per, eng)
        return result


class SubstringCompleter(QCompleterBase):
    """Custom completer that matches substrings."""

    def __init__(self, items: List[str], parent=None):
        super().__init__(items, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)


class BaseWidget(QWidget):
    """Base widget with common functionality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_fonts()
        self.setup_styling()

    def setup_fonts(self):
        """Setup common fonts."""
        self.default_font = QFont("IRANSans", 10)
        self.bold_font = QFont("IRANSans", 10, QFont.Weight.Bold)
        self.title_font = QFont("IRANSans", 12, QFont.Weight.Bold)
        self.large_font = QFont("IRANSans", 14, QFont.Weight.Bold)

    def setup_styling(self):
        """Setup widget styling."""
        self.setStyleSheet("""
            QGroupBox {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 20px;
                padding-left: 20px;
                padding-right: 20px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                color: palette(windowText);
                background-color: transparent;
            }

            QLineEdit {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 4px;
            }

            QLineEdit:focus {
                border: 1px solid palette(link);
            }

            QPushButton {
                background-color: palette(button);
                color: palette(buttonText);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px 12px;
            }

            QPushButton:hover {
                background-color: palette(light);
            }

            QPushButton:pressed {
                background-color: palette(dark);
            }
        """)

    def show_message(self, title: str, message: str, message_type: str = "information"):
        """Show message box."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if message_type == "information":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif message_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif message_type == "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)

        return msg_box.exec()

    def confirm_action(self, title: str, message: str) -> bool:
        """Show confirmation dialog."""
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes


class CustomerFormWidget(BaseWidget):
    """Widget for customer information input."""

    # Signals
    customer_data_changed = Signal(dict)
    save_customer_requested = Signal(dict)
    delete_customer_requested = Signal(str)
    customer_search_requested = Signal(str, str)  # field_type, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # CustomerModel group box
        self.customer_group = QGroupBox("اطلاعات مشتری")
        self.customer_group.setFont(self.bold_font)
        layout.addWidget(self.customer_group)

        customer_layout = QVBoxLayout(self.customer_group)

        # Form layout
        form_layout = QVBoxLayout()

        # National ID
        national_id_layout = QHBoxLayout()
        national_id_layout.addWidget(QLabel("کد ملی:"))
        self.national_id_edit = QLineEdit()
        self.national_id_edit.setPlaceholderText("کد ملی 10 رقمی")
        national_id_layout.addWidget(self.national_id_edit)
        form_layout.addLayout(national_id_layout)

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("نام و نام خانوادگی:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("نام کامل مشتری")
        name_layout.addWidget(self.name_edit)
        form_layout.addLayout(name_layout)

        # Phone
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(QLabel("شماره تلفن:"))
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("شماره تلفن")
        phone_layout.addWidget(self.phone_edit)
        form_layout.addLayout(phone_layout)

        # Address
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("آدرس:"))
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("آدرس کامل")
        address_layout.addWidget(self.address_edit)
        form_layout.addLayout(address_layout)

        # Optional fields
        optional_layout = QHBoxLayout()

        # Email
        email_layout = QVBoxLayout()
        email_layout.addWidget(QLabel("ایمیل (اختیاری):"))
        self.email_edit = QLineEdit()
        email_layout.addWidget(self.email_edit)
        optional_layout.addLayout(email_layout)

        # Telegram ID
        telegram_layout = QVBoxLayout()
        telegram_layout.addWidget(QLabel("تلگرام (اختیاری):"))
        self.telegram_edit = QLineEdit()
        telegram_layout.addWidget(self.telegram_edit)
        optional_layout.addLayout(telegram_layout)

        form_layout.addLayout(optional_layout)
        customer_layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("ذخیره مشتری")
        self.save_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; }")
        button_layout.addWidget(self.save_button)

        self.delete_button = QPushButton("حذف مشتری")
        self.delete_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        button_layout.addWidget(self.delete_button)

        self.clear_button = QPushButton("پاک کردن فرم")
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()
        customer_layout.addLayout(button_layout)

        # Set tab order
        self.setTabOrder(self.national_id_edit, self.name_edit)
        self.setTabOrder(self.name_edit, self.phone_edit)
        self.setTabOrder(self.phone_edit, self.address_edit)
        self.setTabOrder(self.address_edit, self.email_edit)
        self.setTabOrder(self.email_edit, self.telegram_edit)

    def connect_signals(self):
        """Connect widget signals."""
        # Text change signals for auto-search
        self.national_id_edit.textChanged.connect(
            lambda text: self.customer_search_requested.emit("national_id", text)
        )
        self.name_edit.textChanged.connect(
            lambda text: self.customer_search_requested.emit("name", text)
        )
        self.phone_edit.textChanged.connect(
            lambda text: self.customer_search_requested.emit("phone", text)
        )

        # Button signals
        self.save_button.clicked.connect(self.on_save_clicked)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.clear_button.clicked.connect(self.clear_form)

        # Data change signal
        for edit in [self.national_id_edit, self.name_edit, self.phone_edit,
                     self.address_edit, self.email_edit, self.telegram_edit]:
            edit.textChanged.connect(self.on_data_changed)

    def on_save_clicked(self):
        """Handle save button click."""
        customer_data = self.get_customer_data()
        self.save_customer_requested.emit(customer_data)

    def on_delete_clicked(self):
        """Handle delete button click."""
        national_id = self.national_id_edit.text().strip()
        if national_id:
            if self.confirm_action("تایید حذف", f"آیا از حذف مشتری با کد ملی {national_id} اطمینان دارید؟"):
                self.delete_customer_requested.emit(national_id)

    def on_data_changed(self):
        """Handle data change."""
        customer_data = self.get_customer_data()
        self.customer_data_changed.emit(customer_data)

    def get_customer_data(self) -> Dict[str, str]:
        """Get customer data from form."""
        return {
            'national_id': self.national_id_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'telegram_id': self.telegram_edit.text().strip()
        }

    def set_customer_data(self, customer: Customer):
        """Set form data from customer object."""
        self.national_id_edit.setText(customer.national_id)
        self.name_edit.setText(customer.name)
        self.phone_edit.setText(customer.phone)
        self.address_edit.setText(customer.address)
        self.email_edit.setText(customer.email or "")
        self.telegram_edit.setText(customer.telegram_id or "")

    def clear_form(self):
        """Clear all form fields."""
        for edit in [self.national_id_edit, self.name_edit, self.phone_edit,
                     self.address_edit, self.email_edit, self.telegram_edit]:
            edit.clear()

    def set_completers(self, suggestions: Dict[str, List[str]]):
        """Set auto-complete suggestions."""
        if 'national_id' in suggestions:
            completer = SubstringCompleter(suggestions['national_id'])
            self.national_id_edit.setCompleter(completer)

        if 'name' in suggestions:
            completer = SubstringCompleter(suggestions['name'])
            self.name_edit.setCompleter(completer)

        if 'phone' in suggestions:
            completer = SubstringCompleter(suggestions['phone'])
            self.phone_edit.setCompleter(completer)

    def show_validation_errors(self, errors: Dict[str, str]):
        """Show validation errors on form fields."""
        # Clear previous errors
        for edit in [self.national_id_edit, self.name_edit, self.phone_edit, self.address_edit]:
            edit.setStyleSheet("")
            edit.setToolTip("")

        # Show new errors
        field_mapping = {
            'national_id': self.national_id_edit,
            'name': self.name_edit,
            'phone': self.phone_edit,
            'address': self.address_edit
        }

        for field, error_message in errors.items():
            if field in field_mapping:
                edit = field_mapping[field]
                edit.setStyleSheet("QLineEdit { border: 2px solid red; background-color: #ffe6e6; }")
                edit.setToolTip(error_message)


class DocumentsTableWidget(BaseWidget):
    """Widget for displaying and managing invoice items."""

    # Signals
    item_added = Signal(dict)
    item_deleted = Signal(int)
    item_edited = Signal(int, dict)
    selection_changed = Signal(int)  # row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Setup columns
        headers = ["ردیف", "نام سند", "تعداد", "قیمت واحد", "قیمت کل", "رسمی", "مهر قضایی", "مهر خارجه"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Configure table
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ردیف
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # نام سند
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # تعداد
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # قیمت واحد
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # قیمت کل
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # رسمی
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # مهر قضایی
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # مهر خارجه

        # Set column widths
        self.table.setColumnWidth(0, 60)  # ردیف
        self.table.setColumnWidth(2, 80)  # تعداد
        self.table.setColumnWidth(3, 100)  # قیمت واحد
        self.table.setColumnWidth(4, 120)  # قیمت کل
        self.table.setColumnWidth(5, 60)  # رسمی
        self.table.setColumnWidth(6, 80)  # مهر قضایی
        self.table.setColumnWidth(7, 80)  # مهر خارجه

        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.delete_button = QPushButton("حذف آیتم")
        self.delete_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        button_layout.addWidget(self.delete_button)

        self.edit_button = QPushButton("ویرایش آیتم")
        button_layout.addWidget(self.edit_button)

        self.clear_button = QPushButton("پاک کردن همه")
        self.clear_button.setStyleSheet("QPushButton { background-color: #ffc107; color: black; }")
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()

        # Total label
        self.total_label = QLabel("مجموع: ۰ تومان")
        self.total_label.setFont(self.title_font)
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                background-color: #f8f9fa;
                border: 1px solid #28a745;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        button_layout.addWidget(self.total_label)

        layout.addLayout(button_layout)

    def connect_signals(self):
        """Connect widget signals."""
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        self.clear_button.clicked.connect(self.on_clear_clicked)

    def on_selection_changed(self):
        """Handle selection change."""
        current_row = self.table.currentRow()
        self.selection_changed.emit(current_row)

    def on_delete_clicked(self):
        """Handle delete button click."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            if self.confirm_action("تایید حذف", "آیا از حذف این آیتم اطمینان دارید؟"):
                item_id = self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
                self.item_deleted.emit(item_id or current_row)

    def on_edit_clicked(self):
        """Handle edit button click."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            item_data = self.get_row_data(current_row)
            self.item_edited.emit(current_row, item_data)

    def on_clear_clicked(self):
        """Handle clear button click."""
        if self.table.rowCount() > 0:
            if self.confirm_action("تایید پاک کردن", "آیا از پاک کردن تمام آیتم‌ها اطمینان دارید؟"):
                self.clear_table()

    def add_item(self, item: InvoiceItem):
        """Add an item to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Row number
        row_item = QTableWidgetItem(str(row + 1))
        row_item.setData(Qt.ItemDataRole.UserRole, item.id)
        self.table.setItem(row, 0, row_item)

        # Item data
        self.table.setItem(row, 1, QTableWidgetItem(item.item_name))
        self.table.setItem(row, 2, QTableWidgetItem(NumberConverter.to_persian(str(item.item_qty))))
        self.table.setItem(row, 3, QTableWidgetItem(NumberConverter.to_persian(str(item.item_price))))
        self.table.setItem(row, 4, QTableWidgetItem(NumberConverter.to_persian(str(item.total_price))))
        self.table.setItem(row, 5, QTableWidgetItem("بله" if item.officiality else "خیر"))
        self.table.setItem(row, 6, QTableWidgetItem("بله" if item.judiciary_seal else "خیر"))
        self.table.setItem(row, 7, QTableWidgetItem("بله" if item.foreign_affairs_seal else "خیر"))

        self.update_totals()

    def remove_item(self, row: int):
        """Remove an item from the table."""
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
            self.update_row_numbers()
            self.update_totals()

    def clear_table(self):
        """Clear all items from the table."""
        self.table.setRowCount(0)
        self.update_totals()

    def update_row_numbers(self):
        """Update row numbers after deletion."""
        for row in range(self.table.rowCount()):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def update_totals(self):
        """Update the total amount display."""
        total = 0
        for row in range(self.table.rowCount()):
            amount_item = self.table.item(row, 4)
            if amount_item:
                try:
                    amount_text = NumberConverter.to_english(amount_item.text())
                    total += int(amount_text)
                except (ValueError, TypeError):
                    continue

        total_text = NumberConverter.to_persian(f"{total:,}")
        self.total_label.setText(f"مجموع: {total_text} تومان")

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """Get data from a specific row."""
        if row < 0 or row >= self.table.rowCount():
            return {}

        return {
            'name': self.table.item(row, 1).text(),
            'quantity': NumberConverter.to_english(self.table.item(row, 2).text()),
            'price': NumberConverter.to_english(self.table.item(row, 3).text()),
            'officiality': self.table.item(row, 5).text() == "بله",
            'judiciary_seal': self.table.item(row, 6).text() == "بله",
            'foreign_affairs_seal': self.table.item(row, 7).text() == "بله"
        }

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items from the table."""
        items = []
        for row in range(self.table.rowCount()):
            items.append(self.get_row_data(row))
        return items

    def load_items(self, items: List[InvoiceItem]):
        """Load items into the table."""
        self.clear_table()
        for item in items:
            self.add_item(item)


class ServiceInputWidget(BaseWidget):
    """Widget for service/document input."""

    # Signals
    service_requested = Signal(str, int, dict)  # service_name, quantity, options

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # ServicesModel selection group
        service_group = QGroupBox("اضافه کردن سند")
        service_group.setFont(self.bold_font)
        layout.addWidget(service_group)

        service_layout = QVBoxLayout(service_group)

        # ServicesModel name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("نام سند:"))
        self.service_name_edit = QLineEdit()
        self.service_name_edit.setPlaceholderText("نام سند یا خدمات...")
        name_layout.addWidget(self.service_name_edit)
        service_layout.addLayout(name_layout)

        # Quantity and price
        details_layout = QHBoxLayout()

        # Quantity
        qty_layout = QVBoxLayout()
        qty_layout.addWidget(QLabel("تعداد:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.setValue(1)
        qty_layout.addWidget(self.quantity_spin)
        details_layout.addLayout(qty_layout)

        # Price
        price_layout = QVBoxLayout()
        price_layout.addWidget(QLabel("قیمت واحد:"))
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("قیمت به تومان")
        price_layout.addWidget(self.price_edit)
        details_layout.addLayout(price_layout)

        service_layout.addLayout(details_layout)

        # Options
        options_layout = QHBoxLayout()

        self.official_check = QCheckBox("رسمی")
        options_layout.addWidget(self.official_check)

        self.judiciary_check = QCheckBox("مهر قوه قضاییه")
        options_layout.addWidget(self.judiciary_check)

        self.foreign_check = QCheckBox("مهر امور خارجه")
        options_layout.addWidget(self.foreign_check)

        options_layout.addStretch()
        service_layout.addLayout(options_layout)

        # Add button
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("افزودن به فاکتور")
        self.add_button.setStyleSheet("QPushButton { background-color: #007bff; color: white; }")
        self.add_button.setMinimumHeight(40)
        button_layout.addWidget(self.add_button)
        service_layout.addLayout(button_layout)

        # Remarks
        remarks_layout = QVBoxLayout()
        remarks_layout.addWidget(QLabel("توضیحات (اختیاری):"))
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(80)
        self.remarks_edit.setPlaceholderText("توضیحات اضافی...")
        remarks_layout.addWidget(self.remarks_edit)
        service_layout.addLayout(remarks_layout)

    def connect_signals(self):
        """Connect widget signals."""
        self.add_button.clicked.connect(self.on_add_clicked)
        self.service_name_edit.returnPressed.connect(self.on_add_clicked)

    def on_add_clicked(self):
        """Handle add button click."""
        service_name = self.service_name_edit.text().strip()
        if not service_name:
            self.show_message("خطا", "لطفاً نام سند را وارد کنید.", "warning")
            return

        try:
            quantity = self.quantity_spin.value()
            price_text = NumberConverter.to_english(self.price_edit.text().strip())
            price = int(price_text) if price_text else 0

            if price <= 0:
                self.show_message("خطا", "لطفاً قیمت معتبر وارد کنید.", "warning")
                return

            options = {
                'officiality': 1 if self.official_check.isChecked() else 0,
                'judiciary_seal': 1 if self.judiciary_check.isChecked() else 0,
                'foreign_affairs_seal': 1 if self.foreign_check.isChecked() else 0,
                'remarks': self.remarks_edit.toPlainText().strip() or None,
                'price': price
            }

            self.service_requested.emit(service_name, quantity, options)
            self.clear_form()

        except ValueError:
            self.show_message("خطا", "لطفاً قیمت معتبر وارد کنید.", "warning")

    def clear_form(self):
        """Clear the form."""
        self.service_name_edit.clear()
        self.quantity_spin.setValue(1)
        self.price_edit.clear()
        self.official_check.setChecked(False)
        self.judiciary_check.setChecked(False)
        self.foreign_check.setChecked(False)
        self.remarks_edit.clear()

    def set_service_completer(self, service_names: List[str]):
        """Set auto-completer for service names."""
        completer = SubstringCompleter(service_names)
        self.service_name_edit.setCompleter(completer)

    def set_service_data(self, service: Service):
        """Set form data from service."""
        self.service_name_edit.setText(service.name)
        self.price_edit.setText(NumberConverter.to_persian(str(service.base_price)))


class InvoiceHeaderWidget(BaseWidget):
    """Widget for invoice header information."""

    # Signals
    invoice_data_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Invoice info group
        invoice_group = QGroupBox("اطلاعات فاکتور")
        invoice_group.setFont(self.bold_font)
        layout.addWidget(invoice_group)

        invoice_layout = QVBoxLayout(invoice_group)

        # First row: Invoice number and dates
        first_row = QHBoxLayout()

        # Invoice number
        number_layout = QVBoxLayout()
        number_layout.addWidget(QLabel("شماره فاکتور:"))
        self.invoice_number_label = QLabel("1000")
        self.invoice_number_label.setStyleSheet("QLabel { font-weight: bold; color: #007bff; }")
        number_layout.addWidget(self.invoice_number_label)
        first_row.addLayout(number_layout)

        # Issue date
        issue_date_layout = QVBoxLayout()
        issue_date_layout.addWidget(QLabel("تاریخ صدور:"))
        self.issue_date_edit = QDateEdit()
        self.issue_date_edit.setDate(date.today())
        self.issue_date_edit.setCalendarPopup(True)
        issue_date_layout.addWidget(self.issue_date_edit)
        first_row.addLayout(issue_date_layout)

        # Delivery date
        delivery_date_layout = QVBoxLayout()
        delivery_date_layout.addWidget(QLabel("تاریخ تحویل:"))
        self.delivery_date_edit = QDateEdit()
        self.delivery_date_edit.setDate(date.today())
        self.delivery_date_edit.setCalendarPopup(True)
        delivery_date_layout.addWidget(self.delivery_date_edit)
        first_row.addLayout(delivery_date_layout)

        first_row.addStretch()
        invoice_layout.addLayout(first_row)

        # Second row: Languages and translator
        second_row = QHBoxLayout()

        # Source language
        source_lang_layout = QVBoxLayout()
        source_lang_layout.addWidget(QLabel("زبان مبدا:"))
        self.source_language_edit = QLineEdit()
        self.source_language_edit.setPlaceholderText("زبان مبدا")
        source_lang_layout.addWidget(self.source_language_edit)
        second_row.addLayout(source_lang_layout)

        # Target language
        target_lang_layout = QVBoxLayout()
        target_lang_layout.addWidget(QLabel("زبان مقصد:"))
        self.target_language_edit = QLineEdit()
        self.target_language_edit.setPlaceholderText("زبان مقصد")
        target_lang_layout.addWidget(self.target_language_edit)
        second_row.addLayout(target_lang_layout)

        # Translator
        translator_layout = QVBoxLayout()
        translator_layout.addWidget(QLabel("مترجم:"))
        self.translator_edit = QLineEdit()
        self.translator_edit.setPlaceholderText("نام مترجم")
        translator_layout.addWidget(self.translator_edit)
        second_row.addLayout(translator_layout)

        invoice_layout.addLayout(second_row)

        # Third row: Financial details
        financial_group = QGroupBox("جزئیات مالی")
        invoice_layout.addWidget(financial_group)

        financial_layout = QHBoxLayout(financial_group)

        # Advance payment
        advance_layout = QVBoxLayout()
        advance_layout.addWidget(QLabel("پیش‌پرداخت:"))
        self.advance_payment_edit = QLineEdit()
        self.advance_payment_edit.setPlaceholderText("0")
        self.advance_payment_edit.setText("0")
        advance_layout.addWidget(self.advance_payment_edit)
        financial_layout.addLayout(advance_layout)

        # Discount
        discount_layout = QVBoxLayout()
        discount_layout.addWidget(QLabel("تخفیف:"))
        self.discount_edit = QLineEdit()
        self.discount_edit.setPlaceholderText("0")
        self.discount_edit.setText("0")
        discount_layout.addWidget(self.discount_edit)
        financial_layout.addLayout(discount_layout)

        # Force majeure
        force_majeure_layout = QVBoxLayout()
        force_majeure_layout.addWidget(QLabel("قوه قهریه:"))
        self.force_majeure_edit = QLineEdit()
        self.force_majeure_edit.setPlaceholderText("0")
        self.force_majeure_edit.setText("0")
        force_majeure_layout.addWidget(self.force_majeure_edit)
        financial_layout.addLayout(force_majeure_layout)

        financial_layout.addStretch()

        # Remarks
        remarks_layout = QVBoxLayout()
        remarks_layout.addWidget(QLabel("توضیحات:"))
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(80)
        self.remarks_edit.setPlaceholderText("توضیحات اضافی...")
        remarks_layout.addWidget(self.remarks_edit)
        invoice_layout.addLayout(remarks_layout)

    def connect_signals(self):
        """Connect widget signals."""
        # Connect all input fields to data change signal
        for widget in [self.issue_date_edit, self.delivery_date_edit, self.source_language_edit,
                       self.target_language_edit, self.translator_edit, self.advance_payment_edit,
                       self.discount_edit, self.force_majeure_edit]:
            if hasattr(widget, 'textChanged'):
                widget.textChanged.connect(self.on_data_changed)
            elif hasattr(widget, 'dateChanged'):
                widget.dateChanged.connect(self.on_data_changed)

        self.remarks_edit.textChanged.connect(self.on_data_changed)

    def on_data_changed(self):
        """Handle data change."""
        invoice_data = self.get_invoice_data()
        self.invoice_data_changed.emit(invoice_data)

    def get_invoice_data(self) -> Dict[str, Any]:
        """Get invoice data from form."""
        try:
            advance_payment = int(NumberConverter.to_english(self.advance_payment_edit.text() or "0"))
            discount = int(NumberConverter.to_english(self.discount_edit.text() or "0"))
            force_majeure = int(NumberConverter.to_english(self.force_majeure_edit.text() or "0"))
        except ValueError:
            advance_payment = discount = force_majeure = 0

        return {
            'issue_date': self.issue_date_edit.date().toPython(),
            'delivery_date': self.delivery_date_edit.date().toPython(),
            'source_language': self.source_language_edit.text().strip() or None,
            'target_language': self.target_language_edit.text().strip() or None,
            'translator': self.translator_edit.text().strip(),
            'advance_payment': advance_payment,
            'discount_amount': discount,
            'force_majeure': force_majeure,
            'remarks': self.remarks_edit.toPlainText().strip() or None
        }

    def set_invoice_number(self, number: int):
        """Set invoice number."""
        self.invoice_number_label.setText(NumberConverter.to_persian(str(number)))

    def set_invoice_data(self, invoice: Invoice):
        """Set form data from invoice."""
        self.set_invoice_number(invoice.invoice_number)
        self.issue_date_edit.setDate(invoice.issue_date)
        self.delivery_date_edit.setDate(invoice.delivery_date)
        self.source_language_edit.setText(invoice.source_language or "")
        self.target_language_edit.setText(invoice.target_language or "")
        self.translator_edit.setText(invoice.translator)
        self.advance_payment_edit.setText(NumberConverter.to_persian(str(invoice.advance_payment)))
        self.discount_edit.setText(NumberConverter.to_persian(str(invoice.discount_amount)))
        self.force_majeure_edit.setText(NumberConverter.to_persian(str(invoice.force_majeure)))
        self.remarks_edit.setPlainText(invoice.remarks or "")


class InvoiceMainWidget(BaseWidget):
    """Main invoice widget combining all components."""

    # Signals
    invoice_saved = Signal(dict)
    invoice_preview_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # CustomerModel tab
        self.customer_widget = CustomerFormWidget()
        self.tab_widget.addTab(self.customer_widget, "اطلاعات مشتری")

        # Invoice tab
        invoice_tab = QWidget()
        invoice_layout = QVBoxLayout(invoice_tab)

        # Invoice header
        self.invoice_header = InvoiceHeaderWidget()
        invoice_layout.addWidget(self.invoice_header)

        # ServicesModel input
        self.service_input = ServiceInputWidget()
        invoice_layout.addWidget(self.service_input)

        # Documents table
        self.documents_table = DocumentsTableWidget()
        invoice_layout.addWidget(self.documents_table)

        self.tab_widget.addTab(invoice_tab, "جزئیات فاکتور")

        # Action buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("ذخیره فاکتور")
        self.save_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; }")
        self.save_button.setMinimumHeight(40)
        button_layout.addWidget(self.save_button)

        self.preview_button = QPushButton("نمایش فاکتور")
        self.preview_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; }")
        self.preview_button.setMinimumHeight(40)
        button_layout.addWidget(self.preview_button)

        self.clear_button = QPushButton("فرم جدید")
        self.clear_button.setMinimumHeight(40)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def connect_signals(self):
        """Connect widget signals."""
        # ServicesModel input to documents table
        self.service_input.service_requested.connect(self.on_service_requested)

        # Action buttons
        self.save_button.clicked.connect(self.on_save_clicked)
        self.preview_button.clicked.connect(self.on_preview_clicked)
        self.clear_button.clicked.connect(self.clear_all)

    def on_service_requested(self, service_name: str, quantity: int, options: Dict[str, Any]):
        """Handle service addition request."""
        # Create invoice item
        item = InvoiceItem(
            invoice_number=0,  # Will be set later
            item_name=service_name,
            item_qty=quantity,
            item_price=options['price'],
            officiality=options.get('officiality', 0),
            judiciary_seal=options.get('judiciary_seal', 0),
            foreign_affairs_seal=options.get('foreign_affairs_seal', 0),
            remarks=options.get('remarks')
        )

        self.documents_table.add_item(item)

    def on_save_clicked(self):
        """Handle save button click."""
        invoice_data = self.get_complete_invoice_data()
        self.invoice_saved.emit(invoice_data)

    def on_preview_clicked(self):
        """Handle preview button click."""
        invoice_data = self.get_complete_invoice_data()
        self.invoice_preview_requested.emit(invoice_data)

    def get_complete_invoice_data(self) -> Dict[str, Any]:
        """Get complete invoice data from all components."""
        customer_data = self.customer_widget.get_customer_data()
        invoice_data = self.invoice_header.get_invoice_data()
        items_data = self.documents_table.get_all_items()

        # Merge all data
        complete_data = {
            **customer_data,
            **invoice_data,
            'items': items_data
        }

        return complete_data

    def clear_all(self):
        """Clear all forms."""
        if self.confirm_action("تایید پاک کردن", "آیا از پاک کردن تمام اطلاعات اطمینان دارید؟"):
            self.customer_widget.clear_form()
            self.service_input.clear_form()
            self.documents_table.clear_table()
            self.tab_widget.setCurrentIndex(0)  # Go back to customer tab

    def set_invoice_number(self, number: int):
        """Set invoice number."""
        self.invoice_header.set_invoice_number(number)

    def load_invoice(self, invoice: Invoice):
        """Load invoice data into the form."""
        # Load customer data
        customer = Customer(
            national_id=invoice.national_id,
            name=invoice.name,
            phone=invoice.phone,
            address=""  # Not available in invoice
        )
        self.customer_widget.set_customer_data(customer)

        # Load invoice header
        self.invoice_header.set_invoice_data(invoice)

        # Load items
        self.documents_table.load_items(invoice.items)
