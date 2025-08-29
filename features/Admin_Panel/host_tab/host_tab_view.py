# Admin_Panel/host_tab/host_tab_view.py

from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from sqlalchemy.orm import sessionmaker
import qtawesome as qta

# Import all necessary components
from features.Admin_Panel.admin_dashboard.admin_dashboard_view import AdminDashboardView
from features.Admin_Panel.admin_dashboard.admin_dashboard_controller import AdminDashboardController
from features.Admin_Panel.admin_dashboard.admin_dashboard_logic import AdminDashboardLogic
from features.Admin_Panel.admin_dashboard.admin_dashboard_repo import AdminDashboardRepository
from features.Admin_Panel.admin_reports.admin_reports_controller import AdminReportsController
from features.Admin_Panel.admin_reports.admin_reports_view import AdminReportsView
from features.Admin_Panel.admin_reports.admin_reports_logic import AdminReportsLogic
from features.Admin_Panel.admin_reports.admin_reports_repo import AdminReportsRepository
from features.Admin_Panel.wage_calculator.wage_calculator_controller import WageCalculatorController
from features.Admin_Panel.wage_calculator.wage_calculator_view import WageCalculatorView
from features.Admin_Panel.wage_calculator.wage_calculator_logic import WageCalculatorLogic
from features.Admin_Panel.wage_calculator.wage_calculator_repo import WageCalculatorRepository
from features.Admin_Panel.employee_management.employee_management_controller import UserManagementController
from features.Admin_Panel.employee_management.employee_management_view import UserManagementView
from features.Admin_Panel.employee_management.employee_management_logic import UserManagementLogic
from features.Admin_Panel.employee_management.employee_management_repo import EmployeeManagementRepository
from shared.fonts.font_manager import FontManager


class AdminMainWindow(QMainWindow):
    def __init__(self,
                 invoices_session_factory,
                 customers_session_factory,
                 services_session_factory,
                 expenses_session_factory,
                 users_session_factory,
                 payroll_session_factory,):
        super().__init__()
        # Store session factories for use in tabs
        self.InvoicesSession = invoices_session_factory
        self.CustomersSession = customers_session_factory
        self.ServicesSession = services_session_factory
        self.ExpensesSession = expenses_session_factory
        self.UsersSession = users_session_factory
        self.PayrollSession = payroll_session_factory

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
        view = AdminDashboardView()
        repo = AdminDashboardRepository()
        logic = AdminDashboardLogic(repo,
                                    self.InvoicesSession,
                                    self.CustomersSession)
        self.dashboard_controller = AdminDashboardController(view, logic)
        dashboard_view = self.dashboard_controller.get_view()
        dashboard_icon = qta.icon('fa5s.tachometer-alt', color='black')
        self.tab_widget.addTab(dashboard_view, dashboard_icon, "داشبورد")

    def _setup_wage_calculator_tab(self):
        """Composes and adds the Wage Calculator feature."""
        view = WageCalculatorView()
        repo = WageCalculatorRepository()
        logic = WageCalculatorLogic(repo,
                                    self.InvoicesSession,
                                    self.PayrollSession)
        self.wage_controller = WageCalculatorController(view, logic)  # Compose with dependencies
        wage_view = self.wage_controller.get_view()
        wage_icon = qta.icon('fa5s.money-bill-wave', color='black')
        self.tab_widget.addTab(wage_view, wage_icon, "محاسبه حقوق و دستمزد")

    def _setup_reports_tab(self):
        """Composes and adds the new Admin Reports feature."""
        # The main window is the composition root, providing all necessary dependencies.
        view = AdminReportsView()
        repo = AdminReportsRepository()
        logic = AdminReportsLogic(repo,
                                  self.InvoicesSession,
                                  self.ServicesSession,
                                  self.ExpensesSession,
                                  self.CustomersSession)
        self.reports_controller = AdminReportsController(view, logic)
        reports_view = self.reports_controller.get_view()
        reports_icon = qta.icon('fa5s.chart-pie', color='back')
        self.tab_widget.addTab(reports_view, reports_icon, "گزارشات")

    def _setup_user_management_tab(self):
        view = UserManagementView()
        repo = EmployeeManagementRepository()
        logic = UserManagementLogic(repo,
                                    self.UsersSession,
                                    self.PayrollSession)
        self.users_controller = UserManagementController(view, logic)
        users_view = self.users_controller.get_view()
        dashboard_icon = qta.icon('fa5s.user-alt', color='black')
        self.tab_widget.addTab(users_view, dashboard_icon, "مدیریت کاربران")

    def _setup_settings_tab(self):
        dashboard_placeholder = QLabel("تنظیمات جدید در حال ساخت است...")
        dashboard_placeholder.setAlignment(Qt.AlignCenter)
        dashboard_icon = qta.icon('fa5s.cogs', color='black')
        self.tab_widget.addTab(dashboard_placeholder, dashboard_icon, "تنظیمات")
