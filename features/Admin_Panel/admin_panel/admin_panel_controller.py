# features/Admin_Panel/admin_panel/admin_panel_controller.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.admin_panel.admin_panel_view import AdminPanelView

# Import the factories for each sub-feature
from features.Admin_Panel.admin_dashboard.admin_dashboard_factory import AdminDashboardFactory
from features.Admin_Panel.admin_reports.admin_reports_factory import AdminReportsFactory
from features.Admin_Panel.employee_management.employee_management_factory import EmployeeManagementFactory
from features.Admin_Panel.wage_calculator.wage_calculator_factory import WageCalculatorFactory


class AdminPanelController:
    """
    Orchestrates the creation and display of all admin sub-features within a tabbed view.
    """
    def __init__(self, view: AdminPanelView, engines: dict[str, Engine]):
        self._view = view
        self._engines = engines
        self._sub_controllers = {}  # To keep references to the created controllers

        self._create_tabs()

    def _create_tabs(self):
        """
        Uses the factories of each sub-feature to create them and add their
        views to the main tab widget.
        """
        # --- 1. Dashboard Tab ---
        try:
            dashboard_controller = AdminDashboardFactory.create(
                invoices_engine=self._engines['invoices'],
                customers_engine=self._engines['customers'],
                parent=self._view
            )
            self._sub_controllers['dashboard'] = dashboard_controller
            self._view.add_feature_tab(dashboard_controller.get_view(), 'fa5s.tachometer-alt', "داشبورد")
        except Exception as e:
            print(f"Failed to create Admin Dashboard tab: {e}")

        # --- 2. Reports Tab ---
        try:
            reports_controller = AdminReportsFactory.create(
                invoices_engine=self._engines['invoices'],
                services_engine=self._engines['services'],
                expenses_engine=self._engines['expenses'],
                customers_engine=self._engines['customers'],
                parent=self._view
            )
            self._sub_controllers['reports'] = reports_controller
            self._view.add_feature_tab(reports_controller.get_view(), 'fa5s.chart-bar', "گزارشات")
        except Exception as e:
            print(f"Failed to create Admin Reports tab: {e}")

        # --- 3. Employee Management Tab ---
        try:
            employee_controller = EmployeeManagementFactory.create(
                payroll_engine=self._engines['payroll'],
                users_engine=self._engines['users'],
                parent=self._view
            )
            self._sub_controllers['employee_management'] = employee_controller
            self._view.add_feature_tab(employee_controller.get_view(), 'fa5s.users-cog', "مدیریت کارمندان")
        except Exception as e:
            print(f"Failed to create Employee Management tab: {e}")

        # --- 4. Wage Calculator Tab ---
        try:
            wage_controller = WageCalculatorFactory.create(
                payroll_engine=self._engines['payroll'],
                invoices_engine=self._engines['invoices'],
                parent=self._view
            )
            self._sub_controllers['wage_calculator'] = wage_controller
            self._view.add_feature_tab(wage_controller.get_view(), 'fa5s.calculator', "محاسبه حقوق")
        except Exception as e:
            print(f"Failed to create Wage Calculator tab: {e}")

    def get_view(self) -> AdminPanelView:
        """
        Returns the main container view for the entire Admin Panel.
        This is what the PageManager will display.
        """
        return self._view
