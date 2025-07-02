from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTextEdit, QProgressBar,
                               QFrame, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
import re


class DatabaseSetupThread(QThread):
    """Thread to handle database setup without blocking UI"""
    progress_updated = Signal(str)  # Status message
    setup_completed = Signal(dict)  # Result dictionary

    def __init__(self, admin_info):
        super().__init__()
        self.admin_info = admin_info

    def run(self):
        from databases.database_provisioning import DatabaseProvisioner

        try:
            self.progress_updated.emit("بررسی مجوز...")

            provisioner = DatabaseProvisioner(self.admin_info)

            self.progress_updated.emit("ایجاد پایگاه داده...")

            result = provisioner.provision_office_database()

            if not result['success']:
                # Emit failure message and error for UI display
                self.setup_completed.emit({
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'message': result.get('message', '')
                })
                self.progress_updated.emit("خطا در راه‌اندازی پایگاه داده")
            else:
                self.setup_completed.emit({
                    'success': True,
                    'message': 'پایگاه داده با موفقیت راه‌اندازی شد'
                })
                self.progress_updated.emit("تکمیل نصب...")

        except Exception as e:
            self.setup_completed.emit({
                'success': False,
                'error': str(e),
                'message': 'خطا در راه‌اندازی پایگاه داده'
            })


class FirstRunSetupWizard(QDialog):
    """Wizard for first-time setup of the translation office"""
    setup_completed = Signal(bool)  # True if setup successful

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("راه‌اندازی اولیه - دفتر ترجمه")
        self.setFixedSize(500, 700)

        self.setModal(True)

        # Center the dialog
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self.setup_thread = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)

        title_label = QLabel("به مترجم‌یار خوش آمدید!")
        title_label.setFont(QFont("IranSANS", 18, QFont.Bold))
        title_label.setStyleSheet("color: white; text-align: center;")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("لطفا اطلاعات مدیر/مسئول دارالترجمه را وارد کنید")
        subtitle_label.setFont(QFont("IranSANS", 11))
        subtitle_label.setStyleSheet("color: #ecf0f1; text-align: center;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_frame)

        # Form
        form_frame = QFrame()
        form_frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setSpacing(15)

        # Admin info fields
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("نام و نام خانوادگی مدیر")

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("نام کاربری (انگلیسی)")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("ایمیل")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("رمز عبور")
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setPlaceholderText("تکرار رمز عبور")
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)

        # Style line edits
        line_edit_style = """
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """

        for edit in [self.full_name_edit, self.username_edit, self.email_edit,
                     self.password_edit, self.confirm_password_edit]:
            edit.setStyleSheet(line_edit_style)

        # Add to form
        form_layout.addWidget(QLabel("نام کامل:"), 0, 0)
        form_layout.addWidget(self.full_name_edit, 0, 1)

        form_layout.addWidget(QLabel("نام کاربری:"), 1, 0)
        form_layout.addWidget(self.username_edit, 1, 1)

        form_layout.addWidget(QLabel("ایمیل:"), 2, 0)
        form_layout.addWidget(self.email_edit, 2, 1)

        form_layout.addWidget(QLabel("رمز عبور:"), 3, 0)
        form_layout.addWidget(self.password_edit, 3, 1)

        form_layout.addWidget(QLabel("تکرار رمز عبور:"), 4, 0)
        form_layout.addWidget(self.confirm_password_edit, 4, 1)

        layout.addWidget(form_frame)

        # Progress section (initially hidden)
        self.progress_frame = QFrame()
        self.progress_frame.hide()
        progress_layout = QVBoxLayout(self.progress_frame)

        self.progress_label = QLabel("در حال راه‌اندازی...")
        self.progress_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_text)

        layout.addWidget(self.progress_frame)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("انصراف")
        self.cancel_button.clicked.connect(self.reject)

        self.setup_button = QPushButton("شروع راه‌اندازی")
        self.setup_button.clicked.connect(self.start_setup)
        self.setup_button.setDefault(True)

        # Style buttons
        button_style = """
            QPushButton {
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
                font-weight: bold;
            }
        """

        self.cancel_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        self.setup_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.setup_button)

        layout.addLayout(button_layout)

    def validate_input(self) -> tuple[bool, str]:
        """Validate user input"""
        if not self.full_name_edit.text().strip():
            return False, "لطفا نام کامل را وارد کنید"

        if not self.username_edit.text().strip():
            return False, "لطفا نام کاربری را وارد کنید"

        username = self.username_edit.text().strip()
        if len(username) < 3:
            return False, "نام کاربری باید حداقل ۳ کاراکتر باشد"

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "نام کاربری فقط باید شامل حروف انگلیسی، اعداد و _ باشد"

        email = self.email_edit.text().strip()
        if not email:
            return False, "لطفا ایمیل را وارد کنید"

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return False, "فرمت ایمیل صحیح نیست"

        password = self.password_edit.text()
        if len(password) < 6:
            return False, "رمز عبور باید حداقل ۶ کاراکتر باشد"

        if password != self.confirm_password_edit.text():
            return False, "رمز عبور و تکرار آن یکسان نیستند"

        return True, ""

    def start_setup(self):
        """Start the database setup process"""
        # Validate input
        valid, error_msg = self.validate_input()
        if not valid:
            QMessageBox.warning(self, "خطا", error_msg)
            return

        # Prepare admin info
        admin_info = {
            'full_name': self.full_name_edit.text().strip(),
            'username': self.username_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'password': self.password_edit.text()
        }

        # Show progress and disable form
        self.progress_frame.show()
        self.setup_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        # Disable form fields
        for edit in [self.full_name_edit, self.username_edit, self.email_edit,
                     self.password_edit, self.confirm_password_edit]:
            edit.setEnabled(False)

        # Start setup thread
        self.setup_thread = DatabaseSetupThread(admin_info)
        self.setup_thread.progress_updated.connect(self.update_progress)
        self.setup_thread.setup_completed.connect(self.setup_finished)
        self.setup_thread.start()

    def update_progress(self, message: str):
        """Update progress display"""
        self.status_text.append(f"• {message}")
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def setup_finished(self, result: dict):
        """Handle setup completion"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        print(result)

        if result['success']:
            self.update_progress("راه‌اندازی با موفقیت تکمیل شد!")
            self.progress_label.setText("تکمیل شد!")

            # Show success message
            QMessageBox.information(
                self,
                "موفقیت",
                "پایگاه داده با موفقیت راه‌اندازی شد.\nاکنون می‌توانید وارد برنامه شوید."
            )

            # Close wizard and signal success
            QTimer.singleShot(1000, lambda: self.setup_completed.emit(True))
            QTimer.singleShot(1000, self.accept)

        else:
            self.update_progress(f"خطا: {result.get('message', 'خطای نامشخص')}")
            self.progress_label.setText("خطا در راه‌اندازی")

            # Show error message
            QMessageBox.critical(
                self,
                "خطا",
                f"خطا در راه‌اندازی پایگاه داده:\n{result.get('error', 'خطای نامشخص')}"
            )

            # Re-enable form
            self.setup_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            for edit in [self.full_name_edit, self.username_edit, self.email_edit,
                         self.password_edit, self.confirm_password_edit]:
                edit.setEnabled(True)
