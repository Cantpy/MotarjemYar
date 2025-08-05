# -*- coding: utf-8 -*-
"""
View Layer - PySide6 UI Components for CustomerModel Information
Optimized for compactness and responsiveness
"""
import sys
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QSize, Signal, QRegularExpression
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSpacerItem, QSizePolicy, QFrame, QSpinBox, QScrollArea,
    QCheckBox, QMessageBox, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QTextEdit, QGridLayout
)

from features.InvoicePage.customer_info.customer_info_controller import (CustomerInfoController,
                                                                         CustomerManagementController,
                                                                         CustomerDialogController)
from features.InvoicePage.customer_info.customer_info_repo import ICustomerRepository


class CustomerInfoView(QWidget):
    """CustomerModel information view - first step of invoice creation."""

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
        """Setup the customer information UI - optimized for compactness with vertical stretch."""
        # Main layout with reduced margins
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)  # Reduced spacing
        main_layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins

        # Title - more compact
        title_frame = self._create_title_frame()
        main_layout.addWidget(title_frame)

        # Customer info group - reduced size
        self.customer_group = self._create_customer_group()
        main_layout.addWidget(self.customer_group)

        # Companions group - more compact but allows vertical stretch
        self.companions_group = self._create_companions_group()
        main_layout.addWidget(self.companions_group, 1)  # Stretch factor of 1

        # Initially hide companions group
        self.companions_group.setVisible(False)

        # Reduced spacer - only small minimum space
        main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))

        # Action buttons at bottom - more compact
        action_buttons_frame = self._create_bottom_action_buttons()
        main_layout.addWidget(action_buttons_frame)

    def _create_title_frame(self):
        """Create compact title frame."""
        title_frame = QFrame()
        title_frame.setObjectName("title_frame")

        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(5)
        title_layout.setContentsMargins(15, 10, 15, 10)

        # Main title
        title_label = QLabel("اطلاعات مشتری")
        title_label.setFont(self._get_font(14, bold=True))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("main_title")

        # Description
        desc_label = QLabel("لطفاً اطلاعات مشتری و همراهان را وارد کنید")
        desc_label.setFont(self._get_font(9))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setObjectName("description")

        title_layout.addWidget(title_label)
        title_layout.addWidget(desc_label)

        return title_frame

    def _create_customer_group(self):
        """Create customer information group - more compact."""
        group = QGroupBox("اطلاعات مشتری")
        group.setObjectName("customer_gb")
        group.setMinimumSize(QSize(0, 200))  # Reduced from 300
        group.setFont(self._get_font(11, bold=True))
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Group layout with reduced margins
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(15, 20, 15, 15)
        group_layout.setSpacing(15)

        # Input fields using grid layout for better responsiveness
        fields_layout = self._create_input_fields()
        group_layout.addLayout(fields_layout)

        return group

    def _create_companions_group(self):
        """Create companions information group - removed spinbox, improved spacing."""
        group = QGroupBox("اطلاعات همراهان")
        group.setObjectName("companions_gb")
        group.setMinimumSize(QSize(0, 200))  # Reduced minimum height
        # Remove maximum height to allow vertical stretching
        group.setFont(self._get_font(11, bold=True))
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Group layout with improved margins
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(15, 20, 15, 15)  # Better margins
        group_layout.setSpacing(12)  # Better spacing

        # Scroll area for companions - allows vertical expansion
        self.companions_scroll = QScrollArea()
        self.companions_scroll.setWidgetResizable(True)
        self.companions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.companions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.companions_scroll.setMinimumHeight(150)  # Slightly larger minimum height
        # No maximum height set - allows expansion
        self.companions_scroll.setObjectName("companions_scroll")

        # Companions container widget
        self.companions_container = QWidget()
        self.companions_layout = QVBoxLayout(self.companions_container)
        self.companions_layout.setSpacing(10)  # Better spacing between companions
        self.companions_layout.setContentsMargins(10, 10, 10, 10)  # Better margins

        # Add button - better styling
        self.add_companion_btn = QPushButton("➕ افزودن همراه")
        self.add_companion_btn.setObjectName("add_companion_btn")
        self.add_companion_btn.setFont(self._get_font(9))  # Slightly larger font
        self.add_companion_btn.setMinimumSize(QSize(0, 32))  # Better height
        self.add_companion_btn.setMaximumSize(QSize(16777215, 32))

        self.companions_layout.addWidget(self.add_companion_btn)
        self.companions_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.companions_scroll.setWidget(self.companions_container)
        group_layout.addWidget(self.companions_scroll)

        return group

    def _create_bottom_action_buttons(self):
        """Create compact action buttons."""
        buttons_frame = QFrame()
        buttons_frame.setObjectName("action_buttons_frame")

        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(12)
        buttons_layout.setContentsMargins(15, 10, 15, 10)

        # Add spacer to center buttons
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Add customer button - more compact
        self.add_customer_btn = QPushButton("ثبت مشتری")
        self.add_customer_btn.setObjectName("add_customer_btn")
        self.add_customer_btn.setMinimumSize(QSize(120, 35))  # Reduced from 140, 45
        self.add_customer_btn.setFont(self._get_font(10, bold=True))
        self.add_customer_btn.setToolTip("ثبت اطلاعات مشتری در پایگاه داده")

        # CustomerModel affairs button - more compact
        self.customer_affairs_btn = QPushButton("امور مشتریان")
        self.customer_affairs_btn.setObjectName("customer_affairs_btn")
        self.customer_affairs_btn.setMinimumSize(QSize(120, 35))  # Reduced from 140, 45
        self.customer_affairs_btn.setFont(self._get_font(10, bold=True))
        self.customer_affairs_btn.setToolTip("مدیریت امور مشتریان")

        buttons_layout.addWidget(self.add_customer_btn)
        buttons_layout.addWidget(self.customer_affairs_btn)

        # Add spacer to center buttons
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        return buttons_frame

    def _create_input_fields(self):
        """Create customer input fields using responsive grid layout."""
        # Use grid layout for better responsiveness
        fields_layout = QGridLayout()
        fields_layout.setSpacing(15)
        fields_layout.setVerticalSpacing(12)

        # Row 0: National ID, Full Name
        # National ID
        national_id_layout = self._create_field_layout("کد ملی *", True)
        self.national_id_le = QLineEdit()
        self.national_id_le.setObjectName("national_id_le")
        self.national_id_le.setFont(self._get_font(9))
        self.national_id_le.setPlaceholderText("کد ملی را وارد کنید")
        self.national_id_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.national_id_le.setMinimumSize(QSize(0, 28))
        national_id_layout.addWidget(self.national_id_le)

        # Full Name
        full_name_layout = self._create_field_layout("نام و نام خانوادگی *", True)
        self.full_name_le = QLineEdit()
        self.full_name_le.setObjectName("full_name_le")
        self.full_name_le.setFont(self._get_font(9))
        self.full_name_le.setPlaceholderText("نام و نام خانوادگی را وارد کنید")
        self.full_name_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.full_name_le.setMinimumSize(QSize(0, 28))
        full_name_layout.addWidget(self.full_name_le)

        # Row 1: Phone, Email
        # Phone
        phone_layout = self._create_field_layout("شماره تماس *", True)
        self.phone_le = QLineEdit()
        self.phone_le.setObjectName("phone_le")
        self.phone_le.setFont(self._get_font(9))
        self.phone_le.setPlaceholderText("شماره تماس را وارد کنید")
        self.phone_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.phone_le.setMinimumSize(QSize(0, 28))
        phone_layout.addWidget(self.phone_le)

        # Email
        email_layout = self._create_field_layout("ایمیل")
        self.email_le = QLineEdit()
        self.email_le.setObjectName("email_le")
        self.email_le.setFont(self._get_font(9))
        self.email_le.setPlaceholderText("ایمیل را وارد کنید")
        self.email_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.email_le.setMinimumSize(QSize(0, 28))
        email_layout.addWidget(self.email_le)

        # Row 2: Address (full width)
        address_layout = self._create_field_layout("آدرس")
        self.address_le = QLineEdit()
        self.address_le.setObjectName("address_le")
        self.address_le.setFont(self._get_font(9))
        self.address_le.setPlaceholderText("آدرس را وارد کنید")
        self.address_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.address_le.setMinimumSize(QSize(0, 28))
        address_layout.addWidget(self.address_le)

        # Row 3: Companions checkbox
        # Has companions checkbox
        self.has_companions_cb = QCheckBox("آیا همراه دارید؟")
        self.has_companions_cb.setObjectName("has_companions_cb")
        self.has_companions_cb.setFont(self._get_font(9))

        # Add to grid
        fields_layout.addLayout(national_id_layout, 0, 0)
        fields_layout.addLayout(full_name_layout, 0, 1)
        fields_layout.addLayout(phone_layout, 1, 0)
        fields_layout.addLayout(email_layout, 1, 1)
        fields_layout.addLayout(address_layout, 2, 0, 1, 2)  # Span 2 columns
        fields_layout.addWidget(self.has_companions_cb, 3, 0, 1, 2)  # Span 2 columns

        # Set column stretch for responsiveness
        fields_layout.setColumnStretch(0, 1)
        fields_layout.setColumnStretch(1, 1)

        return fields_layout

    def _create_field_layout(self, label_text: str, required: bool = False):
        """Create a compact field layout with label."""
        layout = QVBoxLayout()
        layout.setSpacing(3)  # Reduced spacing

        # Label
        label = QLabel(label_text)
        label.setFont(self._get_font(9, bold=True))  # Smaller font
        label.setObjectName("field_label")
        if required:
            label.setProperty("required", True)

        layout.addWidget(label)
        return layout

    def _create_companion_widget(self, companion_num: int):
        """Create widget for a single companion with better spacing."""
        companion_frame = QFrame()
        companion_frame.setObjectName(f"companion_frame_{companion_num}")
        companion_frame.setMinimumHeight(120)
        companion_frame.setMaximumHeight(140)

        companion_layout = QVBoxLayout(companion_frame)
        companion_layout.setSpacing(8)  # Increased spacing
        companion_layout.setContentsMargins(12, 10, 12, 10)  # Better margins

        # Header with companion number and delete button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)  # Better spacing

        companion_title = QLabel(f"همراه {companion_num}")
        companion_title.setFont(self._get_font(9, bold=True))  # Slightly larger font
        companion_title.setObjectName("companion_title")

        delete_btn = QPushButton("✕")
        delete_btn.setObjectName(f"delete_companion_{companion_num}")
        delete_btn.setMinimumSize(QSize(24, 24))  # Slightly larger delete button
        delete_btn.setMaximumSize(QSize(24, 24))
        delete_btn.setFont(self._get_font(11, bold=True))
        delete_btn.setProperty("companion_num", companion_num)
        delete_btn.clicked.connect(lambda: self.controller.on_delete_companion_clicked(companion_num))

        header_layout.addWidget(companion_title)
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        header_layout.addWidget(delete_btn)

        # Companion fields - horizontal layout with better spacing
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(15)  # Better spacing between fields

        # National ID - better spacing
        national_id_layout = QVBoxLayout()
        national_id_layout.setSpacing(4)  # Better spacing
        national_id_label = QLabel("کد ملی")
        national_id_label.setFont(self._get_font(8, bold=True))  # Slightly larger font
        national_id_label.setObjectName("companion_field_label")

        national_id_le = QLineEdit()
        national_id_le.setObjectName(f"companion_national_id_{companion_num}")
        national_id_le.setFont(self._get_font(9))  # Slightly larger font
        national_id_le.setPlaceholderText("کد ملی")
        national_id_le.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        national_id_le.setMinimumSize(QSize(0, 26))  # Better height
        national_id_le.setMaximumSize(QSize(16777215, 26))
        national_id_le.textChanged.connect(
            lambda text: self.controller.on_companion_field_changed(companion_num, 'national_id', text))

        national_id_layout.addWidget(national_id_label)
        national_id_layout.addWidget(national_id_le)

        # Full Name - better spacing
        full_name_layout = QVBoxLayout()
        full_name_layout.setSpacing(4)  # Better spacing
        full_name_label = QLabel("نام و نام خانوادگی")
        full_name_label.setFont(self._get_font(8, bold=True))  # Slightly larger font
        full_name_label.setObjectName("companion_field_label")

        full_name_le = QLineEdit()
        full_name_le.setObjectName(f"companion_full_name_{companion_num}")
        full_name_le.setFont(self._get_font(9))  # Slightly larger font
        full_name_le.setPlaceholderText("نام و نام خانوادگی")
        full_name_le.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        full_name_le.setMinimumSize(QSize(0, 26))  # Better height
        full_name_le.setMaximumSize(QSize(16777215, 26))
        full_name_le.textChanged.connect(
            lambda text: self.controller.on_companion_field_changed(companion_num, 'name', text))

        full_name_layout.addWidget(full_name_label)
        full_name_layout.addWidget(full_name_le)

        fields_layout.addLayout(national_id_layout)
        fields_layout.addLayout(full_name_layout)

        companion_layout.addLayout(header_layout)
        companion_layout.addLayout(fields_layout)

        return companion_frame

    def _connect_signals(self):
        """Connect UI signals to controller methods."""
        # CustomerModel fields
        self.national_id_le.textChanged.connect(self.controller.on_national_id_changed)
        self.full_name_le.textChanged.connect(self.controller.on_full_name_changed)
        self.phone_le.textChanged.connect(self.controller.on_phone_changed)
        self.address_le.textChanged.connect(self.controller.on_address_changed)
        self.email_le.textChanged.connect(self.controller.on_email_changed)

        # Companions - removed spinbox connection
        self.has_companions_cb.toggled.connect(self.controller.on_has_companions_changed)
        self.add_companion_btn.clicked.connect(self.controller.on_add_companion_clicked)
        self.controller.companions_refreshed.connect(self.sync_companions_with_data)
        self.controller.customer_saved.connect(self._on_customer_saved)

        # Action buttons
        self.add_customer_btn.clicked.connect(self._on_add_customer_clicked)
        self.customer_affairs_btn.clicked.connect(self._on_customer_affairs_clicked)

        # Controller signals
        self.controller.data_changed.connect(self.data_changed)
        self.controller.validation_changed.connect(self.validation_changed)
        self.controller.companions_visibility_changed.connect(self.show_companions_group)
        self.controller.field_validation_changed.connect(self.set_field_validation)
        self.controller.error_occurred.connect(self.show_error)
        self.controller.customer_loaded.connect(self._on_customer_loaded)

    def _setup_styles(self):
        """Setup component styles - optimized for compactness with better companion spacing."""
        self.setStyleSheet("""
            /* Title Frame - more compact */
            QFrame#title_frame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
            }

            QLabel#main_title {
                color: #333;
                margin-bottom: 3px;
            }

            QLabel#description {
                color: #666;
                border: none;
                padding: 3px;
            }

            /* Group Boxes - more compact */
            QGroupBox {
                border: 2px solid #ddd;
                border-radius: 6px;
                margin: 3px;
                padding-top: 12px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 6px 0 6px;
                color: #333;
            }

            /* Companions Group Box - allows stretching */
            QGroupBox#companions_gb {
                border: 2px solid #007bff;
                border-radius: 6px;
                margin: 3px;
                padding-top: 12px;
            }

            /* Action Buttons Frame - more compact */
            QFrame#action_buttons_frame {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin: 3px 0;
            }

            /* Buttons - more compact */
            QPushButton#add_customer_btn {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }

            QPushButton#add_customer_btn:hover {
                background-color: #218838;
            }

            QPushButton#add_customer_btn:pressed {
                background-color: #1e7e34;
            }

            QPushButton#customer_affairs_btn {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }

            QPushButton#customer_affairs_btn:hover {
                background-color: #0056b3;
            }

            QPushButton#customer_affairs_btn:pressed {
                background-color: #004085;
            }

            QPushButton#add_companion_btn {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                margin: 4px 0;
                font-size: 9pt;
                font-weight: bold;
            }

            QPushButton#add_companion_btn:hover {
                background-color: #45a049;
            }

            /* Input Fields - more compact */
            QLineEdit {
                padding: 4px 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 80px;
            }

            QLineEdit:focus {
                border-color: #4CAF50;
            }

            QLineEdit[invalid="true"] {
                border-color: #f44336;
            }

            /* CheckBox - compact */
            QCheckBox {
                color: #333;
                spacing: 5px;
            }

            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }

            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }

            /* Scroll Area - compact */
            QScrollArea#companions_scroll {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }

            /* Companion Frames - better spacing */
            QFrame[objectName^="companion_frame_"] {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                margin: 4px 2px;
            }

            /* Labels - better spacing */
            QLabel#field_label {
                color: #333;
            }

            QLabel#field_label[required="true"] {
                color: #333;
                font-weight: bold;
            }

            QLabel#companion_field_label {
                color: #333;
                font-size: 8pt;
                margin-bottom: 2px;
            }

            QLabel#companion_title {
                color: #333;
                font-size: 9pt;
            }

            /* Delete companion buttons - better styling */
            QPushButton[objectName^="delete_companion_"] {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
            }

            QPushButton[objectName^="delete_companion_"]:hover {
                background-color: #c82333;
                transform: scale(1.05);
            }

            QPushButton[objectName^="delete_companion_"]:pressed {
                background-color: #bd2130;
                transform: scale(0.95);
            }

            /* Responsive adjustments */
            @media (max-width: 800px) {
                QLineEdit {
                    min-width: 60px;
                }

                QPushButton {
                    min-width: 80px;
                }
            }
        """)

    @staticmethod
    def _get_font(size: int, bold: bool = False) -> QFont:
        """Get a font with specified size and weight."""
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    # UI Event Handlers
    def _on_customer_saved(self):
        """Handle customer saved successfully."""
        QMessageBox.information(self, "موفقیت", "اطلاعات مشتری با موفقیت ذخیره شد")

    def _on_add_customer_clicked(self):
        """Handle add customer button click - save to database."""
        # Save customer and companions to database
        success = self.controller.save_customer()
        if success:
            # Optionally clear form after successful save
            reply = QMessageBox.question(
                self,
                "پیام",
                "اطلاعات با موفقیت ذخیره شد. آیا می‌خواهید فرم را پاک کنید؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_form()

    def _on_customer_affairs_clicked(self):
        """Handle customer affairs button click."""
        dialog = CustomerManagementDialog(self.customer_repository, self)
        dialog.exec()

    def _on_customer_loaded(self, customer_data: Dict[str, Any]):
        """Handle customer loaded signal from controller."""
        if customer_data:
            self.set_customer_data(customer_data)

            # Handle companions data
            companions = customer_data.get('companions', [])
            if companions:
                self.sync_companions_with_data(companions)
                self.show_companions_group(True)

    # Public interface methods for controller
    def add_companion_row(self, companion_num: int):
        """Add a new companion row to the UI."""
        # Avoid duplicate companions
        if companion_num in self.companion_widgets:
            return

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

    def renumber_companion_widgets(self, companions_data: List[Dict[str, Any]]):
        """Renumber companion widgets to maintain sequential numbering."""
        # Clear existing widgets
        old_widgets = self.companion_widgets.copy()
        self.companion_widgets.clear()

        # Remove old widgets from layout
        for widget in old_widgets.values():
            widget.setParent(None)
            widget.deleteLater()

        # Create new widgets with correct numbering
        for i, companion in enumerate(companions_data, 1):
            companion_widget = self._create_companion_widget(i)
            self.companion_widgets[i] = companion_widget

            # Insert before the add button and spacer
            insert_index = self.companions_layout.count() - 2
            self.companions_layout.insertWidget(insert_index, companion_widget)

            # Set companion data
            name_field = companion_widget.findChild(QLineEdit, f"companion_full_name_{i}")
            if name_field:
                name_field.setText(companion.get('name', ''))

            national_id_field = companion_widget.findChild(QLineEdit, f"companion_national_id_{i}")
            if national_id_field:
                national_id_field.setText(companion.get('national_id', ''))

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
        self.clear_companions()
        self.show_companions_group(False)

    def sync_companions_with_data(self, companions_data: List[Dict[str, Any]]):
        """Sync companion widgets with data - uses renumbering for proper sequencing."""
        self.renumber_companion_widgets(companions_data)

    def resizeEvent(self, event):
        """Handle window resize for responsiveness."""
        super().resizeEvent(event)

        # Adjust layout based on window width
        width = self.width()

        # For very narrow windows, stack fields vertically
        if width < 600:
            # Find the grid layout and adjust column spans
            for i in range(self.customer_group.layout().count()):
                item = self.customer_group.layout().itemAt(i)
                if hasattr(item, 'layout') and isinstance(item.layout(), QGridLayout):
                    grid = item.layout()
                    # Make all fields span full width on narrow screens
                    for row in range(grid.rowCount()):
                        for col in range(grid.columnCount()):
                            item = grid.itemAtPosition(row, col)
                            if item and item.layout():
                                # This would require more complex responsive logic
                                pass


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
