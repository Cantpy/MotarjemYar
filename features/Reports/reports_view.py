# _view.py
import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QDateEdit,
    QPushButton, QFormLayout, QGroupBox, QTableView, QHeaderView,
    QLabel, QHBoxLayout, QFileDialog
)
from PySide6.QtCore import QDate, QAbstractTableModel, Qt, Slot
from PySide6.QtGui import QIcon
from pathlib import Path
import pyqtgraph as pg
import qtawesome as qta
from typing import List, Dict, Any, Optional


# --- Custom Table Model for Pandas DataFrame ---
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None


# --- Main Reports View ---
class ReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("صفحه گزارشات")
        self.setLayoutDirection(Qt.RightToLeft)

        # Store data for exporting
        self.current_dataframes = {}

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Filters ---
        filters_group = QGroupBox("فیلترها")
        filters_layout = QHBoxLayout()
        form_layout = QFormLayout()

        self.start_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy/MM/dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy/MM/dd")
        self.end_date_edit.setDate(QDate.currentDate())

        form_layout.addRow("از تاریخ:", self.start_date_edit)
        form_layout.addRow("تا تاریخ:", self.end_date_edit)

        self.generate_report_btn = QPushButton("تولید گزارش", icon=qta.icon('fa5s.sync'))

        filters_layout.addLayout(form_layout)
        filters_layout.addStretch()
        filters_layout.addWidget(self.generate_report_btn, alignment=Qt.AlignBottom)
        filters_group.setLayout(filters_layout)

        main_layout.addWidget(filters_group)

        # --- Tabs ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.tabs.setLayoutDirection(Qt.RightToLeft)

        self._create_financial_tab()
        self._create_translator_tab()
        self._create_customer_tab()
        self._create_user_activity_tab()

        # Add icons to tabs
        self.tabs.setTabIcon(0, qta.icon('fa5s.file-invoice-dollar'))
        self.tabs.setTabIcon(1, qta.icon('fa5s.user-tie'))
        self.tabs.setTabIcon(2, qta.icon('fa5s.users'))
        self.tabs.setTabIcon(3, qta.icon('fa5s.user-clock'))
        self._set_stylesheet()

    # --- Export Helper ---
    def _create_export_buttons(self, report_name):
        btn_layout = QHBoxLayout()
        pdf_btn = QPushButton("خروجی PDF", icon=qta.icon('fa5s.file-pdf', color='red'))
        excel_btn = QPushButton("خروجی Excel", icon=qta.icon('fa5s.file-excel', color='green'))

        pdf_btn.setProperty("report_name", report_name)
        excel_btn.setProperty("report_name", report_name)

        btn_layout.addStretch()
        btn_layout.addWidget(pdf_btn)
        btn_layout.addWidget(excel_btn)
        return btn_layout, pdf_btn, excel_btn

    # --- Financial Tab ---
    def _create_financial_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Left side - Chart
        self.financial_chart = pg.PlotWidget()
        self.financial_chart.setBackground('w')
        layout.addWidget(self.financial_chart, 2)  # 2/3 of space

        # Right side - Summary
        details_layout = QVBoxLayout()
        summary_group = QGroupBox("خلاصه مالی")
        self.financial_results_layout = QFormLayout(summary_group)
        self.total_revenue_label = QLabel("۰")
        self.net_income_label = QLabel("۰")
        self.paid_invoices_label = QLabel("۰")
        self.unpaid_invoices_label = QLabel("۰")
        self.financial_results_layout.addRow("درآمد کل:", self.total_revenue_label)
        self.financial_results_layout.addRow("درآمد خالص:", self.net_income_label)
        self.financial_results_layout.addRow("فاکتورهای پرداخت شده:", self.paid_invoices_label)
        self.financial_results_layout.addRow("فاکتورهای پرداخت نشده:", self.unpaid_invoices_label)

        export_buttons_layout, self.pdf_btn_fin, self.excel_btn_fin = self._create_export_buttons("financial")

        details_layout.addWidget(summary_group)
        details_layout.addStretch()
        details_layout.addLayout(export_buttons_layout)
        layout.addLayout(details_layout, 1)  # 1/3 of space

        self.tabs.addTab(tab, "گزارش مالی")

    def set_financial_data(self, data: Dict[str, Any]):
        self.current_dataframes["financial_summary"] = pd.DataFrame([data])

        # Update labels
        self.total_revenue_label.setText(f"{data.get('total_revenue') or 0:,} ریال")
        self.net_income_label.setText(f"{data.get('net_income') or 0:,} ریال")
        self.paid_invoices_label.setText(str(data.get('fully_paid_invoices') or 0))
        self.unpaid_invoices_label.setText(str(data.get('unpaid_invoices') or 0))

        # Update chart
        self.financial_chart.clear()
        net = data.get('net_income', 0)
        discount = data.get('total_discount', 0)
        advance = data.get('total_advance', 0)
        if net > 0 or discount > 0 or advance > 0:
            x = [1, 2]
            y = [data.get('total_revenue', 0), net]
            bargraph = pg.BarGraphItem(x=x, height=y, width=0.6, brush='b')
            self.financial_chart.addItem(bargraph)
            self.financial_chart.getAxis('bottom').setTicks([[(1, 'درآمد کل'), (2, 'درآمد خالص')]])
            self.financial_chart.setTitle("مقایسه درآمد کل و خالص")

    # --- Generic Table & Chart Tab ---
    def _create_table_chart_tab(self, name: str, title: str):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        top_layout = QHBoxLayout()
        table = QTableView()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        top_layout.addWidget(table, 2)

        chart = pg.PlotWidget()
        chart.setBackground('w')
        top_layout.addWidget(chart, 1)

        export_buttons_layout, pdf_btn, excel_btn = self._create_export_buttons(name)

        layout.addLayout(top_layout)
        layout.addLayout(export_buttons_layout)

        self.tabs.addTab(tab, title)
        return table, chart, pdf_btn, excel_btn

    def _create_translator_tab(self):
        self.translator_table, self.translator_chart, self.pdf_btn_trans, self.excel_btn_trans = self._create_table_chart_tab(
            "translator", "عملکرد مترجمین"
        )

    def set_translator_data(self, data: List[Dict[str, Any]]):
        if not data:
            self.translator_table.setModel(None)
            self.translator_chart.clear()
            self.current_dataframes['translator'] = pd.DataFrame()
            return

        df = pd.DataFrame(data)
        self.current_dataframes['translator'] = df

        # Table
        display_df = df.rename(columns={
            "translator_name": "نام مترجم",
            "total_revenue": "درآمد کل",
            "invoice_count": "تعداد فاکتور",
            "average_revenue_per_invoice": "میانگین درآمد/فاکتور"
        })
        self.translator_table.setModel(PandasModel(display_df))

        # Chart
        self.translator_chart.clear()
        df = df.sort_values('total_revenue', ascending=True)
        y = range(len(df))
        x = df['total_revenue']
        bargraph = pg.BarGraphItem(x=x, y=y, height=0.6, orientation='horizontal', brush='g')
        self.translator_chart.addItem(bargraph)
        self.translator_chart.getAxis('left').setTicks([list(zip(y, df['translator_name']))])
        self.translator_chart.setTitle("درآمد بر اساس مترجم")

    def _create_customer_tab(self):
        self.customer_table, self.customer_chart, self.pdf_btn_cust, self.excel_btn_cust = self._create_table_chart_tab(
            "customer", "مشتریان برتر"
        )

    def set_customer_data(self, data: List[Dict[str, Any]]):
        if not data:
            self.customer_table.setModel(None)
            self.customer_chart.clear()
            self.current_dataframes['customer'] = pd.DataFrame()
            return

        df = pd.DataFrame(data)
        self.current_dataframes['customer'] = df

        # Table
        display_df = df.rename(columns={
            "customer_name": "نام مشتری", "national_id": "کد ملی",
            "total_spent": "مجموع پرداختی", "invoice_count": "تعداد فاکتور"
        })
        self.customer_table.setModel(PandasModel(display_df))

        # Chart
        self.customer_chart.clear()
        df = df.sort_values('total_spent', ascending=True).head(10)  # show top 10 on chart
        y = range(len(df))
        x = df['total_spent']
        bargraph = pg.BarGraphItem(x=x, y=y, height=0.6, orientation='horizontal', brush='purple')
        self.customer_chart.addItem(bargraph)
        self.customer_chart.getAxis('left').setTicks([list(zip(y, df['customer_name']))])
        self.customer_chart.setTitle("مجموع پرداختی مشتریان")

    def _create_user_activity_tab(self):
        self.user_table, self.user_chart, self.pdf_btn_user, self.excel_btn_user = self._create_table_chart_tab(
            "user", "فعالیت کاربران"
        )

    def set_user_activity_data(self, data: List[Dict[str, Any]]):
        if not data:
            self.user_table.setModel(None)
            self.user_chart.clear()
            self.current_dataframes['user'] = pd.DataFrame()
            return

        df = pd.DataFrame(data)
        self.current_dataframes['user'] = df

        # Table
        df_display = df.copy()
        df_display['total_time_on_app_hours'] = df_display['total_time_on_app_hours'].round(2)
        df_display = df_display.rename(columns={
            "username": "نام کاربری", "display_name": "نام کامل",
            "invoice_count": "فاکتورهای صادر شده", "total_time_on_app_hours": "زمان فعالیت (ساعت)"
        })
        self.user_table.setModel(PandasModel(df_display))

        # Chart
        self.user_chart.clear()
        df_chart = df[df['invoice_count'] > 0].sort_values('invoice_count')
        y = range(len(df_chart))
        x = df_chart['invoice_count']
        if not df_chart.empty:
            bargraph = pg.BarGraphItem(x=x, y=y, height=0.6, orientation='horizontal', brush='orange')
            self.user_chart.addItem(bargraph)
            self.user_chart.getAxis('left').setTicks([list(zip(y, df_chart['username']))])
            self.user_chart.setTitle("تعداد فاکتورهای صادر شده توسط کاربر")

    # --- File Dialog Helper ---
    def get_save_path(self, file_type: str) -> Optional[str]:
        extension = "Excel Files (*.xlsx)" if file_type == "excel" else "PDF Files (*.pdf)"
        path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل", "", extension)
        return path

    def _set_stylesheet(self):
        self.setStyleSheet(""""
           /* styles.qss */
            QWidget {
                font-family: 'IranSans', 'Vazir';
                font-size: 11pt;
                background-color: #f0f4f7;
                color: #333;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0d0e0;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #e6eef5;
                border-radius: 4px;
                color: #2a5282;
            }
            
            QLabel {
                color: #444;
            }
            
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                border: 1px solid #005a9e;
            }
            
            QPushButton:hover {
                background-color: #005a9e;
            }
            
            QPushButton:pressed {
                background-color: #003a64;
            }
            
            QDateEdit {
                background-color: white;
                border: 1px solid #c0d0e0;
                padding: 5px;
                border-radius: 5px;
            }
            
            QDateEdit::drop-down {
                border-left: 1px solid #c0d0e0;
            }
            
            QTableView {
                background-color: white;
                border: 1px solid #c0d0e0;
                gridline-color: #d0e0f0;
                border-radius: 5px;
            }
            
            QTableView QHeaderView::section {
                background-color: #2a5282;
                color: white;
                padding: 4px;
                border: none;
                font-weight: bold;
            }
            
            QTabWidget::pane {
                border: 1px solid #c0d0e0;
                border-radius: 5px;
                padding: 10px;
            }
            
            QTabBar::tab {
                background: #e6eef5;
                border: 1px solid #c0d0e0;
                border-bottom-color: #c0d0e0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
            }
            
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: white;
            } 
        """)
