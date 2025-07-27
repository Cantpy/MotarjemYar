import bcrypt
import json
import os
import secrets
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
                               QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from shared import (return_resource, show_error_message_box, show_warning_message_box, show_information_message_box)
from contextlib import contextmanager

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    username = Column(String(255), primary_key=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    token_hash = Column(Text, nullable=True)
    expires_at = Column(String(50), nullable=True)  # Using String to match existing ISO format
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to user profile
    profile = relationship("UserProfile", back_populates="user", uselist=False)


class UserProfile(Base):
    __tablename__ = 'user_profiles'

    username = Column(String(255), ForeignKey('users.username'), primary_key=True)
    full_name = Column(String(255), nullable=True)
    role_fa = Column(String(100), nullable=True)

    # Relationship back to user
    user = relationship("User", back_populates="profile")


class LoginWidget(QWidget):
    # Signal emitted when login is successful, passes username and role
    login_successful = Signal(str, str)

    def __init__(self, db_config=None):
        super().__init__()
        self.db_config = db_config
        self.setup_database()
        self.setup_ui()
        self.setup_connections()
        self.check_remembered_login()

    def setup_database(self):
        """Setup SQLAlchemy database connection"""
        # Create database URL from config  ----------------------------- uncomment later after tests
        # if isinstance(self.db_config, dict):
        #     # PostgreSQL connection
        #     db_url = (f"postgresql://{self.db_config['user']}:{self.db_config['password']}"
        #               f"@{self.db_config['host']}:{self.db_config.get('port', 5432)}"
        #               f"/{self.db_config['database']}")
        # else:
        #     # SQLite connection (for backward compatibility)
        #     db_url = f"sqlite:///{self.db_config}"

        db_url = return_resource("databases_cleaned", "users.db")  # Use SQLite for simplicity in tests
        self.engine = create_engine(f"sqlite:///{db_url}", echo=False)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))

        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_db_session(self):
        """Get SQLAlchemy database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("ورود به سیستم")
        self.setFixedSize(930, 780)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'IRANSans', Tahoma, Arial, sans-serif;
            }
            QLabel#welcome_text {
                color: #2c3e50;
                font-size: 32px;
                font-weight: bold;
            }
            QLabel#login_text {
                color: #7f8c8d;
                font-size: 20px;
            }
            QLabel#role_text {
                color: #27ae60;
                font-size: 20px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 15px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                max-width: 300px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QPushButton#enter_button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#enter_button:hover {
                background-color: #2980b9;
            }
            QPushButton#enter_button:pressed {
                background-color: #21618c;
            }
            QPushButton#show_password_btn {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 11px;
                max-width: 60px;
            }
            QPushButton#show_password_btn:hover {
                background-color: #7f8c8d;
            }
            QLabel#forgot_password_label, QLabel#register_label {
                color: #7f8c8d;
                font-size: 11px;
            }
        """)

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
        self.remember_me_checkbox.setStyleSheet("""
            QCheckBox {
                color: #7f8c8d;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border-color: #3498db;
                background-color: #3498db;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QCheckBox::indicator:hover {
                border-color: #3498db;
            }
        """)
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

    def check_remembered_login(self):
        """Check if there's a remembered login and auto-login if valid"""
        try:
            settings_path = return_resource("databases", "login_settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                if settings.get('remember_me', False):
                    username = settings.get('username', '')
                    token = settings.get('token', '')

                    if username and token and self.verify_remember_token(username, token):
                        # Auto-login the user
                        self.username_input.setText(username)
                        self.remember_me_checkbox.setChecked(True)
                        self.auto_login_user(username)
                    else:
                        # Invalid or expired token, clear settings
                        self.clear_remember_settings()
        except Exception as e:
            print(f"Error checking remembered login: {e}")

    def verify_remember_token(self, username, token):
        """Verify the remember me token is valid and not expired"""
        try:
            with self.get_db_session() as session:
                user = session.query(User).filter_by(username=username).first()

                if not user or not user.active:
                    return False

                # Check if token matches and hasn't expired
                if user.token_hash and user.expires_at:
                    if isinstance(user.token_hash, str):
                        token_hash = user.token_hash.encode('utf-8')
                    else:
                        token_hash = user.token_hash

                    expires_datetime = datetime.fromisoformat(user.expires_at)
                    if datetime.now() < expires_datetime:
                        return bcrypt.checkpw(token.encode('utf-8'), token_hash)

                return False
        except Exception as e:
            print(f"Error verifying remember token: {e}")
            return False

    def auto_login_user(self, username):
        """Automatically log in a remembered user"""
        try:
            with self.get_db_session() as session:
                user = session.query(User).filter_by(username=username).first()

                if user and user.active:
                    role_fa = user.profile.role_fa if user.profile else None
                    self.login_successful_handler(username, user.role, role_fa)
                else:
                    self.clear_remember_settings()
        except Exception as e:
            print(f"Error in auto login: {e}")
            self.clear_remember_settings()

    def get_full_name(self, username):
        """Get user's full name from profile"""
        try:
            with self.get_db_session() as session:
                user = session.query(User).filter_by(username=username).first()
                if user and user.profile:
                    return user.profile.full_name or "کاربر میهمان"
                return "کاربر میهمان"
        except Exception as e:
            print(f"Error fetching full name: {e}")
            return "کاربر میهمان"

    def save_remember_settings(self, username, token):
        """Save remember me settings to file"""
        try:
            # Get the full path for the settings file
            settings_path = return_resource("databases", "login_settings.json")
            settings_dir = os.path.dirname(settings_path)
            os.makedirs(settings_dir, exist_ok=True)

            # Fetch full name
            full_name = self.get_full_name(username)

            settings = {
                'remember_me': True,
                'username': username,
                'token': token,
                'full_name': full_name
            }

            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Error saving remember settings: {e}")

    def clear_remember_settings(self):
        """Clear saved remember me settings"""
        try:
            settings_path = return_resource("databases", "login_settings.json")
            if os.path.exists(settings_path):
                os.remove(settings_path)
        except Exception as e:
            print(f"Error clearing remember settings: {e}")

    def generate_remember_token(self, username):
        """Generate and save a remember me token for the user"""
        try:
            # Generate a random token
            token = secrets.token_urlsafe(32)
            token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt())

            # Set expiration to 30 days from now
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()

            # Save token hash to database using ORM
            with self.get_db_session() as session:
                user = session.query(User).filter_by(username=username).first()
                if user:
                    user.token_hash = token_hash
                    user.expires_at = expires_at
                    # Session will be committed by context manager

            # Save settings to file
            self.save_remember_settings(username, token)

        except Exception as e:
            print(f"Error generating remember token: {e}")

    def clear_remember_token(self, username):
        """Clear the remember me token from database"""
        try:
            with self.get_db_session() as session:
                user = session.query(User).filter_by(username=username).first()
                if user:
                    user.token_hash = None
                    user.expires_at = None
                    # Session will be committed by context manager
        except Exception as e:
            print(f"Error clearing remember token: {e}")

    def setup_connections(self):
        """Setup signal connections"""
        self.login_btn.clicked.connect(self.handle_login)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    def toggle_password_visibility(self):
        """Toggle password field visibility"""
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("مخفی")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("نمایش")

    def handle_login(self):
        """Handle login attempt"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            title = "خطا"
            message = "لطفاً نام کاربری و رمز عبور را وارد کنید."
            show_warning_message_box(self, title, message)
            return

        # Disable login button during authentication
        self.login_btn.setEnabled(False)
        self.login_btn.setText("در حال بررسی...")

        # Use QTimer to prevent UI freezing during database operations
        QTimer.singleShot(100, lambda: self.authenticate_user(username, password))

    def authenticate_user(self, username, password):
        """Authenticate user against database using SQLAlchemy ORM"""
        try:
            with self.get_db_session() as session:
                # Get user with profile using eager loading
                user = session.query(User).filter_by(username=username).first()
                print(user)

                if not user:
                    self.login_failed("نام کاربری یا رمز عبور اشتباه است.")
                    return

                # Check if user is active
                if not user.active:
                    self.login_failed("حساب کاربری غیرفعال است.")
                    return

                # Handle password hash type conversion
                password_hash = user.password_hash
                if isinstance(password_hash, str):
                    password_hash = password_hash.encode('utf-8')

                # Verify password
                try:
                    password_valid = bcrypt.checkpw(password.encode('utf-8'), password_hash)

                    if password_valid:
                        role_fa = user.profile.role_fa if user.profile else None
                        self.login_successful_handler(username, user.role, role_fa)
                    else:
                        self.login_failed("نام کاربری یا رمز عبور اشتباه است.")

                except ValueError as ve:
                    self.login_failed("خطا در تأیید رمز عبور. ممکن است رمز عبور نیاز به بازنشانی داشته باشد.")

        except SQLAlchemyError as e:
            self.login_failed(f"خطا در اتصال به پایگاه داده: {str(e)}")
        except Exception as e:
            self.login_failed(f"خطای غیرمنتظره: {str(e)}")
        finally:
            # Re-enable login button
            self.login_btn.setEnabled(True)
            self.login_btn.setText("ورود")

    def login_successful_handler(self, username, role, role_fa):
        """Handle successful login"""
        full_name = self.get_full_name(username)

        self.logged_in_user = {
            "username": username,
            "role": role,
            "role_fa": role_fa,
            "full_name": full_name,
            "is_remembered": self.remember_me_checkbox.isChecked()
        }

        self.login_text.setText(f"خوش آمدید، {full_name}")
        self.login_text.setObjectName("role_text")

        role_text = self.get_role_text(role, role_fa)
        self.role_label.setText(f"نقش: {role_text}")
        self.role_label.show()

        if self.remember_me_checkbox.isChecked():
            self.generate_remember_token(username)
        else:
            self.clear_remember_token(username)
            self.clear_remember_settings()

        self.password_input.clear()
        self.login_successful.emit(username, role)

        show_information_message_box(self, "موفقیت", f"ورود موفق!\nنقش شما: {role_text}")

    def get_role_text(self, role, role_fa):
        """Get Persian role text"""
        if role_fa:
            return role_fa

        role_mapping = {
            'admin': 'مدیر',
            'translator': 'مترجم',
            'clerk': 'منشی',
            'accountant': 'حسابدار'
        }
        return role_mapping.get(role, 'کاربر')

    def login_failed(self, message):
        """Handle failed login"""
        self.login_text.setText("ورود ناموفق")
        self.login_text.setObjectName("login_text")  # Reset to default style
        self.role_label.hide()
        show_error_message_box(self, "خطا", message)

    def reset_form(self):
        """Reset the login form"""
        self.username_input.clear()
        self.password_input.clear()
        self.login_text.setText("شما هنوز وارد نشده‌اید")
        self.login_text.setObjectName("login_text")
        self.role_label.hide()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.show_password_btn.setText("نمایش")
        self.remember_me_checkbox.setChecked(False)
        self.clear_remember_settings()

    def __del__(self):
        """Cleanup database connections"""
        if hasattr(self, 'SessionLocal'):
            self.SessionLocal.remove()
