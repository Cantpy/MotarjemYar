# Admin_Panel/host_tab/host_tab_view.py

from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QWidget
from PySide6.QtCore import Qt
from sqlalchemy.orm import sessionmaker
import qtawesome as qta

# Import all necessary components
from features.Admin_Panel.admin_dashboard.admin_dashboard_factory import AdminDashboardFactory
from features.Admin_Panel.admin_reports.admin_reports_factory import AdminReportsFactory
from features.Admin_Panel.wage_calculator.wage_calculator_factory import WageCalculatorFactory
from features.Admin_Panel.employee_management.employee_management_factory import EmployeeManagementFactory
from shared.fonts.font_manager import FontManager
from shared.session_provider import SessionProvider


class AdminMainWindow(QWidget):
    def __init__(self,
                 session_provider: SessionProvider):
        super().__init__()
        # Store session factories for use in tabs
        self._session_provider = session_provider

        self.setWindowTitle("پنل مدیریت مترجم‌یار")
        self.setFont(FontManager.get_font(size=10))
        self.setMinimumSize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        self.tab_widget.setLayoutDirection(Qt.RightToLeft)
        # Set the font for the tab bar itself
        self.tab_widget.setFont(FontManager.get_font(size=10, bold=True))
        layout.addWidget(self.tab_widget)

        self._setup_tabs()

    def _setup_tabs(self):
        """Sets up the new tab structure."""
        self._setup_dashboard_tab()
        self._setup_user_management_tab()    # Placeholder
        self._setup_wage_calculator_tab()
        self._setup_reports_tab()
        self._setup_settings_tab()  # Placeholder

    def _setup_dashboard_tab(self):
        # For now, a simple placeholder. We will build a real one later.
        self.dashboard_controller = AdminDashboardFactory.create(self._session_provider)
        dashboard_view = self.dashboard_controller.get_view()
        dashboard_icon = qta.icon('fa5s.tachometer-alt', color='black')
        self.tab_widget.addTab(dashboard_view, dashboard_icon, "داشبورد")

    def _setup_wage_calculator_tab(self):
        """Composes and adds the Wage Calculator feature."""
        self.wage_controller = WageCalculatorFactory.create(self._session_provider)
        wage_view = self.wage_controller.get_view()
        wage_icon = qta.icon('fa5s.money-bill-wave', color='black')
        self.tab_widget.addTab(wage_view, wage_icon, "محاسبه حقوق و دستمزد")

    def _setup_reports_tab(self):
        """Composes and adds the new Admin Reports feature."""
        # The main window is the composition root, providing all necessary dependencies.
        self.reports_controller = AdminReportsFactory.create(self._session_provider)
        reports_view = self.reports_controller.get_view()
        reports_icon = qta.icon('fa5s.chart-pie', color='back')
        self.tab_widget.addTab(reports_view, reports_icon, "گزارشات")

    def _setup_user_management_tab(self):
        self.users_controller = EmployeeManagementFactory.create(self._session_provider)
        users_view = self.users_controller.get_view()
        dashboard_icon = qta.icon('fa5s.user-alt', color='black')
        self.tab_widget.addTab(users_view, dashboard_icon, "مدیریت کاربران")

    def _setup_settings_tab(self):
        dashboard_placeholder = QLabel("تنظیمات جدید در حال ساخت است...")
        dashboard_placeholder.setAlignment(Qt.AlignCenter)
        dashboard_icon = qta.icon('fa5s.cogs', color='black')
        self.tab_widget.addTab(dashboard_placeholder, dashboard_icon, "تنظیمات")
