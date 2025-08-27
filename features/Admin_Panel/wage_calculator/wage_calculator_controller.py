# Admin_Panel/wage_calculator/wage_calculator_controller.py

from .wage_calculator_view import WageCalculatorView
from .wage_calculator_logic import WageCalculatorLogic
from .wage_calculator_models import EmployeeData
import jdatetime  # For Jalali date handling


class WageCalculatorController:
    def __init__(self, view: WageCalculatorView, logic: WageCalculatorLogic):
        self._view = view
        self._logic = logic
        self._current_employee_for_calc: EmployeeData | None = None

        # --- NEW: Manage selected date state ---
        today = jdatetime.date.today()
        self._current_year = today.year
        self._current_month = today.month

        # Connect signals
        self._view.calculation_requested.connect(self._on_calculation_requested)
        self._view.perform_calculation_requested.connect(self._perform_calculation)
        self._view.month_changed.connect(self._on_month_changed)

        self.load_page_data()  # Changed from load_initial_data

    def load_page_data(self):
        """Loads all data for the payroll tab based on the current state."""
        try:
            # --- Load data based on the selected month and year ---
            stats_data = self._logic.get_payroll_stats_for_month(self._current_year, self._current_month)
            self._view.update_payroll_stats(stats_data)

            # --- These are now considered general info, not month-specific ---
            employees = self._logic.get_all_employees_for_display()
            self._view.populate_employee_table(employees)

            summary_data = self._logic.get_role_summary_data()
            self._view.update_role_summary(summary_data)
        except Exception as e:
            print(f"Error loading wage data: {e}")

    def _on_month_changed(self, month: int):
        """Updates the state and triggers a full data refresh."""
        self._current_month = month
        self.load_page_data()

    def _on_calculation_requested(self, employee: EmployeeData):
        """Stores the selected employee and tells the view to show the correct panel."""
        self._current_employee_for_calc = employee
        self._view.show_calculation_panel(employee)

    def _perform_calculation(self, inputs: dict):
        """Takes inputs from the view and calls the logic to get the result."""
        if not self._current_employee_for_calc:
            return

        try:
            result = self._logic.calculate_wage(self._current_employee_for_calc.user_id, inputs)
            self._view.display_calculation_result(result)
        except Exception as e:
            print(f"Error during wage calculation: {e}")
            # Optionally show an error message in the UI

    def get_view(self):
        """
        Returns the associated view for embedding in the main window.
        """
        return self._view
