# -*- coding: utf-8 -*-
"""
Customer Information UI - Step 1 of invoice creation
"""
import sys

from PySide6.QtCore import Qt, QSize, Signal, QRegularExpression
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy, QFrame, QSpinBox, QScrollArea,
    QCheckBox
)

from features.InvoicePage.controller.customer_info_controller import CustomerInfoController


class CustomerInfoUI(QWidget):
    """Customer information page - first step of invoice creation."""

    # Signals
    data_changed = Signal(dict)
    validation_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomerInfoUI")
        self.companion_layouts = []  # Store companion layouts for management

        # Initialize controller
        self.controller = CustomerInfoController(self)

        self._setup_ui()
        self._connect_signals()

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
        title_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(10)

        # Main title
        title_label = QLabel("اطلاعات مشتری")
        title_label.setFont(self._get_font(16, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #333; margin-bottom: 10px;")

        # Description
        desc_label = QLabel("لطفاً اطلاعات مشتری و همراهان را به صورت کامل وارد کنید")
        desc_label.setFont(self._get_font(10))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #666; border: none; padding: 10px")

        title_layout.addWidget(title_label)
        title_layout.addWidget(desc_label)

        return title_frame

    def _create_customer_group(self):
        """Create customer information group."""
        group = QGroupBox("اطلاعات مشتری")
        group.setObjectName("customer_gb")
        group.setMinimumSize(QSize(0, 300))
        group.setFont(self._get_font(12, bold=True))
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group.setStyleSheet("""
            QGroupBox {
                /* background-color: white; */
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
        """)

        # Group layout
        group_layout = QHBoxLayout(group)
        group_layout.setContentsMargins(20, 30, 20, 30)
        group_layout.setSpacing(40)

        # Action buttons
        buttons_layout = self._create_action_buttons()

        # Input fields
        fields_layout = self._create_input_fields()

        # Add to group layout
        group_layout.addLayout(buttons_layout)
        group_layout.addLayout(fields_layout)

        return group

    def _create_companions_group(self):
        """Create companions information group."""
        group = QGroupBox("اطلاعات همراهان")
        group.setObjectName("companions_gb")
        group.setMinimumSize(QSize(0, 350))  # Increased height
        group.setMaximumSize(QSize(16777215, 450))  # Set maximum height
        group.setFont(self._get_font(12, bold=True))
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        group.setStyleSheet("""
            QGroupBox {
                /* background-color: white; */
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
        """)

        # Group layout
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(20, 30, 20, 30)
        group_layout.setSpacing(15)

        # Number of companions input
        companions_count_layout = QHBoxLayout()
        companions_count_layout.setSpacing(10)

        companions_count_label = QLabel("تعداد همراهان:")
        companions_count_label.setFont(self._get_font(10, bold=True))
        companions_count_label.setStyleSheet("color: #333;")

        self.companions_count_sb = QSpinBox()
        self.companions_count_sb.setObjectName("companions_count_sb")
        self.companions_count_sb.setMinimum(0)
        self.companions_count_sb.setMaximum(20)
        self.companions_count_sb.setValue(0)
        self.companions_count_sb.setFont(self._get_font(10))
        self.companions_count_sb.setStyleSheet("""
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
        """)

        companions_count_layout.addWidget(companions_count_label)
        companions_count_layout.addWidget(self.companions_count_sb)
        companions_count_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Scroll area for companions
        self.companions_scroll = QScrollArea()
        self.companions_scroll.setWidgetResizable(True)
        self.companions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.companions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.companions_scroll.setMinimumHeight(200)  # Set minimum height for scroll area
        self.companions_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        # Companions container widget
        self.companions_container = QWidget()
        self.companions_layout = QVBoxLayout(self.companions_container)
        self.companions_layout.setSpacing(10)
        self.companions_layout.setContentsMargins(10, 10, 10, 10)

        # Add button at the bottom
        self.add_companion_btn = QPushButton("➕ افزودن همراه")
        self.add_companion_btn.setObjectName("add_companion_btn")
        self.add_companion_btn.setFont(self._get_font(10))
        self.add_companion_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                margin: 10px 0;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

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
        self.add_customer_btn.setObjectName("invoice_button_add_customer")
        self.add_customer_btn.setMinimumSize(QSize(120, 45))
        self.add_customer_btn.setFont(self._get_font(10))
        self.add_customer_btn.setToolTip("افزودن مشتری جدید")
        self.add_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Delete customer button
        self.delete_customer_btn = QPushButton("حذف مشتری")
        self.delete_customer_btn.setObjectName("invoice_button_delete_customer")
        self.delete_customer_btn.setMinimumSize(QSize(120, 45))
        self.delete_customer_btn.setFont(self._get_font(10))
        self.delete_customer_btn.setToolTip("حذف مشتری")
        self.delete_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        # Customer affairs button
        self.customer_affairs_btn = QPushButton("امور مشتریان")
        self.customer_affairs_btn.setObjectName("invoice_button_customer_affairs")
        self.customer_affairs_btn.setMinimumSize(QSize(120, 45))
        self.customer_affairs_btn.setFont(self._get_font(10))
        self.customer_affairs_btn.setToolTip("امور مشتریان")
        self.customer_affairs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

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
        self.national_id_le.setStyleSheet("""
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
        """)
        national_id_layout.addWidget(self.national_id_le)

        # Full Name
        full_name_layout = self._create_field_layout("نام و نام خانوادگی *", True)
        self.full_name_le = QLineEdit()
        self.full_name_le.setObjectName("full_name_le")
        self.full_name_le.setFont(self._get_font(10))
        self.full_name_le.setPlaceholderText("نام و نام خانوادگی را وارد کنید")
        self.full_name_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.full_name_le.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QLineEdit[invalid="true"] {
                border-color: #f44336;
            }
        """)
        full_name_layout.addWidget(self.full_name_le)

        # Phone
        phone_layout = self._create_field_layout("شماره تماس *", True)
        self.phone_le = QLineEdit()
        self.phone_le.setObjectName("phone_le")
        self.phone_le.setFont(self._get_font(10))
        self.phone_le.setPlaceholderText("شماره تماس را وارد کنید")
        self.phone_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.phone_le.setStyleSheet("""
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
        """)
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
        self.address_le.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 250px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        address_layout.addWidget(self.address_le)

        # Email
        email_layout = self._create_field_layout("ایمیل")
        self.email_le = QLineEdit()
        self.email_le.setObjectName("email_le")
        self.email_le.setFont(self._get_font(10))
        self.email_le.setPlaceholderText("ایمیل را وارد کنید")
        self.email_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.email_le.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
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
        self.has_companions_cb.setStyleSheet("""
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
            QCheckBox::indicator:checked::before {
                content: "✓";
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)

        third_row.addWidget(self.has_companions_cb)
        third_row.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        fields_layout.addLayout(first_row)
        fields_layout.addLayout(second_row)
        fields_layout.addLayout(third_row)

        return fields_layout

    def _create_field_layout(self, label_text, required=False):
        """Create a field layout with label and input."""
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Label
        label = QLabel(label_text)
        label.setFont(self._get_font(10, bold=True))
        label.setStyleSheet("color: #333;")
        if required:
            label.setStyleSheet("color: #333; font-weight: bold;")

        layout.addWidget(label)
        return layout

    def _create_companion_layout(self, companion_num):
        """Create layout for a single companion."""
        companion_frame = QFrame()
        companion_frame.setObjectName(f"companion_frame_{companion_num}")
        companion_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }
        """)

        companion_layout = QVBoxLayout(companion_frame)
        companion_layout.setSpacing(10)
        companion_layout.setContentsMargins(15, 15, 15, 15)

        # Header with companion number and delete button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        companion_title = QLabel(f"همراه {companion_num}")
        companion_title.setFont(self._get_font(10, bold=True))
        companion_title.setStyleSheet("color: #333;")

        delete_btn = QPushButton("❌")
        delete_btn.setObjectName(f"delete_companion_{companion_num}")
        delete_btn.setMinimumSize(QSize(30, 30))
        delete_btn.setMaximumSize(QSize(30, 30))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

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
        national_id_label.setStyleSheet("color: #333;")

        national_id_le = QLineEdit()
        national_id_le.setObjectName(f"companion_national_id_{companion_num}")
        national_id_le.setFont(self._get_font(9))
        national_id_le.setPlaceholderText("کد ملی")
        national_id_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        national_id_le.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
                min-width: 120px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)

        national_id_layout.addWidget(national_id_label)
        national_id_layout.addWidget(national_id_le)

        # Full Name
        full_name_layout = QVBoxLayout()
        full_name_layout.setSpacing(5)
        full_name_label = QLabel("نام و نام خانوادگی")
        full_name_label.setFont(self._get_font(9, bold=True))
        full_name_label.setStyleSheet("color: #333;")

        full_name_le = QLineEdit()
        full_name_le.setObjectName(f"companion_full_name_{companion_num}")
        full_name_le.setFont(self._get_font(9))
        full_name_le.setPlaceholderText("نام و نام خانوادگی")
        full_name_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        full_name_le.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
                min-width: 150px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)

        full_name_layout.addWidget(full_name_label)
        full_name_layout.addWidget(full_name_le)

        # Phone
        phone_layout = QVBoxLayout()
        phone_layout.setSpacing(5)
        phone_label = QLabel("شماره تماس")
        phone_label.setFont(self._get_font(9, bold=True))
        phone_label.setStyleSheet("color: #333;")

        phone_le = QLineEdit()
        phone_le.setObjectName(f"companion_phone_{companion_num}")
        phone_le.setFont(self._get_font(9))
        phone_le.setPlaceholderText("شماره تماس")
        phone_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        phone_le.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
                min-width: 120px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)

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
        # Customer fields - connect to the new controller methods
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
        self.add_customer_btn.clicked.connect(self.controller.on_add_customer_clicked)
        self.delete_customer_btn.clicked.connect(self.controller.on_delete_customer_clicked)
        self.customer_affairs_btn.clicked.connect(self.controller.on_customer_affairs_clicked)

        # Controller signals
        self.controller.data_changed.connect(self.data_changed)
        self.controller.validation_changed.connect(self.validation_changed)
        self.controller.companions_visibility_changed.connect(self.show_companions_group)
        self.controller.companions_count_changed.connect(self.update_companions_count)
        self.controller.field_validation_changed.connect(self.set_field_validation)

    def _get_font(self, size, bold=False):
        """Get a font with specified size and weight."""
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def add_companion_row(self, companion_num):
        """Add a new companion row to the UI."""
        companion_frame = self._create_companion_layout(companion_num)

        # Insert before the add button and spacer
        insert_index = self.companions_layout.count() - 2
        self.companions_layout.insertWidget(insert_index, companion_frame)

        # Connect delete button
        delete_btn = companion_frame.findChild(QPushButton, f"delete_companion_{companion_num}")
        if delete_btn:
            delete_btn.clicked.connect(lambda: self.controller.on_delete_companion_clicked(companion_num))

        # Connect companion fields
        national_id_le = companion_frame.findChild(QLineEdit, f"companion_national_id_{companion_num}")
        full_name_le = companion_frame.findChild(QLineEdit, f"companion_full_name_{companion_num}")
        phone_le = companion_frame.findChild(QLineEdit, f"companion_phone_{companion_num}")

        if national_id_le:
            national_id_le.textChanged.connect(
                lambda text: self.controller.on_companion_field_changed(companion_num, 'national_id', text))
        if full_name_le:
            full_name_le.textChanged.connect(
                lambda text: self.controller.on_companion_field_changed(companion_num, 'full_name', text))
        if phone_le:
            phone_le.textChanged.connect(
                lambda text: self.controller.on_companion_field_changed(companion_num, 'phone', text))

    def remove_companion_row(self, companion_num):
        """Remove a companion row from the UI."""
        companion_frame = self.companions_container.findChild(QFrame, f"companion_frame_{companion_num}")
        if companion_frame:
            companion_frame.deleteLater()

    def clear_companions(self):
        """Clear all companion rows."""
        # Find all companion frames and remove them
        companion_frames = self.companions_container.findChildren(QFrame, QRegularExpression("companion_frame_\\d+"))
        for frame in companion_frames:
            frame.deleteLater()

    def show_companions_group(self, show=True):
        """Show or hide the companions group."""
        self.companions_group.setVisible(show)

    def update_companions_count(self, count):
        """Update the companions count spinbox."""
        self.companions_count_sb.setValue(count)

    def get_customer_data(self):
        """Get customer data from UI."""
        return {
            'national_id': self.national_id_le.text().strip(),
            'full_name': self.full_name_le.text().strip(),
            'phone': self.phone_le.text().strip(),
            'address': self.address_le.text().strip(),
            'email': self.email_le.text().strip(),
            'has_companions': self.has_companions_cb.isChecked()
        }

    def get_companions_data(self):
        """Get companions data from UI."""
        companions = []
        companion_frames = self.companions_container.findChildren(QFrame, QRegularExpression("companion_frame_\\d+"))

        for frame in companion_frames:
            companion_num = frame.objectName().split('_')[-1]

            national_id_le = frame.findChild(QLineEdit, f"companion_national_id_{companion_num}")
            full_name_le = frame.findChild(QLineEdit, f"companion_full_name_{companion_num}")
            phone_le = frame.findChild(QLineEdit, f"companion_phone_{companion_num}")

            if national_id_le and full_name_le and phone_le:
                companions.append({
                    'national_id': national_id_le.text().strip(),
                    'full_name': full_name_le.text().strip(),
                    'phone': phone_le.text().strip()
                })

        return companions

    def set_customer_data(self, data):
        """Set customer data in UI."""
        self.national_id_le.setText(data.get('national_id', ''))
        self.full_name_le.setText(data.get('full_name', ''))
        self.phone_le.setText(data.get('phone', ''))
        self.address_le.setText(data.get('address', ''))
        self.email_le.setText(data.get('email', ''))
        self.has_companions_cb.setChecked(data.get('has_companions', False))

    def set_field_validation(self, field_name, is_valid):
        """Set validation state for a field."""
        field_map = {
            'national_id': self.national_id_le,
            'full_name': self.full_name_le,
            'phone': self.phone_le,
            'address': self.address_le,
            'email': self.email_le
        }

        field = field_map.get(field_name)
        if field:
            field.setProperty("invalid", "false" if is_valid else "true")
            field.style().polish(field)

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


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = CustomerInfoUI()
    widget.show()
    sys.exit(app.exec())
