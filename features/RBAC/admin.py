import sys

from modules.RBAC.admin_dashboard import AdminDashboardWidget
from modules.RBAC.admin_usesrmanagement import UserManagementWidget
from modules.RBAC.admin_translationoffice import TranslationOfficeWidget

from modules.helper_functions import return_resource
from modules.user_context import UserContext

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QApplication
from PySide6.QtCore import Signal, Qt


class TabbedAdminPanel(QWidget):
    """Main tabbed admin panel containing all admin functionality"""
    logout_requested = Signal()

    def __init__(self, parent, db_path=return_resource('databases', 'users.db')):  # user_context: UserContext
        super().__init__(parent)
        # self.user_context = user_context
        # self.username = self.user_context.username
        self.db_path = db_path
        self.setup_ui()

    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("پنل مدیریت سیستم")
        self.setMinimumSize(900, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 5px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 150px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #bdc3c7;
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

        # Create tabs
        self.create_dashboard_tab()
        self.create_user_management_tab()
        self.create_office_info_tab()

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def create_dashboard_tab(self):
        """Create the admin dashboard tab"""
        self.dashboard_widget = AdminDashboardWidget(self, "admin", self.db_path)  # self.username
        self.tab_widget.addTab(self.dashboard_widget, "داشبورد مدیر")

    def create_user_management_tab(self):
        """Create user management tab (placeholder)"""
        self.user_management_tab = UserManagementWidget(self, self.db_path)
        self.tab_widget.addTab(self.user_management_tab, "مدیریت کاربران")

    def create_office_info_tab(self):
        """Create translation office information tab (placeholder)"""
        self.office_tab = TranslationOfficeWidget(self, self.db_path)
        self.tab_widget.addTab(self.office_tab, "اطلاعات دفتر ترجمه")
