# controller.py
import dataclasses
import pandas as pd
from pathlib import Path
from PySide6.QtCore import Slot
from PySide6.QtGui import QPixmap

from features.Reports.reports_view import ReportsView
from features.Reports.reports_logic import ReportsLogic
from file_exporter import FileExporter


class ReportsController:
    def __init__(self, view: ReportsView, logic: ReportsLogic, exporter: FileExporter):
        self.view = view
        self.logic = logic
        self.exporter = exporter
        self._connect_signals()

    def _connect_signals(self):
        self.view.generate_report_btn.clicked.connect(self.update_all_reports)
        # Connect export buttons
        self.view.pdf_btn_fin.clicked.connect(self.export_file)
        self.view.excel_btn_fin.clicked.connect(self.export_file)
        self.view.pdf_btn_trans.clicked.connect(self.export_file)
        self.view.excel_btn_trans.clicked.connect(self.export_file)
        self.view.pdf_btn_cust.clicked.connect(self.export_file)
        self.view.excel_btn_cust.clicked.connect(self.export_file)
        self.view.pdf_btn_user.clicked.connect(self.export_file)
        self.view.excel_btn_user.clicked.connect(self.export_file)

    def _get_dates(self):
        start_date = self.view.start_date_edit.date().toPython()
        end_date = self.view.end_date_edit.date().toPython()
        return start_date, end_date

    @Slot()
    def update_all_reports(self):
        start_date, end_date = self._get_dates()

        # Financial Report
        fin_data = self.logic.generate_financial_report(start_date, end_date)
        self.view.set_financial_data(dataclasses.asdict(fin_data))

        # Translator Report
        trans_data = self.logic.generate_translator_performance_report(start_date, end_date)
        self.view.set_translator_data([dataclasses.asdict(item) for item in trans_data])

        # Customer Report
        cust_data = self.logic.generate_top_customers_report(start_date, end_date)
        self.view.set_customer_data([dataclasses.asdict(item) for item in cust_data])

        # User Activity Report
        user_data = self.logic.generate_user_activity_report(start_date, end_date)
        self.view.set_user_activity_data([dataclasses.asdict(item) for item in user_data])

    @Slot()
    def export_file(self):
        button = self.view.sender()
        report_name = button.property("report_name")
        file_type = "pdf" if "pdf" in button.text().lower() else "excel"

        df = self.view.current_dataframes.get(report_name)
        if df is None or df.empty:
            print(f"No data available to export for {report_name}")
            return

        save_path = self.view.get_save_path(file_type)
        if not save_path:
            return

        if file_type == "excel":
            self.exporter.to_excel(df, save_path)
        else:  # PDF
            chart_widget = getattr(self.view, f"{report_name}_chart", None)

            # Save chart to a temporary image file
            temp_chart_path = Path("./temp_chart.png")
            if chart_widget:
                pixmap = chart_widget.grab()
                pixmap.save(str(temp_chart_path))

            start_date, end_date = self._get_dates()
            report_info = f"گزارش از تاریخ {start_date} تا {end_date}"

            title_map = {
                "financial": "گزارش خلاصه مالی",
                "translator": "گزارش عملکرد مترجمین",
                "customer": "گزارش مشتریان برتر",
                "user": "گزارش فعالیت کاربران"
            }
            title = title_map.get(report_name, "گزارش")

            # For financial report, use a simplified dataframe
            if report_name == 'financial':
                summary_df = self.view.current_dataframes.get("financial_summary")
                summary_df.columns = ["درآمد کل", "تخفیف", "پیش پرداخت", "درآمد خالص", "فاکتورهای پرداخت شده",
                                      "پرداخت نشده"]
                self.exporter.to_pdf(title, summary_df.T, report_info, temp_chart_path, save_path)
            else:
                self.exporter.to_pdf(title, df, report_info, temp_chart_path, save_path)

            if temp_chart_path.exists():
                temp_chart_path.unlink()  # Clean up the temp image
