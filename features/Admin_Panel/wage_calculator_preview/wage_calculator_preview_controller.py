# features/Admin_Panel/wage_calculator_preview/wage_calculator_preview_controller.py

import sys
from PySide6.QtWidgets import QDialog, QFileDialog
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt
import jdatetime

from features.Admin_Panel.wage_calculator_preview.wage_calculator_preview_view import WageCalculatorPreviewDialog
from features.Admin_Panel.wage_calculator.wage_calculator_logic import WageCalculatorLogic
from features.Admin_Panel.wage_calculator.wage_calculator_models import PayslipData

from shared import show_error_message_box, show_information_message_box


class WageCalculatorPreviewController:
    """
    Manages the entire lifecycle of the payslip generation and preview dialog.
    This is the "engine" for creating a new payslip.
    """

    def __init__(self, view: WageCalculatorPreviewDialog, logic: WageCalculatorLogic):
        """
        Initializes the controller for a new payslip generation session.
        """
        self._logic = logic
        self._view = view
        self._current_payslip_data: PayslipData | None = None

        # --- Connect signals from the _view to the controller's methods ---
        self._view.generate_requested.connect(self._generate_and_preview)
        self._view.print_requested.connect(self._handle_print)
        self._view.save_as_requested.connect(self._handle_save_as)
        self._view.accepted.connect(self._handle_final_save)  # User clicked "Confirm & Save"

    def exec(self) -> int:
        """Shows the dialog modally and returns its result code when closed."""
        return self._view.exec()

    def _generate_and_preview(self, inputs: dict):
        """
        Handles the 'Generate' action. It calculates the data but does not save it.
        """
        try:
            # 1. Call the logic method from the core package to get the calculated DTO.
            self._current_payslip_data = self._logic.calculate_payslip_for_preview(inputs)

            # 2. Tell the view to switch to its "preview" state and display the data.
            self._view.show_preview(self._current_payslip_data)

        except Exception as e:
            print(f'error in generating preview: {e}', file=sys.stderr)
            show_error_message_box(self._view, "خطا در محاسبه", f"فرایند پیش‌نمایش ناموفق بود:\n{e}")

    def _get_payslip_pixmap(self) -> QPixmap | None:
        """Helper method to safely get the current state of the payslip widget as an image."""
        if self._view and self._view.payslip_preview:
            return self._view.payslip_preview.grab()
        return None

    def _handle_print(self):
        """Handles the 'Print' action."""
        pixmap = self._get_payslip_pixmap()
        if not pixmap: return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self._view)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._paint_pixmap_on_printer(pixmap, printer)

    def _handle_save_as(self):
        """Saves the payslip preview as a PNG or PDF file."""
        pixmap = self._get_payslip_pixmap()
        if not pixmap or not self._current_payslip_data:
            return

        default_filename = f"payslip_{self._current_payslip_data.employee_name.replace(' ', '_')}_{jdatetime.date.today():%Y-%m}.png"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self._view,
            "ذخیره فایل فیش حقوقی",
            default_filename,
            "PNG Image (*.png);;PDF Document (*.pdf)"
        )

        if not file_path:
            return

        try:
            if selected_filter == "PNG Image (*.png)":
                if not file_path.lower().endswith('.png'):
                    file_path += '.png'
                pixmap.save(file_path, "PNG")
                show_information_message_box(self._view, "موفقیت",
                                             f"فایل PNG با موفقیت در مسیر زیر ذخیره شد:\n{file_path}")

            elif selected_filter == "PDF Document (*.pdf)":
                if not file_path.lower().endswith('.pdf'):
                    file_path += '.pdf'
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QPrinter.A5)
                printer.setPageOrientation(QPrinter.Landscape)

                self._paint_pixmap_on_printer(pixmap, printer)
                show_information_message_box(self._view, "موفقیت",
                                             f"فایل PDF با موفقیت در مسیر زیر ذخیره شد:\n{file_path}")

        except Exception as e:
            show_error_message_box(self._view, "خطا در ذخیره فایل", f"خطایی در هنگام ذخیره فایل رخ داد:\n{e}")

    def _paint_pixmap_on_printer(self, pixmap: QPixmap, printer: QPrinter):
        """Reusable logic to draw the payslip pixmap onto a QPrinter device (for PDF or printing)."""
        painter = QPainter(printer)
        rect = painter.viewport()
        size = pixmap.size()
        size.scale(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
        painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
        painter.setWindow(pixmap.rect())
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

    def _handle_final_save(self):
        """
        This is triggered when the dialog is 'accepted'. It performs the final save.
        """
        if not self._current_payslip_data:
            show_error_message_box(self._view, "خطای داخلی", "هیچ اطلاعاتی برای ذخیره وجود ندارد.")
            return

        try:
            self._logic.save_payslip_record(self._current_payslip_data)
            self._logic.audit_payroll(self._current_payslip_data)

            show_information_message_box(self._view, "موفقیت", "فیش حقوقی با موفقیت در سیستم ذخیره شد.")
        except Exception as e:
            print(f'error in handling the final save: {e}', file=sys.stderr)
            show_error_message_box(self._view, "خطا در ذخیره", f"فرایند ذخیره نهایی ناموفق بود:\n{e}")
            self._view.reject()

    def get_view(self):
        """Returns the underlying dialog instance."""
        return self._view
