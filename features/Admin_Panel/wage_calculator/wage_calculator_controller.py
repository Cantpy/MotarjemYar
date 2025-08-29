# motarjemyar/wage_calculator/wage_calculator_controller.py

import jdatetime
from PySide6.QtWidgets import QMessageBox, QDialog
from features.Admin_Panel.wage_calculator.wage_calculator_view import WageCalculatorView, OvertimeInputDialog
from features.Admin_Panel.wage_calculator.wage_calculator_logic import WageCalculatorLogic


class WageCalculatorController:
    def __init__(self, view: WageCalculatorView, logic: WageCalculatorLogic):
        self._view = view
        self._logic = logic
        today = jdatetime.date.today()
        self._current_year = today.year
        self._current_month = today.month

        self._view.period_changed.connect(self._on_period_changed)
        self._view.run_payroll_requested.connect(self._on_run_payroll_requested)
        self._view.employee_selected.connect(self._on_employee_selected)

        self.load_page_data()

    def load_page_data(self):
        try:
            records = self._logic.get_payroll_run_summary(self._current_year, self._current_month)
            print(f"records: {records}")  # Debugging line
            self._view.populate_table(records)
        except Exception as e:
            QMessageBox.critical(self._view, "خطا", f"خطایی در بارگذاری اطلاعات حقوق رخ داد:\n{e}")

    def _on_period_changed(self, period: dict):
        self._current_year = period['year']
        self._current_month = period['month']
        self.load_page_data()

    def _on_run_payroll_requested(self):
        """
        Handles the entire 'Run Payroll' workflow.
        This is the correct location for this logic.
        """
        try:
            # 1. Get the full list of employees from the logic layer.
            employees = self._logic.get_employee_list()

            # 2. Perform validation within the controller.
            if not employees:
                QMessageBox.warning(self._view, "هشدار", "هیچ کارمند فعالی برای محاسبه حقوق وجود ندارد.")
                return

            # 3. Create and show the dialog to get overtime hours.
            dialog = OvertimeInputDialog(employees, self._view)
            if dialog.exec() == QDialog.Accepted:
                overtime_data = dialog.get_overtime_data()

                # 4. Execute the pay run with the collected data.
                self._logic.execute_pay_run(self._current_year, self._current_month, overtime_data)

                # 5. Refresh the page to show the new results.
                self.load_page_data()
                QMessageBox.information(self._view, "موفقیت",
                                        "محاسبه حقوق برای دوره انتخابی با موفقیت انجام و ذخیره شد.")

        except Exception as e:
            QMessageBox.critical(self._view, "خطا", f"خطایی در حین اجرای محاسبه حقوق رخ داد:\n{e}")

    def _on_employee_selected(self, payroll_id: str):
        try:
            details = self._logic.get_payslip_details(payroll_id)
            if details:
                self._view.display_payslip_details(details)
        except Exception as e:
            QMessageBox.critical(self._view, "خطا", f"خطایی در نمایش جزئیات فیش حقوقی رخ داد:\n{e}")

    def get_view(self):
        """
        Returns the associated view instance.
        """
        return self._view
