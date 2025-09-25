# Admin_Panel/host_tab/admin_panel_logic.py

from sqlalchemy.engine import Engine
import qtawesome as qta

from features.Admin_Panel.admin_dashboard.admin_dashboard_factory import AdminDashboardFactory
from features.Admin_Panel.admin_reports.admin_reports_factory import AdminReportsFactory
from features.Admin_Panel.wage_calculator.wage_calculator_factory import WageCalculatorFactory
from features.Admin_Panel.employee_management.employee_management_factory import EmployeeManagementFactory

from shared.session_provider import ManagedSessionProvider


class AdminMainWindowService:
    """
    Service class for the Admin Panel main window.
    """
    def __init__(self,
                 users_engine: Engine,
                 payroll_engine: Engine,
                 expenses_engine: Engine,
                 customers_engine: Engine,
                 invoices_engine: Engine,
                 services_engine: Engine):

        self._users_engine = users_engine
        self._payroll_engine = payroll_engine
        self._expenses_engine = expenses_engine
        self._customers_engine = customers_engine
        self._invoices_engine = invoices_engine
        self._services_engine = services_engine

    def create_tabs(self):
        """
        Return a list of (_view, icon, title) for each tab.
        This method now passes the correct ENGINE objects to each factory.
        """
        dashboard_controller = AdminDashboardFactory.create(
            invoices_engine=self._invoices_engine,
            customers_engine=self._customers_engine
        )
        wage_controller = WageCalculatorFactory.create(
            payroll_engine=self._payroll_engine,
            invoices_engine=self._invoices_engine
        )
        reports_controller = AdminReportsFactory.create(
            invoices_engine=self._invoices_engine,
            expenses_engine=self._expenses_engine,
            customers_engine=self._customers_engine,
            services_engine=self._services_engine
        )
        users_controller = EmployeeManagementFactory.create(
            payroll_engine=self._payroll_engine,
            users_engine=self._users_engine
        )

        return [
            (dashboard_controller.get_view(), qta.icon('fa5s.tachometer-alt'), "داشبورد"),
            (users_controller.get_view(), qta.icon('fa5s.user-alt'), "مدیریت کاربران"),
            (wage_controller.get_view(), qta.icon('fa5s.money-bill-wave'), "محاسبه حقوق و دستمزد"),
            (reports_controller.get_view(), qta.icon('fa5s.chart-pie'), "گزارشات"),
        ]
