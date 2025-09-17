# Admin_Panel/host_tab/admin_panel_logic.py

from features.Admin_Panel.admin_dashboard.admin_dashboard_factory import AdminDashboardFactory
from features.Admin_Panel.admin_reports.admin_reports_factory import AdminReportsFactory
from features.Admin_Panel.wage_calculator.wage_calculator_factory import WageCalculatorFactory
from features.Admin_Panel.employee_management.employee_management_factory import EmployeeManagementFactory

import qtawesome as qta


class AdminMainWindowService:
    def __init__(self, session_provider):
        self._session_provider = session_provider

    def create_tabs(self):
        """Return a list of (_view, icon, title) for each tab."""
        dashboard_controller = AdminDashboardFactory.create(self._session_provider)
        wage_controller = WageCalculatorFactory.create(self._session_provider)
        reports_controller = AdminReportsFactory.create(self._session_provider)
        users_controller = EmployeeManagementFactory.create(self._session_provider)

        return [
            (dashboard_controller.get_view(), qta.icon('fa5s.tachometer-alt'), "داشبورد"),
            (users_controller.get_view(), qta.icon('fa5s.user-alt'), "مدیریت کاربران"),
            (wage_controller.get_view(), qta.icon('fa5s.money-bill-wave'), "محاسبه حقوق و دستمزد"),
            (reports_controller.get_view(), qta.icon('fa5s.chart-pie'), "گزارشات"),
        ]
