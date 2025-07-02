from PySide6.QtWidgets import QTabWidget, QHBoxLayout, QVBoxLayout, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal
from modules.RBAC.users_info import UserInformationWidget
from modules.RBAC.users_dashboard import UserDashboardWidget
from modules.RBAC.admin_translationoffice import TranslationOfficeWidget

from modules.helper_functions import return_resource
from modules.user_context import UserContext


class UsersTabbedWidget(QWidget):
    """Main tabbed widget for user interface"""
    logout_requested = Signal()

    def __init__(self, parent,
                 database=return_resource("databases", "users.db")):  # user_context: UserContext
        super().__init__(parent)
        # self.user_context = user_context
        # self.username = self.user_context.username
        self.db = database
        self.setup_ui()

    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("پنل کاربری سیستم")
        # Set RTL layout direction for Persian
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(900, 800)

        # Style the widget
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: #FAFAFA;
                border-radius: 5px;
            }
            QTabWidget::tab-bar {
                alignment: right;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                color: #2c3e50;
                padding: 10px 20px;
                margin: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #007ACC;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #B0B0B0;
            }
            QLabel#title_label {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                padding: 5px;
            }
            QLabel#subtitle_label {
                color: #7f8c8d;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton#logout_btn {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton#logout_btn:hover {
                background-color: #c0392b;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header with logout button
        header_layout = QHBoxLayout()
        header_layout.addStretch()

        self.logout_btn = QPushButton("خروج")
        self.logout_btn.setObjectName("logout_btn")
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(self.logout_btn)

        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setLayoutDirection(Qt.RightToLeft)
        # Set tab position
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Create tabs
        self.create_dashboard_tab()
        self.create_user_management_tab()
        self.create_office_info_tab()

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        self.dashboard_widget = UserDashboardWidget(self)  # self.user_context
        self.tab_widget.addTab(self.dashboard_widget, "داشبورد کاربری")

    def create_user_management_tab(self):
        """Create the user information tab"""
        self.info_widget = UserInformationWidget(self, "admin")  # self.username
        self.tab_widget.addTab(self.info_widget, "اطلاعات کاربری")

    def create_office_info_tab(self):
        """Create the translation office information tab"""
        self.translation_office_widget = TranslationOfficeWidget(self, self.db)
        self.tab_widget.addTab(self.translation_office_widget, "اطلاعات دارالترچمه")
