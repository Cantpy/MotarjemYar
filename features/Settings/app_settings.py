import sys
import os
import shutil
import sqlite3
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from modules.helper_functions import (return_resource, show_question_message_box, show_error_message_box,
                                      show_warning_message_box, show_information_message_box)
import datetime

# Assuming DB_PATH is defined somewhere in your project
DB_PATH = return_resource("databases", "invoices.db")


class FontManager:
    """Manages font sizing hierarchy for different UI elements"""

    def __init__(self, base_size=10):
        self.base_size = base_size
        self.size_ratios = {
            'title': 1.6,  # Main titles (16pt when base is 10pt)
            'header': 1.3,  # Section headers (13pt when base is 10pt)
            'subheader': 1.1,  # Sub headers (11pt when base is 10pt)
            'normal': 1.0,  # Normal text (10pt when base is 10pt)
            'small': 0.9,  # Small text (9pt when base is 10pt)
            'button': 1.0,  # Button text (10pt when base is 10pt)
            'table_header': 1.0,  # Table headers (10pt when base is 10pt)
            'table_cell': 0.95,  # Table cells (9.5pt when base is 10pt)
        }

    def get_font(self, font_family, element_type='normal', bold=False):
        """Get font for specific element type"""
        size = int(self.base_size * self.size_ratios.get(element_type, 1.0))
        font = QFont(font_family, size)
        font.setBold(bold)
        return font

    def update_base_size(self, new_base_size):
        """Update base font size"""
        self.base_size = new_base_size

    def apply_fonts_to_widget(self, widget, font_family):
        """Apply appropriate fonts to a widget and its children"""
        self._apply_fonts_recursive(widget, font_family)

    def _apply_fonts_recursive(self, widget, font_family):
        """Recursively apply fonts to widget hierarchy"""
        if not widget:
            return

        # Skip QFontComboBox to prevent interference
        if isinstance(widget, QFontComboBox):
            return

        # Determine element type based on widget class and properties
        element_type = self._determine_element_type(widget)

        # Apply font
        font = self.get_font(font_family, element_type)
        widget.setFont(font)

        # Process children
        for child in widget.children():
            if isinstance(child, QWidget):
                self._apply_fonts_recursive(child, font_family)

    def _determine_element_type(self, widget):
        """Determine the element type based on widget characteristics"""
        if isinstance(widget, QPushButton):
            return 'button'
        elif isinstance(widget, QLabel):
            # Check if it's a title or header based on font properties or text content
            current_font = widget.font()
            if current_font.bold() and current_font.pointSize() > 12:
                return 'title'
            elif current_font.bold():
                return 'header'
            else:
                return 'normal'
        elif isinstance(widget, QGroupBox):
            return 'header'
        elif isinstance(widget, QHeaderView) or (hasattr(widget, 'horizontalHeader') and widget.horizontalHeader()):
            return 'table_header'
        elif isinstance(widget, (QTableWidget, QTableView)):
            return 'table_cell'
        elif isinstance(widget, (QComboBox, QLineEdit, QSpinBox, QCheckBox)):
            return 'normal'
        else:
            return 'normal'


