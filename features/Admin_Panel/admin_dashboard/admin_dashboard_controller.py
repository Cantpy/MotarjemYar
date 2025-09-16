# Admin_Panel/admin_dashboard/admin_dashboard_controller.py

from .admin_dashboard_view import AdminDashboardView
from .admin_dashboard_logic import AdminDashboardLogic
from .wage_calculator_dialog import WageCalculatorDialog


class AdminDashboardController:
    def __init__(self, view: AdminDashboardView, logic: AdminDashboardLogic,):
        self._view = view
        self._logic = logic

        self.load_dashboard_data()

        # --- Connect signals for new action buttons ---
        self._view.refresh_btn.clicked.connect(self.load_dashboard_data)
        self._view.calculate_wage_requested.connect(self._open_wage_calculator)

    def load_dashboard_data(self):
        try:
            # Get the fully prepared dataclasses from the _logic layer
            kpi_data = self._logic.get_kpi_data()
            orders_data = self._logic.get_attention_queue()
            performers_data = self._logic.get_top_performers_data()

            # Pass them directly to the _view
            self._view.update_kpi_cards(kpi_data)
            self._view.populate_attention_queue(orders_data)
            self._view.populate_top_performers(performers_data)

        except Exception as e:
            print(f"Failed to load dashboard data: {e}")

    def _open_wage_calculator(self):
        """Creates and shows the wage calculator dialog."""
        dialog = WageCalculatorDialog(self._view)
        # In a real app, you would pass employee data to the dialog here
        dialog.exec()

    def get_view(self):
        """
        Returns the associated _view for embedding in the main window.
        """
        return self._view
