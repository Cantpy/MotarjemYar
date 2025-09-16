# _view.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
                               QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize
from shared import show_error_message_box, show_warning_message_box, show_information_message_box
from features.Login.login_window_styles import (LOGIN_WINDOW_STYLES, REMEMBER_ME_STYLES, LOGIN_SUCCESS_STYLES,
                                                LOGIN_FAILED_STYLES, RESET_FORM_STYLES)


class LoginWidget(QWidget):
    """
    The LoginWidget class represents the login window UI. It is responsible for rendering the login form,
    capturing user input, and emitting signals for the controller to handle.
    """
    login_attempted = Signal(str, str, bool)
    password_visibility_toggled = Signal(int)
    reset_form_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the user interface elements and their layout."""
        self.setWindowTitle("ورود به سیستم")
        self.setFixedSize(930, 780)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top spacer
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(top_spacer)

        # Welcome section layout
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(15)
        welcome_layout.setContentsMargins(-1, 20, -1, 20)

        # Welcome text
        self.welcome_text = QLabel("به مترجم‌یار خوش آمدید!")
        self.welcome_text.setObjectName("welcome_text")
        self.welcome_text.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(self.welcome_text)

        # Login status text
        self.login_text = QLabel("شما هنوز وارد نشده‌اید")
        self.login_text.setObjectName("login_text")
        self.login_text.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(self.login_text)

        main_layout.addLayout(welcome_layout)

        # Input fields section
        input_section_layout = QHBoxLayout()
        input_section_layout.setObjectName("input_section_layout")

        # Left spacer
        left_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        input_section_layout.addItem(left_spacer)

        # Input fields layout
        input_layout = QVBoxLayout()
        input_layout.setSpacing(20)
        input_layout.setContentsMargins(-1, 15, -1, 15)

        # Username field
        self.username_input = QLineEdit()
        self.username_input.setObjectName("username_le")
        self.username_input.setPlaceholderText("نام کاربری یا ایمیل")
        self.username_input.setMaximumSize(QSize(300, 16777215))
        input_layout.addWidget(self.username_input)

        # Password field with show/hide button
        password_container = QHBoxLayout()
        password_container.setSpacing(5)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("password_le")
        self.password_input.setPlaceholderText("رمز عبور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMaximumSize(QSize(240, 16777215))
        password_container.addWidget(self.password_input)

        self.show_password_btn = QPushButton("نمایش")
        self.show_password_btn.setObjectName("show_password_btn")
        password_container.addWidget(self.show_password_btn)

        input_layout.addLayout(password_container)

        # Remember me checkbox
        self.remember_me_checkbox = QCheckBox("مرا به خاطر بسپار")
        self.remember_me_checkbox.setObjectName("remember_me_checkbox")
        self.remember_me_checkbox.setStyleSheet(REMEMBER_ME_STYLES)

        input_layout.addWidget(self.remember_me_checkbox)

        input_section_layout.addLayout(input_layout)

        # Right spacer
        right_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        input_section_layout.addItem(right_spacer)

        main_layout.addLayout(input_section_layout)

        # Login button section
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(-1, 20, -1, 20)

        # Button left spacer
        button_left_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(button_left_spacer)

        self.login_btn = QPushButton("ورود")
        self.login_btn.setObjectName("enter_button")
        button_layout.addWidget(self.login_btn)

        # Button right spacer
        button_right_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        button_layout.addItem(button_right_spacer)

        main_layout.addLayout(button_layout)

        # Role display (initially hidden)
        self.role_label = QLabel()
        self.role_label.setObjectName("role_text")
        self.role_label.setAlignment(Qt.AlignCenter)
        self.role_label.hide()
        main_layout.addWidget(self.role_label)

        # Forgot password label
        self.forgot_password_label = QLabel("فراموشی رمز عبور یا نام کاربری")
        self.forgot_password_label.setObjectName("forgot_password_label")
        self.forgot_password_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.forgot_password_label)

        # Register label
        self.register_label = QLabel("هنوز ثبت‌نام نکرده‌اید؟")
        self.register_label.setObjectName("register_label")
        self.register_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.register_label)

        # Bottom spacer
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(bottom_spacer)

        self.setLayout(main_layout)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(LOGIN_WINDOW_STYLES)

    def setup_connections(self):
        """Setup signal connections to the controller's methods."""
        self.login_btn.clicked.connect(self._on_login_button_clicked)
        self.show_password_btn.clicked.connect(self._on_show_password_button_clicked)
        self.username_input.returnPressed.connect(self._on_login_button_clicked)
        self.password_input.returnPressed.connect(self._on_login_button_clicked)

    # Methods for the Controller to call to update the UI (View remains "dumb")
    def _on_login_button_clicked(self) -> None:
        """Collects login data and emits the login_attempted signal."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        ischecked = self.remember_me_checkbox.isChecked()
        self.login_attempted.emit(username, password, ischecked)

    def _on_show_password_button_clicked(self) -> None:
        """Emits the password_visibility_toggled signal."""
        self.password_visibility_toggled.emit(self.password_input.echoMode())

    def login_successful_ui(self, full_name: str, role_text: str) -> None:
        """Updates the UI to reflect a successful login."""
        self.login_text.setText(f"خوش آمدید، {full_name}")
        self.login_text.setObjectName("role_text") # Change object name to apply different CSS
        self.login_text.setStyleSheet(LOGIN_SUCCESS_STYLES)

        self.role_label.setText(f"نقش: {role_text}")
        self.role_label.show()

    def login_failed_ui(self, message: str) -> None:
        """Updates the UI to reflect a failed login."""
        self.login_text.setText("ورود ناموفق")
        self.login_text.setObjectName("login_text")  # Reset to default style object name
        self.login_text.setStyleSheet(LOGIN_FAILED_STYLES)  # Reset style
        self.role_label.hide()

    def toggle_password_visibility_ui(self, current_echo_mode: int) -> None:
        """
        PUBLIC SLOT: Toggles the visibility of the password input field.
        This method contains all the UI update _logic.
        """
        if current_echo_mode == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("مخفی")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("نمایش")

    def disable_login_button(self, text: str) -> None:
        """Disables the login button and sets its text."""
        self.login_btn.setEnabled(False)
        self.login_btn.setText(text)

    def enable_login_button(self, text: str) -> None:
        """Enables the login button and sets its text."""
        self.login_btn.setEnabled(True)
        self.login_btn.setText(text)

    def set_remember_me_checkbox(self, checked: bool) -> None:
        """Sets the checked state of the 'remember me' checkbox."""
        self.remember_me_checkbox.setChecked(checked)

    def clear_password_input(self) -> None:
        """Clears the password input field."""
        self.password_input.clear()

    def reset_form_ui(self) -> None:
        """Resets all relevant UI elements in the login form to their initial state."""
        self.username_input.clear()
        self.password_input.clear()
        self.login_text.setText("شما هنوز وارد نشده‌اید")
        self.login_text.setObjectName("login_text")
        self.login_text.setStyleSheet(RESET_FORM_STYLES)
        self.role_label.hide()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.show_password_btn.setText("نمایش")
        self.remember_me_checkbox.setChecked(False)