class AppSettings(QWidget):
    scale_changed = Signal(float)
    theme_changed = Signal(str)
    backup_created = Signal(str)
    font_changed = Signal(str)  # only font_family now

    def __init__(self, parent=None):
        super().__init__(parent)

        # Settings objects
        self.preview_settings = QSettings("MyScale", "MyPreview")
        self.theme_settings = QSettings("AppTheme", "CurrentTheme")
        self.invoice_settings = QSettings("InvoiceSettings", "Settings")
        self.app_settings = QSettings("AppSettings", "General")

        # Font manager
        self.font_manager = FontManager()

        self.setup_ui()
        self.setup_connections()
        self.load_saved_settings()

    def setup_ui(self):
        """Setup the user interface"""
        # Set RTL layout for Persian
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main scroll area for better handling of maximized window
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content widget inside scroll area
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)

        # Main layout for the entire widget
        main_widget_layout = QVBoxLayout(self)
        main_widget_layout.setContentsMargins(0, 0, 0, 0)
        main_widget_layout.addWidget(scroll_area)

        # Content layout with proper constraints
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Container for all content with maximum width
        container_widget = QWidget()
        container_widget.setMaximumWidth(800)  # Limit width for better appearance
        container_layout = QVBoxLayout(container_widget)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QLabel("تنظیمات برنامه")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)  # Larger size for title
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setProperty('elementType', 'title')  # Custom property for font management
        container_layout.addWidget(title_label)

        # Create sections
        self.create_invoice_section(container_layout)
        self.create_theme_section(container_layout)
        self.create_display_section(container_layout)
        self.create_backup_section(container_layout)
        self.create_advanced_section(container_layout)

        # Add stretch to push everything up
        container_layout.addStretch()

        # Apply/Reset buttons
        self.create_button_section(container_layout)

        # Center the container in the content widget
        content_layout.addStretch()
        content_layout.addWidget(container_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        content_layout.addStretch()

    def apply_saved_theme(self):
        """Apply saved theme on startup"""
        theme_name = self.theme_settings.value("theme", "بهاری")
        self.theme_changed.emit(theme_name)

        # Also apply saved font settings to entire app
        self.apply_saved_font()

    def apply_saved_font(self):
        """Apply saved font settings to the entire application"""
        saved_font_family = self.app_settings.value("font_family", "IranSANS")

        # Apply to entire application
        app_instance = QApplication.instance()
        if app_instance:
            # Set base font for application
            base_font = QFont(saved_font_family)
            app_instance.setFont(base_font)

            # Apply hierarchical fonts to all widgets
            for widget in app_instance.allWidgets():
                if widget and isinstance(widget, QWidget):
                    self.font_manager.apply_fonts_to_widget(widget, saved_font_family)

                    # Special handling for IranNastaliq font
                    if saved_font_family == "IranNastaliq":
                        current_font = widget.font()
                        current_font.setPointSize(current_font.pointSize() + 4)
                        widget.setFont(current_font)

        # Emit signal for any additional handling
        self.font_changed.emit(saved_font_family)

    def create_invoice_section(self, parent_layout):
        """Create invoice settings section"""
        group_box = QGroupBox("تنظیمات فاکتور")
        group_box.setProperty('elementType', 'header')
        group_layout = QFormLayout(group_box)
        group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Invoice number spinbox with apply button
        invoice_number_layout = QHBoxLayout()
        self.invoice_number_spinbox = QSpinBox()
        self.invoice_number_spinbox.setRange(1, 999999)
        self.invoice_number_spinbox.setValue(1)
        self.invoice_number_spinbox.setToolTip("شماره اولیه فاکتور که به صورت خودکار افزایش می‌یابد")

        self.apply_invoice_number_btn = QPushButton("اعمال")
        self.apply_invoice_number_btn.setMaximumWidth(80)
        self.apply_invoice_number_btn.setToolTip("اعمال شماره اولیه فاکتور")

        invoice_number_layout.addWidget(self.invoice_number_spinbox)
        invoice_number_layout.addWidget(self.apply_invoice_number_btn)
        group_layout.addRow("شماره اولیه فاکتور:", invoice_number_layout)

        # Invoice preview scale combobox
        self.invoice_preview_cb = QComboBox()
        self.invoice_preview_cb.addItems(["کوچک (75%)", "متوسط (100%)", "بزرگ (125%)"])
        self.invoice_preview_cb.setToolTip("اندازه نمایش پیش‌نمای فاکتور")
        group_layout.addRow("اندازه پیش‌نمای فاکتور:", self.invoice_preview_cb)

        # Auto-save invoices
        self.auto_save_checkbox = QCheckBox("ذخیره خودکار فاکتورها")
        self.auto_save_checkbox.setToolTip("فاکتورها به صورت خودکار ذخیره شوند")
        group_layout.addRow("", self.auto_save_checkbox)

        # Saving format section (initially hidden)
        self.saving_format_group = QWidget()
        saving_format_layout = QFormLayout(self.saving_format_group)
        saving_format_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        saving_format_layout.setContentsMargins(20, 10, 0, 10)

        # Saving format combo
        self.saving_format_combo = QComboBox()
        self.saving_format_combo.addItems([
            "نام مشتری - تاریخ صدور - زمان",
            "شماره فاکتور - نام مشتری - تاریخ",
            "تاریخ - شماره فاکتور - نام مشتری",
            "نام مشتری - شماره فاکتور",
            "سفارشی"
        ])
        self.saving_format_combo.setToolTip("فرمت نام‌گذاری فایل‌های ذخیره شده")
        saving_format_layout.addRow("فرمت نام‌گذاری:", self.saving_format_combo)

        # Custom format input (initially hidden)
        self.custom_format_edit = QLineEdit()
        self.custom_format_edit.setPlaceholderText("مثال: {customer_name}_{invoice_number}_{date}")
        self.custom_format_edit.setToolTip("فرمت سفارشی برای نام‌گذاری فایل‌ها")
        self.custom_format_edit.setVisible(False)
        saving_format_layout.addRow("فرمت سفارشی:", self.custom_format_edit)

        # Auto-save directory selection
        directory_layout = QHBoxLayout()
        self.auto_save_directory_edit = QLineEdit()
        self.auto_save_directory_edit.setPlaceholderText("مسیر ذخیره خودکار...")
        self.auto_save_directory_edit.setReadOnly(True)
        self.auto_save_directory_edit.setToolTip("مسیر ذخیره خودکار فاکتورها")

        self.browse_auto_save_btn = QPushButton("انتخاب مسیر")
        self.browse_auto_save_btn.setMaximumWidth(100)

        directory_layout.addWidget(self.auto_save_directory_edit)
        directory_layout.addWidget(self.browse_auto_save_btn)
        saving_format_layout.addRow("مسیر ذخیره:", directory_layout)

        # Hide saving format group initially
        self.saving_format_group.setVisible(False)

        group_layout.addRow("", self.saving_format_group)
        parent_layout.addWidget(group_box)

    def create_theme_section(self, parent_layout):
        """Create theme settings section"""
        group_box = QGroupBox("تنظیمات ظاهری")
        group_box.setProperty('elementType', 'header')
        group_layout = QFormLayout(group_box)
        group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["بهاری", "تابستان", "پائیزه", "زمستان", "دراکولا"])
        self.theme_combo.setToolTip("انتخاب تم ظاهری برنامه")
        group_layout.addRow("تم برنامه:", self.theme_combo)

        # Font family
        self.font_family_combo = QFontComboBox()
        self.font_family_combo.setToolTip("انتخاب فونت برنامه")
        group_layout.addRow("نوع فونت:", self.font_family_combo)

        parent_layout.addWidget(group_box)

    def create_display_section(self, parent_layout):
        """Create display settings section"""
        group_box = QGroupBox("تنظیمات نمایش")
        group_box.setProperty('elementType', 'header')
        group_layout = QFormLayout(group_box)
        group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Show splash screen
        self.show_splash_checkbox = QCheckBox("نمایش صفحه خوش‌آمدگویی")
        self.show_splash_checkbox.setToolTip("نمایش صفحه خوش‌آمدگویی هنگام راه‌اندازی")
        group_layout.addRow("", self.show_splash_checkbox)

        # Minimize to tray
        self.minimize_to_tray_checkbox = QCheckBox("کوچک کردن به نوار وظیفه")
        self.minimize_to_tray_checkbox.setToolTip("برنامه را به نوار وظیفه منتقل کن")
        group_layout.addRow("", self.minimize_to_tray_checkbox)

        parent_layout.addWidget(group_box)

    def create_backup_section(self, parent_layout):
        """Create backup settings section"""
        group_box = QGroupBox("تنظیمات پشتیبان‌گیری")
        group_box.setProperty('elementType', 'header')
        group_layout = QVBoxLayout(group_box)

        # Auto backup
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.auto_backup_checkbox = QCheckBox("پشتیبان‌گیری خودکار")
        self.auto_backup_checkbox.setToolTip("ایجاد پشتیبان به صورت خودکار")
        form_layout.addRow("", self.auto_backup_checkbox)

        # Backup frequency
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["روزانه", "هفتگی", "ماهانه"])
        self.backup_frequency_combo.setToolTip("دوره زمانی پشتیبان‌گیری")
        form_layout.addRow("دوره پشتیبان‌گیری:", self.backup_frequency_combo)

        # Backup location
        backup_location_layout = QHBoxLayout()
        self.backup_location_edit = QLineEdit()
        self.backup_location_edit.setPlaceholderText("مسیر ذخیره پشتیبان...")
        self.backup_location_edit.setReadOnly(True)

        self.browse_backup_btn = QPushButton("انتخاب مسیر")
        self.browse_backup_btn.setMaximumWidth(100)

        backup_location_layout.addWidget(self.backup_location_edit)
        backup_location_layout.addWidget(self.browse_backup_btn)

        form_layout.addRow("مسیر پشتیبان:", backup_location_layout)

        group_layout.addLayout(form_layout)

        # Manual backup button
        self.manual_backup_btn = QPushButton("ایجاد پشتیبان دستی")
        self.manual_backup_btn.setToolTip("ایجاد فوری یک فایل پشتیبان")
        group_layout.addWidget(self.manual_backup_btn)

        parent_layout.addWidget(group_box)

    def create_advanced_section(self, parent_layout):
        """Create advanced settings section"""
        group_box = QGroupBox("تنظیمات پیشرفته")
        group_box.setProperty('elementType', 'header')
        group_layout = QFormLayout(group_box)
        group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Debug mode
        self.debug_mode_checkbox = QCheckBox("حالت اشکال‌زدایی")
        self.debug_mode_checkbox.setToolTip("فعال‌سازی لاگ‌های اشکال‌زدایی")
        group_layout.addRow("", self.debug_mode_checkbox)

        # Database optimization
        self.optimize_db_btn = QPushButton("بهینه‌سازی پایگاه داده")
        self.optimize_db_btn.setToolTip("بهینه‌سازی و فشرده‌سازی پایگاه داده")
        group_layout.addRow("", self.optimize_db_btn)

        # Reset all settings
        self.reset_all_btn = QPushButton("بازنشانی همه تنظیمات")
        self.reset_all_btn.setToolTip("بازگردانی همه تنظیمات به حالت پیش‌فرض")
        self.reset_all_btn.setStyleSheet("QPushButton { color: red; }")
        group_layout.addRow("", self.reset_all_btn)

        parent_layout.addWidget(group_box)

    def create_button_section(self, parent_layout):
        """Create apply/cancel buttons section"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_btn = QPushButton("اعمال تغییرات")
        self.apply_btn.setMinimumWidth(120)
        self.apply_btn.setProperty('elementType', 'button')
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.setProperty('elementType', 'button')
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.cancel_btn)

        parent_layout.addLayout(button_layout)

    def setup_connections(self):
        """Setup signal connections"""
        # Invoice settings - removed automatic saving signals
        self.apply_invoice_number_btn.clicked.connect(self.apply_invoice_number)
        self.auto_save_checkbox.toggled.connect(self.toggle_saving_format)
        self.saving_format_combo.currentTextChanged.connect(self.toggle_custom_format)
        self.browse_auto_save_btn.clicked.connect(self.browse_auto_save_directory)

        # Theme settings - removed automatic saving signals

        # Display settings - removed automatic saving signals

        # Backup settings - removed automatic saving signals
        self.browse_backup_btn.clicked.connect(self.browse_backup_location)
        self.manual_backup_btn.clicked.connect(self.create_manual_backup)

        # Advanced settings - removed automatic saving signals
        self.optimize_db_btn.clicked.connect(self.optimize_database)
        self.reset_all_btn.clicked.connect(self.reset_all_settings)

        # Buttons
        self.apply_btn.clicked.connect(self.apply_settings)
        self.cancel_btn.clicked.connect(self.reject_changes)

    def load_saved_settings(self):
        """Load all saved settings"""
        # Invoice settings
        self.invoice_number_spinbox.setValue(
            self.invoice_settings.value("initial_invoice_number", 1, type=int)
        )

        saved_scale = self.preview_settings.value("scaling_factor", "متوسط (100%)")
        self.invoice_preview_cb.setCurrentText(saved_scale)

        self.auto_save_checkbox.setChecked(
            self.invoice_settings.value("auto_save", False, type=bool)
        )

        # Auto-save format settings
        self.saving_format_combo.setCurrentText(
            self.invoice_settings.value("saving_format", "نام مشتری - تاریخ صدور - زمان")
        )

        self.custom_format_edit.setText(
            self.invoice_settings.value("custom_format", "")
        )

        self.auto_save_directory_edit.setText(
            self.invoice_settings.value("auto_save_directory", "")
        )

        # Theme settings
        saved_theme = self.theme_settings.value("theme", "بهاری")
        self.theme_combo.setCurrentText(saved_theme)

        # Load saved font family
        saved_font_family = self.app_settings.value("font_family", "Arial")
        font = QFont(saved_font_family)
        self.font_family_combo.setCurrentFont(font)

        # Display settings
        self.show_splash_checkbox.setChecked(
            self.app_settings.value("show_splash", True, type=bool)
        )

        self.minimize_to_tray_checkbox.setChecked(
            self.app_settings.value("minimize_to_tray", False, type=bool)
        )

        # Backup settings
        self.auto_backup_checkbox.setChecked(
            self.app_settings.value("auto_backup", False, type=bool)
        )

        self.backup_frequency_combo.setCurrentText(
            self.app_settings.value("backup_frequency", "هفتگی")
        )

        self.backup_location_edit.setText(
            self.app_settings.value("backup_location", "")
        )

        # Advanced settings
        self.debug_mode_checkbox.setChecked(
            self.app_settings.value("debug_mode", False, type=bool)
        )

        # Update UI state based on loaded settings
        self.toggle_saving_format()
        self.toggle_custom_format()

    def apply_invoice_number(self):
        """Apply invoice number change"""
        try:
            new_number = self.invoice_number_spinbox.value()

            # Check if DB_PATH is defined
            if 'DB_PATH' not in globals():
                title = "خطا"
                message = "مسیر پایگاه داده تعریف نشده است."
                show_warning_message_box(self, title, message)
                return

            with sqlite3.connect(DB_PATH) as connection:
                cursor = connection.cursor()

                # Check if there are any invoices in the database
                cursor.execute("SELECT COUNT(*) FROM issued_invoices")
                count = cursor.fetchone()[0]

                if count == 0:
                    # No invoices exist, we can safely set the initial number
                    self.invoice_settings.setValue("initial_invoice_number", new_number)
                    title = "موفقیت"
                    message = f"شماره اولیه فاکتور به {new_number} تغییر یافت."
                    show_information_message_box(self, title, message)
                else:
                    # There are existing invoices, show warning but still save
                    def set_invoice_number():
                        self.invoice_settings.setValue("initial_invoice_number", new_number)
                        title = "موفقیت"
                        message = f"شماره اولیه فاکتور به {new_number} تغییر یافت."
                        show_information_message_box(self, title, message)

                    title = "هشدار"
                    message = (f"در حال حاضر {count} فاکتور در پایگاه داده موجود است.\n"
                        f"شماره اولیه فاکتور فقط برای فاکتورهای جدید اعمال خواهد شد.\n"
                        f"آیا می‌خواهید شماره اولیه را به {new_number} تغییر دهید؟",)
                    button1 = "بله"
                    button2 = "خیر"
                    show_question_message_box(self, title, message, button1, set_invoice_number, button2)

        except sqlite3.Error as e:
            title = "خطا"
            message = (f"خطا در به‌روزرسانی پایگاه داده:\n"
                       f"{str(e)}")
            show_error_message_box(self, title, message)

        except Exception as e:
            title = "خطا"
            message = (f"خطای غیرمنتظره: \n"
                       f"{str(e)}")
            show_error_message_box(self, title, message)

    def toggle_saving_format(self):
        """Toggle saving format section visibility"""
        is_auto_save = self.auto_save_checkbox.isChecked()
        self.saving_format_group.setVisible(is_auto_save)

    def toggle_custom_format(self):
        """Toggle custom format input visibility"""
        is_custom = self.saving_format_combo.currentText() == "سفارشی"
        self.custom_format_edit.setVisible(is_custom)

    def browse_auto_save_directory(self):
        """Browse for auto-save directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "انتخاب مسیر ذخیره خودکار",
            self.auto_save_directory_edit.text()
        )

        if directory:
            self.auto_save_directory_edit.setText(directory)

    def save_scale(self):
        """Save invoice preview scale - only called from apply_settings"""
        scale_text = self.invoice_preview_cb.currentText()
        self.preview_settings.setValue("scaling_factor", scale_text)
        self.scale_changed.emit(self.get_scale_factor())

    def get_scale_factor(self):
        """Get numeric scale factor from combobox text"""
        scale_text = self.invoice_preview_cb.currentText()
        scale_map = {
            "کوچک (75%)": 0.75,
            "متوسط (100%)": 1.0,
            "بزرگ (125%)": 1.25
        }
        return scale_map.get(scale_text, 1.0)

    def show_restart_prompt(self):
        """Show restart prompt for theme changes"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("تغییر تم")
        msg_box.setText("برای اعمال کامل تغییرات تم، بازراه‌اندازی برنامه توصیه می‌شود.")
        msg_box.setInformativeText("آیا می‌خواهید برنامه را هم‌اکنون بازراه‌اندازی کنید؟")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # Persian button texts
        yes_btn = msg_box.button(QMessageBox.StandardButton.Yes)
        no_btn = msg_box.button(QMessageBox.StandardButton.No)
        cancel_btn = msg_box.button(QMessageBox.StandardButton.Cancel)

        yes_btn.setText("بله")
        no_btn.setText("خیر")
        cancel_btn.setText("انصراف")

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            # Restart application
            QApplication.quit()
            QProcess.startDetached(sys.executable, sys.argv)
        elif reply == QMessageBox.StandardButton.Cancel:
            return False  # Cancel the theme change

        return True  # Continue with theme change

    def save_theme(self):
        """Save theme setting - only called from apply_settings"""
        theme_name = self.theme_combo.currentText()
        self.theme_settings.setValue("theme", theme_name)
        self.theme_changed.emit(theme_name)

    def save_font_settings(self):
        """Save font settings - only called from apply_settings"""
        # Apply to entire application
        font_family = self.font_family_combo.currentFont().family()

        self.app_settings.setValue("font_family", font_family)

        # Apply to entire application
        app_instance = QApplication.instance()
        if app_instance:
            # Set base font for application
            base_font = QFont(font_family)
            app_instance.setFont(base_font)

            # Apply hierarchical fonts to all widgets
            for widget in app_instance.allWidgets():
                if widget and isinstance(widget, QWidget):
                    self.font_manager.apply_fonts_to_widget(widget, font_family)

                    # Special handling for IranNastaliq font
                    if font_family == "IranNastaliq":
                        current_font = widget.font()
                        current_font.setPointSize(current_font.pointSize() + 4)
                        widget.setFont(current_font)

        self.font_changed.emit(font_family)

    def browse_backup_location(self):
        """Browse for backup location"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "انتخاب مسیر پشتیبان‌گیری",
            self.backup_location_edit.text()
        )

        if directory:
            self.backup_location_edit.setText(directory)

    def create_manual_backup(self):
        """Create manual backup"""
        try:
            # Check if database exists
            if not os.path.exists(DB_PATH):
                title = "خطا"
                message = "فایل پایگاه داده یافت نشد."
                show_warning_message_box(self, title, message)
                return

            # Get backup location
            backup_location = self.backup_location_edit.text()
            if not backup_location:
                backup_location = QFileDialog.getExistingDirectory(
                    self,
                    "انتخاب مسیر ذخیره پشتیبان"
                )
                if not backup_location:
                    return

            # Create backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"invoice_backup_{timestamp}.db"
            backup_path = os.path.join(backup_location, backup_filename)

            # Copy database file
            shutil.copy2(DB_PATH, backup_path)

            # Emit signal
            self.backup_created.emit(backup_path)

            title = "موفقیت"
            message = f"پشتیبان با موفقیت ایجاد شد:\n{backup_path}"
            show_information_message_box(self, title, message)

        except Exception as e:
            title = "خطا"
            message = (f"خطا در ایجاد پشتیبان: \n"
                       f"{e}")
            show_error_message_box(self, title, message)

    def optimize_database(self):
        """Optimize database"""
        try:
            def database_optimization():
                progress = QProgressDialog("در حال بهینه‌سازی پایگاه داده...", "انصراف", 0, 0, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.show()

                # Connect to database and optimize
                with sqlite3.connect(DB_PATH) as connection:
                    cursor = connection.cursor()

                    # Vacuum database
                    cursor.execute("VACUUM")

                    # Analyze tables
                    cursor.execute("ANALYZE")

                    # Reindex
                    cursor.execute("REINDEX")

                progress.close()

                title = "موفقیت"
                message = "پایگاه داده با موفقیت بهینه‌سازی شد."
                show_information_message_box(self, title, message)

            # Show confirmation dialog
            title = "تأیید بهینه‌سازی"
            message = "آیا می‌خواهید پایگاه داده را بهینه‌سازی کنید؟\nاین عملیات ممکن است چند دقیقه طول بکشد."
            button1 = "بله"
            button2 = "خیر"
            show_question_message_box(self, title, message, button1, database_optimization, button2)

        except Exception as e:
            title = "خطا"
            message = f"خطا در بهینه‌سازی پایگاه داده:\n{str(e)}"
            show_error_message_box(self, title, message)


    def reset_all_settings(self):
        """Reset all settings to default"""

        def perform_reset():
            try:
                # Clear all settings
                self.preview_settings.clear()
                self.theme_settings.clear()
                self.invoice_settings.clear()
                self.app_settings.clear()

                # Reset UI to defaults
                self.invoice_number_spinbox.setValue(1)
                self.invoice_preview_cb.setCurrentText("متوسط (100%)")
                self.auto_save_checkbox.setChecked(False)
                self.saving_format_combo.setCurrentText("نام مشتری - تاریخ صدور - زمان")
                self.custom_format_edit.clear()
                self.auto_save_directory_edit.clear()
                self.theme_combo.setCurrentText("بهاری")
                self.font_family_combo.setCurrentFont(QFont("Arial"))
                self.show_splash_checkbox.setChecked(True)
                self.minimize_to_tray_checkbox.setChecked(False)
                self.auto_backup_checkbox.setChecked(False)
                self.backup_frequency_combo.setCurrentText("هفتگی")
                self.backup_location_edit.clear()
                self.debug_mode_checkbox.setChecked(False)

                # Update UI state
                self.toggle_saving_format()
                self.toggle_custom_format()

                title = "موفقیت"
                message = "همه تنظیمات به حالت پیش‌فرض بازگردانده شدند.\nبرای اعمال تغییرات، برنامه را مجدداً راه‌اندازی کنید."
                show_information_message_box(self, title, message)

            except Exception as e:
                title = "خطا"
                message = f"خطا در بازنشانی تنظیمات:\n{str(e)}"
                show_error_message_box(self, title, message)

        title = "تأیید بازنشانی"
        message = "آیا مطمئن هستید که می‌خواهید همه تنظیمات را به حالت پیش‌فرض بازگردانید؟\nاین عمل قابل برگشت نیست."
        button1 = "بله"
        button2 = "خیر"
        show_question_message_box(self, title, message, button1, perform_reset, button2)


    def apply_settings(self):
        """Apply all settings changes"""
        try:
            # Save invoice settings
            self.invoice_settings.setValue("initial_invoice_number", self.invoice_number_spinbox.value())
            self.save_scale()

            # Auto-save settings
            self.invoice_settings.setValue("auto_save", self.auto_save_checkbox.isChecked())
            self.invoice_settings.setValue("saving_format", self.saving_format_combo.currentText())
            self.invoice_settings.setValue("custom_format", self.custom_format_edit.text())
            self.invoice_settings.setValue("auto_save_directory", self.auto_save_directory_edit.text())

            # Theme and font settings
            self.save_theme()
            self.save_font_settings()

            # Display settings
            self.app_settings.setValue("show_splash", self.show_splash_checkbox.isChecked())
            self.app_settings.setValue("minimize_to_tray", self.minimize_to_tray_checkbox.isChecked())

            # Backup settings
            self.app_settings.setValue("auto_backup", self.auto_backup_checkbox.isChecked())
            self.app_settings.setValue("backup_frequency", self.backup_frequency_combo.currentText())
            self.app_settings.setValue("backup_location", self.backup_location_edit.text())

            # Advanced settings
            self.app_settings.setValue("debug_mode", self.debug_mode_checkbox.isChecked())

            title = "موفقیت"
            message = "تنظیمات با موفقیت ذخیره شدند."
            show_information_message_box(self, title, message)

        except Exception as e:
            title = "خطا"
            message = f"خطا در ذخیره تنظیمات:\n{str(e)}"
            show_error_message_box(self, title, message)


    def reject_changes(self):
        """Cancel changes and reload saved settings"""
        self.load_saved_settings()
        self.close()


    def closeEvent(self, event):
        """Handle close event"""
        # Check if there are unsaved changes
        if self.has_unsaved_changes():
            title = "تغییرات ذخیره نشده"
            message = "تغییراتی که اعمال نکرده‌اید از دست خواهد رفت.\nآیا می‌خواهید خروج کنید؟"
            button1 = "بله"
            button2 = "خیر"

            def accept_close():
                event.accept()

            def reject_close():
                event.ignore()

            show_question_message_box(self, title, message, button1, accept_close, button2, reject_close)
        else:
            event.accept()


    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        try:
            # Check invoice settings
            if (self.invoice_number_spinbox.value() !=
                    self.invoice_settings.value("initial_invoice_number", 1, type=int)):
                return True

            if (self.invoice_preview_cb.currentText() !=
                    self.preview_settings.value("scaling_factor", "متوسط (100%)")):
                return True

            if (self.auto_save_checkbox.isChecked() !=
                    self.invoice_settings.value("auto_save", False, type=bool)):
                return True

            if (self.saving_format_combo.currentText() !=
                    self.invoice_settings.value("saving_format", "نام مشتری - تاریخ صدور - زمان")):
                return True

            if (self.custom_format_edit.text() !=
                    self.invoice_settings.value("custom_format", "")):
                return True

            if (self.auto_save_directory_edit.text() !=
                    self.invoice_settings.value("auto_save_directory", "")):
                return True

            # Check theme settings
            if (self.theme_combo.currentText() !=
                    self.theme_settings.value("theme", "بهاری")):
                return True

            saved_font_family = self.app_settings.value("font_family", "Arial")
            if (self.font_family_combo.currentFont().family() != saved_font_family):
                return True

            # Check display settings
            if (self.show_splash_checkbox.isChecked() !=
                    self.app_settings.value("show_splash", True, type=bool)):
                return True

            if (self.minimize_to_tray_checkbox.isChecked() !=
                    self.app_settings.value("minimize_to_tray", False, type=bool)):
                return True

            # Check backup settings
            if (self.auto_backup_checkbox.isChecked() !=
                    self.app_settings.value("auto_backup", False, type=bool)):
                return True

            if (self.backup_frequency_combo.currentText() !=
                    self.app_settings.value("backup_frequency", "هفتگی")):
                return True

            if (self.backup_location_edit.text() !=
                    self.app_settings.value("backup_location", "")):
                return True

            # Check advanced settings
            if (self.debug_mode_checkbox.isChecked() !=
                    self.app_settings.value("debug_mode", False, type=bool)):
                return True

            return False

        except Exception:
            # If there's an error checking, assume there are changes
            return True
