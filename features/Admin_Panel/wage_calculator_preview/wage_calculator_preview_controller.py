# Admin_Panel/wage_calculator_preview/wage_calculator_preview_controller.py

import os
import sys
import tempfile
import subprocess
from PySide6.QtWidgets import QFileDialog, QDialog
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt
import jdatetime

from .wage_calculator_preview_view import WageCalculatorPreviewDialog
from ..wage_calculator.wage_calculator_logic import WageCalculatorLogic
from ..wage_calculator.wage_calculator_models import EmployeeInfo

from shared import show_warning_message_box, show_error_message_box, show_information_message_box


class WageCalculatorPreviewController:
    """
    Manages the entire lifecycle of the payslip generation and preview dialog.
    This is the "engine" for creating a new payslip.
    """

    def __init__(self, view: WageCalculatorPreviewDialog, logic: WageCalculatorLogic, employees: list[EmployeeInfo]):
        """
        Initializes the controller for a new payslip generation session.

        Args:
            logic: A reference to the shared wage calculation logic engine.
            employees: A list of employees to populate the selection dropdown.
        """
        self._logic = logic
        self._view = view
        self._newly_created_payroll_id: str | None = None

        # --- Connect signals from the _view to the controller's methods ---
        self._view.generate_requested.connect(self._generate_and_preview)
        self._view.print_requested.connect(self._handle_print)
        self._view.share_requested.connect(self._handle_share)

    def exec(self) -> int:
        """Shows the dialog modally and returns its result code when closed."""
        return self._view.exec()

    def _generate_and_preview(self, inputs: dict):
        """
        Handles the main 'Generate' action. This is the core workflow method.
        """
        try:
            employee_id = inputs['employee_id']
            start_date = inputs['start_date']

            # The logic needs the Jalali year to fetch the correct labor law constants.
            inputs['year'] = jdatetime.date.fromgregorian(date=start_date).year

            # 1. Call the logic layer to perform the complex calculation and save the record.
            # This returns the unique ID of the newly created payroll record.
            self._newly_created_payroll_id = self._logic.calculate_and_save_payslip(employee_id, inputs)

            # 2. Immediately fetch the clean, formatted DTO for that new record.
            payslip_data_for_display = self._logic.get_payslip_data_for_preview(self._newly_created_payroll_id)

            # 3. Tell the _view to switch to its "preview" state and display the data.
            self._view.show_preview(payslip_data_for_display)
            self._view.accept()  # Mark the dialog as successfully completed.

        except Exception as e:
            show_error_message_box(self._view, "خطا در محاسبه", f"فرایند محاسبه و ذخیره ناموفق بود:\n{e}")

    def _get_payslip_pixmap(self) -> QPixmap | None:
        """Helper method to safely get the current state of the payslip widget as an image."""
        if self._view and self._view.payslip_preview:
            return self._view.payslip_preview.grab()
        return None

    def _handle_print(self):
        """Handles the 'Print' action."""
        pixmap = self._get_payslip_pixmap()
        if not pixmap: return

        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self._view)

        if dialog.exec() == QDialog.Accepted:
            painter = QPainter(printer)
            # Get the printable area of the page
            rect = painter.viewport()
            # Scale the pixmap to fit the page while maintaining aspect ratio
            size = pixmap.size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            # Set the painter's viewport to the scaled size
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(pixmap.rect())
            # Draw the pixmap onto the page
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

    def _handle_share(self):
        """Saves a temporary PNG file and opens its containing folder."""
        pixmap = self._get_payslip_pixmap()
        if not pixmap: return

        try:
            # Create a unique, temporary file path
            temp_dir = tempfile.gettempdir()
            file_name = f"payslip_temp_{self._newly_created_payroll_id}.png"
            file_path = os.path.join(temp_dir, file_name)

            # Save the image
            pixmap.save(file_path, "PNG")

            show_information_message_box(self._view, "اشتراک گذاری",
                                         f"فایل فیش حقوقی در مسیر موقت زیر ذخیره شد.\n"
                                         f"پوشه برای شما باز خواهد شد تا بتوانید فایل را به اشتراک بگذارید.\n\n{file_path}")

            # Open the containing folder in a cross-platform way
            if sys.platform == "win32":
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(['open', '-R', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', os.path.dirname(file_path)])

        except Exception as e:
            show_error_message_box(self._view, "خطا", f"خطایی در ایجاد فایل موقت رخ داد:\n{e}")

    def get_view(self):
        """Returns the underlying dialog instance."""
        return self._view
