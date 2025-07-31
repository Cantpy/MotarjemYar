# -*- coding: utf-8 -*-
"""
View Layer - PySide6 UI Components for Customer Information
"""
import sys
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QSize, Signal, QRegularExpression
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy, QFrame, QSpinBox, QScrollArea,
    QCheckBox, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QTextEdit
)

from features.InvoicePage.customer_info.customer_info_controller import (CustomerInfoController,
                                                                         CustomerManagementController,
                                                                         CustomerDialogController)
from features.InvoicePage.customer_info.customer_info_repo import ICustomerRepository


class CustomerInfoView(QWidget):
    """Customer information view - first step of invoice creation."""

    # Signals
    data_changed = Signal(dict)
    validation_changed = Signal(bool)
    customer_selection_requested = Signal()
    customer_affairs_requested = Signal()

    def __init__(self, customer_repository: ICustomerRepository, parent=None):
        """Initialize view with repository."""
        super().__init__(parent)
        self.setObjectName("CustomerInfoView")
        self.customer_repository = customer_repository
        self.companion_widgets = {}  # Store companion widgets by UI number

        # Initialize controller
        self.controller = CustomerInfoController(customer_repository, self)

        self._setup_ui()
        self._connect_signals()
        self._setup_styles()

        # Initialize controller
        self.controller.initialize()

    def _setup_ui(self):
        """Setup the customer information UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_frame = self._create_title_frame()
        main_layout.addWidget(title_frame)

        # Customer info group
        self.customer_group = self._create_customer_group()
        main_layout.addWidget(self.customer_group)

        # Companions group
        self.companions_group = self._create_companions_group()
        main_layout.addWidget(self.companions_group)

        # Initially hide companions group
        self.companions_group.setVisible(False)

        # Add spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def _create_title_frame(self):
        """Create title frame with description."""
        title_frame = QFrame()
        title_frame.setObjectName("title_frame")

        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(10)

        # Main title
        title_label = QLabel("اطلاعات مشتری")
        title_label.setFont(self._get_font(16, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("main_title")

        # Description
        desc_label = QLabel("لطفاً اطلاعات مشتری و همراهان را به صورت کامل وارد کنید")
        desc_label.setFont(self._get_font(10))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setObjectName("description")

        title_layout.addWidget(title_label)
        title_layout.addWidget(desc_label)

        return title_frame

    def _create_customer_group(self):
        """Create customer information group."""
        group = QGroupBox("اطلاعات مشتری")
        group.setObjectName("customer_gb")
        group.setMinimumSize(QSize(0, 300))
        group.setFont(self._get_font(12, bold=True))
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Group layout
        group_layout = QHBoxLayout(group)
        group_layout.setContentsMargins(20, 30, 20, 30)
        group_layout.setSpacing(40)

        # Input fields
        fields_layout = self._create_input_fields()

        # Action buttons
        buttons_layout = self._create_action_buttons()

        # Add to group layout
        group_layout.addLayout(fields_layout)
        group_layout.addLayout(buttons_layout)

        return group

    def _create_companions_group(self):
        """Create companions information group."""
        group = QGroupBox("اطلاعات همراهان")
        group.setObjectName("companions_gb")
        group.setMinimumSize(QSize(0, 350))
        group.setMaximumSize(QSize(16777215, 450))
        group.setFont(self._get_font(12, bold=True))
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Group layout
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(20, 30, 20, 30)
        group_layout.setSpacing(15)

        # Number of companions input
        companions_count_layout = QHBoxLayout()
        companions_count_layout.setSpacing(10)

        companions_count_label = QLabel("تعداد همراهان:")
        companions_count_label.setFont(self._get_font(10, bold=True))
        companions_count_label.setObjectName("companions_count_label")

        self.companions_count_sb = QSpinBox()
        self.companions_count_sb.setObjectName("companions_count_sb")
        self.companions_count_sb.setMinimum(0)
        self.companions_count_sb.setMaximum(20)
        self.companions_count_sb.setValue(0)
        self.companions_count_sb.setFont(self._get_font(10))

        companions_count_layout.addWidget(companions_count_label)
        companions_count_layout.addWidget(self.companions_count_sb)
        companions_count_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Scroll area for companions
        self.companions_scroll = QScrollArea()
        self.companions_scroll.setWidgetResizable(True)
        self.companions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.companions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.companions_scroll.setMinimumHeight(200)
        self.companions_scroll.setObjectName("companions_scroll")

        # Companions container widget
        self.companions_container = QWidget()
        self.companions_layout = QVBoxLayout(self.companions_container)
        self.companions_layout.setSpacing(10)
        self.companions_layout.setContentsMargins(10, 10, 10, 10)

        # Add button at the bottom
        self.add_companion_btn = QPushButton("➕ افزودن همراه")
        self.add_companion_btn.setObjectName("add_companion_btn")
        self.add_companion_btn.setFont(self._get_font(10))

        self.companions_layout.addWidget(self.add_companion_btn)
        self.companions_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.companions_scroll.setWidget(self.companions_container)

        group_layout.addLayout(companions_count_layout)
        group_layout.addWidget(self.companions_scroll)

        return group

    def _create_action_buttons(self):
        """Create customer action buttons."""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)

        # Add customer button
        self.add_customer_btn = QPushButton("افزودن مشتری")
        self.add_customer_btn.setObjectName("add_customer_btn")
        self.add_customer_btn.setMinimumSize(QSize(120, 45))
        self.add_customer_btn.setFont(self._get_font(10))
        self.add_customer_btn.setToolTip("افزودن مشتری جدید")

        # Delete customer button
        self.delete_customer_btn = QPushButton("حذف مشتری")
        self.delete_customer_btn.setObjectName("delete_customer_btn")
        self.delete_customer_btn.setMinimumSize(QSize(120, 45))
        self.delete_customer_btn.setFont(self._get_font(10))
        self.delete_customer_btn.setToolTip("حذف مشتری")

        # Customer affairs button
        self.customer_affairs_btn = QPushButton("امور مشتریان")
        self.customer_affairs_btn.setObjectName("customer_affairs_btn")
        self.customer_affairs_btn.setMinimumSize(QSize(120, 45))
        self.customer_affairs_btn.setFont(self._get_font(10))
        self.customer_affairs_btn.setToolTip("امور مشتریان")

        buttons_layout.addWidget(self.add_customer_btn)
        buttons_layout.addWidget(self.delete_customer_btn)
        buttons_layout.addWidget(self.customer_affairs_btn)
        buttons_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        return buttons_layout

    def _create_input_fields(self):
        """Create customer input fields."""
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(20)

        # First row: National ID, Full Name, Phone
        first_row = QHBoxLayout()
        first_row.setSpacing(30)

        # National ID
        national_id_layout = self._create_field_layout("کد ملی *", True)
        self.national_id_le = QLineEdit()
        self.national_id_le.setObjectName("national_id_le")
        self.national_id_le.setFont(self._get_font(10))
        self.national_id_le.setPlaceholderText("کد ملی را وارد کنید")
        self.national_id_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        national_id_layout.addWidget(self.national_id_le)

        # Full Name
        full_name_layout = self._create_field_layout("نام و نام خانوادگی *", True)
        self.full_name_le = QLineEdit()
        self.full_name_le.setObjectName("full_name_le")
        self.full_name_le.setFont(self._get_font(10))
        self.full_name_le.setPlaceholderText("نام و نام خانوادگی را وارد کنید")
        self.full_name_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        full_name_layout.addWidget(self.full_name_le)

        # Phone
        phone_layout = self._create_field_layout("شماره تماس *", True)
        self.phone_le = QLineEdit()
        self.phone_le.setObjectName("phone_le")
        self.phone_le.setFont(self._get_font(10))
        self.phone_le.setPlaceholderText("شماره تماس را وارد کنید")
        self.phone_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        phone_layout.addWidget(self.phone_le)

        first_row.addLayout(national_id_layout)
        first_row.addLayout(full_name_layout)
        first_row.addLayout(phone_layout)

        # Second row: Address, Email
        second_row = QHBoxLayout()
        second_row.setSpacing(30)

        # Address
        address_layout = self._create_field_layout("آدرس")
        self.address_le = QLineEdit()
        self.address_le.setObjectName("address_le")
        self.address_le.setFont(self._get_font(10))
        self.address_le.setPlaceholderText("آدرس را وارد کنید")
        self.address_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        address_layout.addWidget(self.address_le)

        # Email
        email_layout = self._create_field_layout("ایمیل")
        self.email_le = QLineEdit()
        self.email_le.setObjectName("email_le")
        self.email_le.setFont(self._get_font(10))
        self.email_le.setPlaceholderText("ایمیل را وارد کنید")
        self.email_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        email_layout.addWidget(self.email_le)

        second_row.addLayout(address_layout)
        second_row.addLayout(email_layout)

        # Third row: Companions checkbox
        third_row = QHBoxLayout()
        third_row.setSpacing(30)

        # Has companions checkbox
        self.has_companions_cb = QCheckBox("آیا همراه دارید؟")
        self.has_companions_cb.setObjectName("has_companions_cb")
        self.has_companions_cb.setFont(self._get_font(10))

        third_row.addWidget(self.has_companions_cb)
        third_row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        fields_layout.addLayout(first_row)
        fields_layout.addLayout(second_row)
        fields_layout.addLayout(third_row)

        return fields_layout

    def _create_field_layout(self, label_text: str, required: bool = False):
        """Create a field layout with label."""
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Label
        label = QLabel(label_text)
        label.setFont(self._get_font(10, bold=True))
        label.setObjectName("field_label")
        if required:
            label.setProperty("required", True)

        layout.addWidget(label)
        return layout

    def _create_companion_widget(self, companion_num: int):
        """Create widget for a single companion."""
        companion_frame = QFrame()
        companion_frame.setObjectName(f"companion_frame_{companion_num}")

        companion_layout = QVBoxLayout(companion_frame)
        companion_layout.setSpacing(10)
        companion_layout.setContentsMargins(15, 15, 15, 15)

        # Header with companion number and delete button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        companion_title = QLabel(f"همراه {companion_num}")
        companion_title.setFont(self._get_font(10, bold=True))
        companion_title.setObjectName("companion_title")

        delete_btn = QPushButton("❌")
        delete_btn.setObjectName(f"delete_companion_{companion_num}")
        delete_btn.setMinimumSize(QSize(30, 30))
        delete_btn.setMaximumSize(QSize(30, 30))
        delete_btn.setProperty("companion_num", companion_num)
        delete_btn.clicked.connect(lambda: self.controller.on_delete_companion_clicked(companion_num))

        header_layout.addWidget(companion_title)
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        header_layout.addWidget(delete_btn)

        # Companion fields
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(20)

        # National ID
        national_id_layout = QVBoxLayout()
        national_id_layout.setSpacing(5)
        national_id_label = QLabel("کد ملی")
        national_id_label.setFont(self._get_font(9, bold=True))
        national_id_label.setObjectName("companion_field_label")

        national_id_le = QLineEdit()
        national_id_le.setObjectName(f"companion_national_id_{companion_num}")
        national_id_le.setFont(self._get_font(9))
        national_id_le.setPlaceholderText("کد ملی")
        national_id_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        national_id_le.textChanged.connect(
            lambda text: self.controller.on_companion_field_changed(companion_num, 'national_id', text))

        national_id_layout.addWidget(national_id_label)
        national_id_layout.addWidget(national_id_le)

        # Full Name
        full_name_layout = QVBoxLayout()
        full_name_layout.setSpacing(5)
        full_name_label = QLabel("نام و نام خانوادگی")
        full_name_label.setFont(self._get_font(9, bold=True))
        full_name_label.setObjectName("companion_field_label")

        full_name_le = QLineEdit()
        full_name_le.setObjectName(f"companion_full_name_{companion_num}")
        full_name_le.setFont(self._get_font(9))
        full_name_le.setPlaceholderText("نام و نام خانوادگی")
        full_name_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        full_name_le.textChanged.connect(
            lambda text: self.controller.on_companion_field_changed(companion_num, 'name', text))

        full_name_layout.addWidget(full_name_label)
        full_name_layout.addWidget(full_name_le)

        # Phone
        phone_layout = QVBoxLayout()
        phone_layout.setSpacing(5)
        phone_label = QLabel("شماره تماس")
        phone_label.setFont(self._get_font(9, bold=True))
        phone_label.setObjectName("companion_field_label")

        phone_le = QLineEdit()
        phone_le.setObjectName(f"companion_phone_{companion_num}")
        phone_le.setFont(self._get_font(9))
        phone_le.setPlaceholderText("شماره تماس")
        phone_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        phone_le.textChanged.connect(
            lambda text: self.controller.on_companion_field_changed(companion_num, 'phone', text))

        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(phone_le)

        fields_layout.addLayout(national_id_layout)
        fields_layout.addLayout(full_name_layout)
        fields_layout.addLayout(phone_layout)

        companion_layout.addLayout(header_layout)
        companion_layout.addLayout(fields_layout)

        return companion_frame

    def _connect_signals(self):
        """Connect UI signals to controller methods."""
        # Customer fields
        self.national_id_le.textChanged.connect(self.controller.on_national_id_changed)
        self.full_name_le.textChanged.connect(self.controller.on_full_name_changed)
        self.phone_le.textChanged.connect(self.controller.on_phone_changed)
        self.address_le.textChanged.connect(self.controller.on_address_changed)
        self.email_le.textChanged.connect(self.controller.on_email_changed)

        # Companions
        self.has_companions_cb.toggled.connect(self.controller.on_has_companions_changed)
        self.companions_count_sb.valueChanged.connect(self.controller.on_companions_count_changed)
        self.add_companion_btn.clicked.connect(self.controller.on_add_companion_clicked)

        # Action buttons
        self.add_customer_btn.clicked.connect(self._on_add_customer_clicked)
        self.delete_customer_btn.clicked.connect(self.controller.on_delete_customer_clicked)
        self.customer_affairs_btn.clicked.connect(self._on_customer_affairs_clicked)

        # Controller signals
        self.controller.data_changed.connect(self.data_changed)
        self.controller.validation_changed.connect(self.validation_changed)
        self.controller.companions_visibility_changed.connect(self.show_companions_group)
        self.controller.companions_count_changed.connect(self.update_companions_count)
        self.controller.field_validation_changed.connect(self.set_field_validation)
        self.controller.error_occurred.connect(self.show_error)
        self.controller.customer_loaded.connect(self._on_customer_loaded)

    def _setup_styles(self):
        """Setup component styles."""
        self.setStyleSheet("""
            /* Title Frame */
            QFrame#title_frame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
            }

            QLabel#main_title {
                color: #333;
                margin-bottom: 10px;
            }

            QLabel#description {
                color: #666;
                border: none;
                padding: 10px;
            }

            /* Group Boxes */
            QGroupBox {
                border: 2px solid #ddd;
                border-radius: 8px;
                margin: 10px;
                padding-top: 20px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px 0 10px;
                color: #333;
            }

            /* Buttons */
            QPushButton#add_customer_btn {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }

            QPushButton#add_customer_btn:hover {
                background-color: #45a049;
            }

            QPushButton#delete_customer_btn {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }

            QPushButton#delete_customer_btn:hover {
                background-color: #da190b;
            }

            QPushButton#customer_affairs_btn {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }

            QPushButton#customer_affairs_btn:hover {
                background-color: #1976D2;
            }

            QPushButton#add_companion_btn {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                margin: 10px 0;
            }

            QPushButton#add_companion_btn:hover {
                background-color: #45a049;
            }

            /* Input Fields */
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 150px;
            }

            QLineEdit:focus {
                border-color: #4CAF50;
            }

            QLineEdit[invalid="true"] {
                border-color: #f44336;
            }

            /* SpinBox */
            QSpinBox {
                padding: 5px 10px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 80px;
            }

            QSpinBox:focus {
                border-color: #4CAF50;
            }

            /* CheckBox */
            QCheckBox {
                color: #333;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }

            /* Scroll Area */
            QScrollArea#companions_scroll {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }

            /* Companion Frames */
            QFrame[objectName^="companion_frame_"] {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }

            /* Labels */
            QLabel#field_label {
                color: #333;
            }

            QLabel#field_label[required="true"] {
                color: #333;
                font-weight: bold;
            }

            QLabel#companion_field_label {
                color: #333;
            }

            QLabel#companion_title {
                color: #333;
            }

            QLabel#companions_count_label {
                color: #333;
            }

            /* Delete companion buttons */
            QPushButton[objectName^="delete_companion_"] {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 12px;
            }

            QPushButton[objectName^="delete_companion_"]:hover {
                background-color: #da190b;
            }
        """)

    def _get_font(self, size: int, bold: bool = False) -> QFont:
        """Get a font with specified size and weight."""
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    # UI Event Handlers
    def _on_add_customer_clicked(self):
        """Handle add customer button click."""
        dialog = CustomerSelectionDialog(self.customer_repository, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_customer = dialog.get_selected_customer()
            if selected_customer:
                self.controller.set_data(selected_customer)

    def _on_customer_affairs_clicked(self):
        """Handle customer affairs button click."""
        dialog = CustomerManagementDialog(self.customer_repository, self)
        dialog.exec()

    def _on_customer_loaded(self, customer_data: Dict[str, Any]):
        """Handle customer loaded signal from controller."""
        if customer_data:
            self.set_customer_data(customer_data)

    # Public interface methods for controller
    def add_companion_row(self, companion_num: int):
        """Add a new companion row to the UI."""
        companion_widget = self._create_companion_widget(companion_num)

        # Store widget reference
        self.companion_widgets[companion_num] = companion_widget

        # Insert before the add button and spacer
        insert_index = self.companions_layout.count() - 2
        self.companions_layout.insertWidget(insert_index, companion_widget)

    def remove_companion_row(self, companion_num: int):
        """Remove a companion row from the UI."""
        if companion_num in self.companion_widgets:
            widget = self.companion_widgets[companion_num]
            widget.deleteLater()
            del self.companion_widgets[companion_num]

    def clear_companions(self):
        """Clear all companion rows."""
        for companion_num in list(self.companion_widgets.keys()):
            self.remove_companion_row(companion_num)
        self.companion_widgets.clear()

    def show_companions_group(self, show: bool = True):
        """Show or hide the companions group."""
        self.companions_group.setVisible(show)

    def update_companions_count(self, count: int):
        """Update the companions count spinbox."""
        self.companions_count_sb.setValue(count)

    def set_field_validation(self, field_name: str, is_valid: bool):
        """Set validation state for a field."""
        field_map = {
            'national_id': self.national_id_le,
            'name': self.full_name_le,
            'phone': self.phone_le,
            'address': self.address_le,
            'email': self.email_le
        }

        # Handle companion fields
        if field_name.startswith('companion_'):
            parts = field_name.split('_')
            if len(parts) >= 3:
                companion_num = int(parts[1])
                comp_field = parts[2]

                if companion_num in self.companion_widgets:
                    widget = self.companion_widgets[companion_num]
                    comp_field_widget = widget.findChild(QLineEdit, f"companion_{comp_field}_{companion_num}")
                    if comp_field_widget:
                        comp_field_widget.setProperty("invalid", "false" if is_valid else "true")
                        comp_field_widget.style().polish(comp_field_widget)
            return

        # Handle regular customer fields
        field = field_map.get(field_name)
        if field:
            field.setProperty("invalid", "false" if is_valid else "true")
            field.style().polish(field)

    def show_error(self, error_message: str):
        """Show error message to user."""
        QMessageBox.warning(self, "خطا", error_message)

    def show_field_error(self, field_name: str, error_message: str):
        """Show field-specific error."""
        # Could implement tooltip or status bar message
        self.show_error(f"{field_name}: {error_message}")

    def get_customer_data(self) -> Dict[str, Any]:
        """Get customer data from UI."""
        return {
            'national_id': self.national_id_le.text().strip(),
            'name': self.full_name_le.text().strip(),
            'phone': self.phone_le.text().strip(),
            'address': self.address_le.text().strip(),
            'email': self.email_le.text().strip(),
            'has_companions': self.has_companions_cb.isChecked()
        }

    def set_customer_data(self, data: Dict[str, Any]):
        """Set customer data in UI."""
        self.national_id_le.setText(data.get('national_id', ''))
        self.full_name_le.setText(data.get('name', '') or data.get('full_name', ''))
        self.phone_le.setText(data.get('phone', ''))
        self.address_le.setText(data.get('address', ''))
        self.email_le.setText(data.get('email', ''))
        self.has_companions_cb.setChecked(data.get('has_companions', False))

    def clear_form(self):
        """Clear all form fields."""
        self.national_id_le.clear()
        self.full_name_le.clear()
        self.phone_le.clear()
        self.address_le.clear()
        self.email_le.clear()
        self.has_companions_cb.setChecked(False)
        self.companions_count_sb.setValue(0)
        self.clear_companions()
        self.show_companions_group(False)

    def sync_companions_with_data(self, companions_data: List[Dict[str, Any]]):
        """Sync companion widgets with data."""
        # Clear existing companions
        self.clear_companions()

        # Add companions based on data
        for companion in companions_data:
            ui_number = companion.get('ui_number', 0)
            if ui_number > 0:
                self.add_companion_row(ui_number)

                # Set companion data
                if ui_number in self.companion_widgets:
                    widget = self.companion_widgets[ui_number]

                    name_field = widget.findChild(QLineEdit, f"companion_full_name_{ui_number}")
                    if name_field:
                        name_field.setText(companion.get('name', ''))

                    national_id_field = widget.findChild(QLineEdit, f"companion_national_id_{ui_number}")
                    if national_id_field:
                        national_id_field.setText(companion.get('national_id', ''))

                    phone_field = widget.findChild(QLineEdit, f"companion_phone_{ui_number}")
                    if phone_field:
                        phone_field.setText(companion.get('phone', ''))


class CustomerSelectionDialog(QDialog):
    """Dialog for selecting existing customers."""

    def __init__(self, customer_repository: ICustomerRepository, parent=None):
        """Initialize dialog with repository."""
        super().__init__(parent)
        self.customer_repository = customer_repository
        self.selected_customer = None

        # Initialize controller
        self.controller = CustomerDialogController(customer_repository, self)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("انتخاب مشتری")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("جستجو:")
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("نام، کد ملی یا شماره تماس را وارد کنید")

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_le)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Set columns
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["نام", "کد ملی", "شماره تماس", "ایمیل"])

        # Resize columns
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("انتخاب")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("انصراف")

        layout.addLayout(search_layout)
        layout.addWidget(self.results_table)
        layout.addWidget(button_box)

        # Connect button box
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def _connect_signals(self):
        """Connect dialog signals."""
        self.search_le.textChanged.connect(self.controller.search_customers)
        self.results_table.doubleClicked.connect(self._on_row_double_clicked)
        self.controller.search_results_changed.connect(self._update_results)

    def _update_results(self, customers: List[Dict[str, Any]]):
        """Update search results table."""
        self.results_table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            self.results_table.setItem(row, 0, QTableWidgetItem(customer.get('name', '')))
            self.results_table.setItem(row, 1, QTableWidgetItem(customer.get('national_id', '')))
            self.results_table.setItem(row, 2, QTableWidgetItem(customer.get('phone', '')))
            self.results_table.setItem(row, 3, QTableWidgetItem(customer.get('email', '')))

            # Store customer data in first item
            self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, customer)

    def _on_row_double_clicked(self):
        """Handle row double click."""
        self.accept()

    def accept(self):
        """Accept dialog and set selected customer."""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            item = self.results_table.item(current_row, 0)
            if item:
                self.selected_customer = item.data(Qt.ItemDataRole.UserRole)
        super().accept()

    def get_selected_customer(self) -> Optional[Dict[str, Any]]:
        """Get selected customer data."""
        return self.selected_customer


class CustomerManagementDialog(QDialog):
    """Dialog for customer management operations."""

    def __init__(self, customer_repository: ICustomerRepository, parent=None):
        """Initialize dialog with repository."""
        super().__init__(parent)
        self.customer_repository = customer_repository
        self.controller = CustomerManagementController(customer_repository, self)

        self._setup_ui()
        self._connect_signals()

        # Load initial data
        self.controller.load_all_customers()

    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("مدیریت مشتریان")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.new_btn = QPushButton("مشتری جدید")
        self.edit_btn = QPushButton("ویرایش")
        self.delete_btn = QPushButton("حذف")
        self.refresh_btn = QPushButton("بروزرسانی")

        # Search
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("جستجو...")

        toolbar_layout.addWidget(self.new_btn)
        toolbar_layout.addWidget(self.edit_btn)
        toolbar_layout.addWidget(self.delete_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("جستجو:"))
        toolbar_layout.addWidget(self.search_le)

        # Customers table
        self.customers_table = QTableWidget()
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Set columns
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels([
            "نام", "کد ملی", "شماره تماس", "ایمیل", "آدرس"
        ])

        # Close button
        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.close)

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.customers_table)
        layout.addWidget(close_btn)

    def _connect_signals(self):
        """Connect dialog signals."""
        self.search_le.textChanged.connect(self.controller.search_customers)
        self.controller.customers_loaded.connect(self._update_customers_table)
        self.controller.search_completed.connect(self._update_customers_table)
        self.controller.error_occurred.connect(self.show_error)

    def _update_customers_table(self, customers: List[Dict[str, Any]]):
        """Update customers table."""
        self.customers_table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            self.customers_table.setItem(row, 0, QTableWidgetItem(customer.get('name', '')))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer.get('national_id', '')))
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer.get('phone', '')))
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer.get('email', '')))
            self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get('address', '')))

    def show_error(self, error_message: str):
        """Show error message."""
        QMessageBox.warning(self, "خطا", error_message)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from features.InvoicePage.customer_info.customer_info_test import InMemoryCustomerRepository
    app = QApplication([])
    window = CustomerInfoView(InMemoryCustomerRepository, parent=None)
    window.show()
    sys.exit(app.exec())
