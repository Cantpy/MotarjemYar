# features/Admin_Panel/wage_calculator/wage_calculator_controller.py

import jdatetime
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout

from features.Admin_Panel.wage_calculator.wage_calculator_view import WageCalculatorView
from features.Admin_Panel.wage_calculator.wage_calculator_logic import WageCalculatorLogic
from features.Admin_Panel.wage_calculator.wage_calculator_preview.wage_calculator_preview_controller import \
    WageCalculatorPreviewController
from features.Admin_Panel.wage_calculator.wage_calculator_preview.wage_calculator_preview_view import WageCalculatorPreviewDialog
from features.Admin_Panel.wage_calculator.wage_calculator_preview.salary_slip_viewer import SalarySlipViewer
from shared import show_error_message_box


class WageCalculatorController:
    def __init__(self, view: WageCalculatorView, logic: WageCalculatorLogic):
        self._view = view
        self._logic = logic
        today = jdatetime.date.today()
        self._current_year = today.year
        self._current_month = today.month

        self._view.period_changed.connect(self._on_period_changed)
        self._view.run_payroll_requested.connect(self._on_run_payroll_requested)
        self._view.view_payslip_requested.connect(self._on_view_payslip_requested)
        self._view.refresh_requested.connect(self.load_page_data)

        self.load_page_data()

    def load_page_data(self):
        try:
            records = self._logic.get_payroll_run_summary(self._current_year, self._current_month)
            self._view.populate_table(records)
        except Exception as e:
            QMessageBox.critical(self._view, "خطا", f"خطایی در بارگذاری اطلاعات حقوق رخ داد:\n{e}")

    def _on_period_changed(self, period: dict):
        self._current_year = period['year']
        self._current_month = period['month']
        self.load_page_data()

    def _on_run_payroll_requested(self):
        """
        Handles the 'Run Payroll' workflow by launching the preview and generation dialog.
        """
        try:
            employees = self._logic.get_employee_list()
            if not employees:
                QMessageBox.warning(self._view, "هشدار", "هیچ کارمند فعالی برای محاسبه حقوق وجود ندارد.")
                return

            # The preview dialog and its controller manage the entire generation process
            preview_view = WageCalculatorPreviewDialog(employees, self._view)
            preview_controller = WageCalculatorPreviewController(preview_view, self._logic)

            # The dialog is executed. If it's accepted, it means the payslip was saved.
            result = preview_controller.exec()
            if result == QDialog.Accepted:
                self.load_page_data()  # Refresh the main table to show the new record

        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطایی در حین اجرای محاسبه حقوق رخ داد:\n{e}")

    def _on_view_payslip_requested(self, payroll_id: str):
        """
        Shows the details of an existing, saved payslip in a new pop-up dialog.
        """
        if not payroll_id:
            return
        try:
            details = self._logic.get_payslip_data_for_preview(payroll_id)
            if details:
                # Create a new dialog to show the payslip
                dialog = QDialog(self._view)
                dialog.setWindowTitle(f"فیش حقوقی - {details.employee_name}")
                dialog.setMinimumSize(850, 750)

                layout = QVBoxLayout(dialog)
                viewer = SalarySlipViewer()
                viewer.populate(details)
                layout.addWidget(viewer)

                dialog.exec()

        except Exception as e:
            QMessageBox.critical(self._view, "خطا", f"خطایی در نمایش جزئیات فیش حقوقی رخ داد:\n{e}")

    def get_view(self):
        """
        Returns the associated _view instance.
        """
        return self._view
