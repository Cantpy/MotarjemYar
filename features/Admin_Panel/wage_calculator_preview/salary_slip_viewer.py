# features/Admin_Panel/wage_calculator_preview/salary_slip_viewer.py

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QFont, QPen, QColor
from PySide6.QtCore import Qt, QRect

# --- MODIFIED: Import EmploymentType to use in logic ---
from features.Admin_Panel.wage_calculator.wage_calculator_models import PayslipData, EmploymentType
from shared.utils.persian_tools import to_persian_numbers


class SalarySlipViewer(QWidget):
    """
    Multi-type salary slip viewer supporting:
    - Full-time (Earning/Deduction table)
    - Part-time (adds work hours/days)
    - Commission-based (invoice table)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.payslip_data: PayslipData | None = None
        self.setMinimumSize(800, 700)
        self.setStyleSheet("background-color: white;")

    # -----------------------------
    # Public API
    # -----------------------------
    def populate(self, data: PayslipData):
        self.payslip_data = data
        self.update()

    # -----------------------------
    # Core Painting Logic
    # -----------------------------
    def paintEvent(self, event):
        if not self.payslip_data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Shared dimensions
        width = self.width()
        height = self.height()
        margin_left = 40
        margin_right = 40
        margin_top = 20
        content_width = width - margin_left - margin_right

        # Fonts
        self._fonts = {
            "header": QFont("B Nazanin", 16, QFont.Weight.Bold),
            "sub_header": QFont("B Nazanin", 12),
            "label": QFont("B Nazanin", 11),
            "bold_label": QFont("B Nazanin", 11, QFont.Weight.Bold),
            "data": QFont("B Nazanin", 10),
            "total": QFont("B Nazanin", 12, QFont.Weight.Bold),
        }

        y_pos = margin_top + 20
        y_pos = self._draw_header(painter, y_pos, content_width, margin_left)
        y_pos = self._draw_employee_info(painter, y_pos, content_width, margin_left, width)
        y_pos += 30

        # --- MODIFIED: Draw table based on actual employment type from DTO ---
        etype = self.payslip_data.employment_type
        if etype == EmploymentType.FULL_TIME:
            y_pos = self._draw_fulltime_table(painter, y_pos, content_width, margin_left)
        elif etype == EmploymentType.PART_TIME:
            y_pos = self._draw_parttime_table(painter, y_pos, content_width, margin_left)
        elif etype == EmploymentType.COMMISSION:
            y_pos = self._draw_commission_table(painter, y_pos, content_width, margin_left)
        else:
            painter.drawText(margin_left, y_pos, "❌ Unknown employment type")

        self._draw_footer(painter, height, width, margin_left, content_width)

    # -----------------------------
    # Header Section
    # -----------------------------
    def _draw_header(self, painter, y_pos, content_width, margin_left):
        painter.setFont(self._fonts["header"])
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(QRect(margin_left, y_pos, content_width, 30),
                         Qt.AlignmentFlag.AlignHCenter, "فیش حقوقی")

        y_pos += 40
        painter.setFont(self._fonts["sub_header"])

        office = self.payslip_data.translation_office
        if office:
            painter.drawText(QRect(margin_left, y_pos, content_width, 25),
                             Qt.AlignmentFlag.AlignHCenter, office.name)
            y_pos += 25
            info = f"شماره ثبت: {to_persian_numbers(office.registration)}   مدیر: {office.manager}   تلفن: {to_persian_numbers(office.phone)}"
            painter.setFont(self._fonts["data"])
            painter.drawText(QRect(margin_left, y_pos, content_width, 25),
                             Qt.AlignmentFlag.AlignHCenter, info)
        else:
            painter.drawText(QRect(margin_left, y_pos, content_width, 25),
                             Qt.AlignmentFlag.AlignHCenter, "شرکت دارالترجمه رسمی")

        return y_pos + 45

    # -----------------------------
    # Employee Info
    # -----------------------------
    def _draw_employee_info(self, painter, y_pos, content_width, margin_left, width):
        painter.setFont(self._fonts["label"])

        info_rect_right = QRect(width - margin_left - 300, y_pos, 300, 25)
        painter.drawText(info_rect_right, Qt.AlignmentFlag.AlignRight,
                         f"نام کارمند: {self.payslip_data.employee_name}")

        info_rect_center = QRect(width // 2 - 150, y_pos, 300, 25)
        painter.drawText(info_rect_center, Qt.AlignmentFlag.AlignHCenter,
                         f"کد ملی: {to_persian_numbers(self.payslip_data.employee_national_id)}")

        info_rect_left = QRect(margin_left, y_pos, 300, 25)
        painter.drawText(info_rect_left, Qt.AlignmentFlag.AlignLeft,
                         f"کد پرسنلی: {to_persian_numbers(self.payslip_data.employee_code)}")

        y_pos += 30
        painter.setFont(self._fonts["sub_header"])
        painter.drawText(QRect(margin_left, y_pos, content_width, 25),
                         Qt.AlignmentFlag.AlignHCenter,
                         f"دوره پرداخت: {self.payslip_data.pay_period_str}")
        return y_pos

    # -----------------------------
    # Full-Time Table (Earnings/Deductions)
    # -----------------------------
    def _draw_fulltime_table(self, painter, y_pos, content_width, margin_left):
        table_top = y_pos + 50
        table_height = 380
        col_width = (content_width - 20) // 2
        col_left_x = margin_left
        col_right_x = margin_left + col_width + 20

        # Table frame
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        table_rect = QRect(margin_left, table_top, content_width, table_height)
        painter.drawRect(table_rect)
        painter.drawLine(col_right_x, table_top, col_right_x, table_top + table_height)

        # Column headers
        painter.setFont(self._fonts["bold_label"])
        header_y = table_top + 15
        painter.drawText(QRect(col_right_x, header_y, col_width, 25), Qt.AlignmentFlag.AlignHCenter, "حقوق و مزایا")
        painter.drawText(QRect(col_left_x, header_y, col_width, 25), Qt.AlignmentFlag.AlignHCenter, "کسورات")

        sub_header_y = header_y + 35
        painter.setFont(self._fonts["data"])
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.drawText(QRect(col_right_x + 120, sub_header_y, col_width - 180, 20),
                         Qt.AlignmentFlag.AlignRight, "شرح")
        painter.drawText(QRect(col_right_x + 25, sub_header_y, col_width - 30, 20),
                         Qt.AlignmentFlag.AlignLeft, "مبلغ (تومان)")
        painter.drawText(QRect(col_left_x + 120, sub_header_y, col_width - 180, 20),
                         Qt.AlignmentFlag.AlignRight, "شرح")
        painter.drawText(QRect(col_left_x + 25, sub_header_y, col_width - 30, 20),
                         Qt.AlignmentFlag.AlignLeft, "مبلغ (تومان)")

        # Data rows
        earnings = sorted([c for c in self.payslip_data.components if c.type == "Earning"], key=lambda x: x.name)
        deductions = sorted([c for c in self.payslip_data.components if c.type == "Deduction"], key=lambda x: x.name)

        row_height = 28
        data_start_y = sub_header_y + 30
        painter.setPen(Qt.GlobalColor.black)

        for i, item in enumerate(earnings):
            label = item.display_name or item.name
            amount = to_persian_numbers(f"{item.amount:,.0f}")
            y = data_start_y + i * row_height
            painter.drawText(QRect(col_right_x + 120, y, col_width - 180, row_height),
                             Qt.AlignmentFlag.AlignRight, label)
            painter.drawText(QRect(col_right_x + 25, y, col_width - 30, row_height),
                             Qt.AlignmentFlag.AlignLeft, amount)

        for i, item in enumerate(deductions):
            label = item.display_name or item.name
            amount = to_persian_numbers(f"{item.amount:,.0f}")
            y = data_start_y + i * row_height
            painter.drawText(QRect(col_left_x + 120, y, col_width - 180, row_height),
                             Qt.AlignmentFlag.AlignRight, label)
            painter.drawText(QRect(col_left_x + 25, y, col_width - 30, row_height),
                             Qt.AlignmentFlag.AlignLeft, amount)

        # Totals
        totals_y = table_top + table_height - 45
        painter.setFont(self._fonts["bold_label"])
        painter.setPen(Qt.GlobalColor.black)

        painter.drawText(QRect(col_right_x, totals_y, col_width, 28),
                         Qt.AlignmentFlag.AlignRight,
                         f"جمع مزایا: {to_persian_numbers(f'{self.payslip_data.gross_income:,.0f}')}")
        painter.drawText(QRect(col_left_x, totals_y, col_width, 28),
                         Qt.AlignmentFlag.AlignRight,
                         f"جمع کسورات: {to_persian_numbers(f'{self.payslip_data.total_deductions:,.0f}')}")

        # Net Pay
        painter.setPen(QPen(QColor("#006400"), 2))
        painter.setFont(self._fonts["total"])
        net_y = table_top + table_height + 25
        painter.drawText(QRect(margin_left, net_y, content_width, 40), Qt.AlignmentFlag.AlignHCenter,
                         f"خالص پرداختی: {to_persian_numbers(f'{self.payslip_data.net_income:,.0f}')} تومان")
        return net_y + 60

    # -----------------------------
    # Part-Time Table
    # -----------------------------
    # --- MODIFIED: Implemented part-time specific info ---
    def _draw_parttime_table(self, painter, y_pos, content_width, margin_left):
        net_y_pos = self._draw_fulltime_table(painter, y_pos, content_width, margin_left)

        # Add hours/days section below the net pay
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(self._fonts["bold_label"])
        worked_info = ""
        if self.payslip_data.hours_worked is not None and self.payslip_data.hours_worked > 0:
            worked_info = f"{to_persian_numbers(float(self.payslip_data.hours_worked))} ساعت کاری"

        if worked_info:
            painter.drawText(QRect(margin_left, net_y_pos - 40, content_width, 30),
                             Qt.AlignmentFlag.AlignHCenter, f"مدت زمان کارکرد: {worked_info}")
        return net_y_pos + 40

    # -----------------------------
    # Commission Table
    # -----------------------------
    # --- MODIFIED: Implemented commission table drawing ---
    def _draw_commission_table(self, painter, y_pos, content_width, margin_left):
        painter.setFont(self._fonts["bold_label"])
        painter.setPen(Qt.GlobalColor.black)

        y_pos += 40
        painter.drawText(QRect(margin_left, y_pos, content_width, 25), Qt.AlignmentFlag.AlignHCenter,
                         "جزئیات کارمزد ترجمه")
        y_pos += 30

        cols = ["شماره فاکتور", "نام مشتری", "مبلغ کل ترجمه (تومان)", "سهم مترجم (تومان)"]
        col_widths = [content_width * 0.2, content_width * 0.3, content_width * 0.25, content_width * 0.25]
        x_pos = margin_left

        # Headers
        for i, col in enumerate(cols):
            painter.drawRect(x_pos, y_pos, col_widths[i], 30)
            painter.drawText(QRect(x_pos, y_pos, col_widths[i], 30), Qt.AlignmentFlag.AlignCenter, col)
            x_pos += col_widths[i]

        y_pos += 30
        painter.setFont(self._fonts["data"])
        painter.setPen(Qt.GlobalColor.black)
        row_h = 28

        if not self.payslip_data.commissions:
            painter.drawText(QRect(margin_left, y_pos, content_width, 30), Qt.AlignmentFlag.AlignCenter,
                             "موردی برای نمایش وجود ندارد.")
            y_pos += 30
        else:
            for row in self.payslip_data.commissions:
                x_pos = margin_left
                # Row data
                data_points = [
                    to_persian_numbers(str(row.invoice_number)),
                    row.customer_name,
                    to_persian_numbers(f"{row.total_price:,.0f}"),
                    to_persian_numbers(f"{row.translator_share:,.0f}")
                ]
                for i, data in enumerate(data_points):
                    painter.drawRect(x_pos, y_pos, col_widths[i], row_h)
                    painter.drawText(QRect(x_pos + 5, y_pos, col_widths[i] - 10, row_h),
                                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter, data)
                    x_pos += col_widths[i]
                y_pos += row_h

        y_pos += 20  # Spacer
        # --- Draw summary table for totals ---
        y_pos = self._draw_fulltime_table(painter, y_pos, content_width, margin_left)
        return y_pos + 40


    # -----------------------------
    # Footer Section
    # -----------------------------
    def _draw_footer(self, painter, height, width, margin_left, content_width):
        painter.setFont(self._fonts["data"])
        painter.setPen(Qt.GlobalColor.black)
        issuer_text = f"صادر کننده: {self.payslip_data.issuer}"
        painter.drawText(QRect(width - 350, height - 50, 300, 25),
                         Qt.AlignmentFlag.AlignRight, issuer_text)
