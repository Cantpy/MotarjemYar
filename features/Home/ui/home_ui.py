"""
UI components for the home page using PySide6.
"""
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QSizePolicy, QSpacerItem
)
from typing import Dict, List, Any, Optional, Callable


class StatCard(QFrame):
    """A reusable card widget for displaying statistics."""

    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        layout = QVBoxLayout(self)

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("IRANSans", 10))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Value label
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("IRANSans", 20, QFont.Weight.Bold))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        """Update the value displayed on the card."""
        self.value_label.setText(value)

    def get_value_label(self) -> QLabel:
        """Get the value label for animations."""
        return self.value_label


class DateTimeCard(QFrame):
    """Card widget for displaying date and time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        layout = QVBoxLayout(self)

        # Date label
        self.date_label = QLabel("سه شنبه ۲۴ بهمن ۱۴۰۳")
        font = QFont("IRANSans", 11, QFont.Weight.Bold)
        self.date_label.setFont(font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)

        # Time label
        self.time_label = QLabel("ساعت با ثانیه")
        self.time_label.setFont(font)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

    def set_date(self, date_str: str):
        """Update the date display."""
        self.date_label.setText(date_str)

    def set_time(self, time_str: str):
        """Update the time display."""
        self.time_label.setText(time_str)


class DocumentStatsCard(QFrame):
    """Card widget for displaying document statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        layout = QVBoxLayout(self)

        # Most repeated document
        self.most_repeated_title = QLabel("پرتکرارترین مدرک")
        self.most_repeated_title.setFont(QFont("IRANSans", 10))
        self.most_repeated_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.most_repeated_title)

        self.most_repeated_value = QLabel("TextLabel")
        self.most_repeated_value.setFont(QFont("IRANSans", 14, QFont.Weight.Bold))
        self.most_repeated_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.most_repeated_value)

        # Most repeated document this month
        self.month_repeated_title = QLabel("پرتکرارترین مدرک در این ماه")
        self.month_repeated_title.setFont(QFont("IRANSans", 10))
        self.month_repeated_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.month_repeated_title)

        self.month_repeated_value = QLabel("TextLabel")
        self.month_repeated_value.setFont(QFont("IRANSans", 14, QFont.Weight.Bold))
        self.month_repeated_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.month_repeated_value)

    def set_most_repeated(self, value: str):
        """Set the most repeated document value."""
        self.most_repeated_value.setText(value)

    def set_month_repeated(self, value: str):
        """Set the most repeated document this month value."""
        self.month_repeated_value.setText(value)


class InvoiceTableWidget(QTableWidget):
    """Custom table widget for displaying invoices."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._setup_table()

    def _setup_table(self):
        """Setup table structure and headers."""
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "شماره فاکتور", "نام", "شماره تماس", "تاریخ تحویل",
            "مترجم", "مشاهده فاکتور", "آماده تحویل", "تحویل"
        ])

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

    def populate_data(self, invoice_data: List[Dict[str, Any]],
                      button_callbacks: Dict[str, Callable] = None):
        """Populate table with invoice data."""
        self.setRowCount(len(invoice_data))

        for row_idx, invoice in enumerate(invoice_data):
            # Add text data
            for col_idx, key in enumerate(['invoice_number', 'name', 'phone', 'delivery_date', 'translator']):
                item = QTableWidgetItem(str(invoice.get(key, '')))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QBrush(QColor("black")))
                self.setItem(row_idx, col_idx, item)

            # Add buttons
            if button_callbacks:
                # View button
                view_btn = QPushButton("نشان بده")
                if 'view_callback' in button_callbacks:
                    view_btn.clicked.connect(
                        lambda checked, path=invoice.get('pdf_file_path', ''):
                        button_callbacks['view_callback'](path)
                    )
                self.setCellWidget(row_idx, 5, view_btn)

                # Ready for delivery button
                ready_btn = QPushButton("آماده تحویل")
                if 'ready_callback' in button_callbacks:
                    ready_btn.clicked.connect(
                        lambda checked, inv_num=invoice.get('invoice_number', 0):
                        button_callbacks['ready_callback'](inv_num)
                    )
                self.setCellWidget(row_idx, 6, ready_btn)

                # Delivery confirmation button
                delivery_status = invoice.get('delivery_status', 0)
                if delivery_status == 1:
                    delivery_btn = QPushButton("تحویل شده")
                    delivery_btn.setEnabled(False)
                    delivery_btn.setStyleSheet("background-color: #90EE90;")
                else:
                    delivery_btn = QPushButton("تحویل")
                    if 'delivery_callback' in button_callbacks:
                        delivery_btn.clicked.connect(
                            lambda checked, inv_num=invoice.get('invoice_number', 0):
                            button_callbacks['delivery_callback'](inv_num)
                        )
                self.setCellWidget(row_idx, 7, delivery_btn)

    def set_row_color(self, row: int, color: QColor):
        """Set background color for a specific row."""
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(QBrush(color))


class DashboardWidget(QWidget):
    """Main dashboard widget containing all statistics cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stat_cards = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the dashboard UI layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)

        # Left section - Date/Time and Customer stats
        left_layout = QVBoxLayout()

        # Date/Time card
        self.datetime_card = DateTimeCard()
        left_layout.addWidget(self.datetime_card)

        # Customer stats card
        self.customer_card = StatCard("تعداد کل مشتری‌ها")
        self.stat_cards['total_customers'] = self.customer_card
        left_layout.addWidget(self.customer_card)

        main_layout.addLayout(left_layout)

        # Center section - Main statistics grid
        center_frame = QFrame()
        center_frame.setFrameShape(QFrame.Shape.StyledPanel)
        center_frame.setFrameShadow(QFrame.Shadow.Raised)

        grid_layout = QGridLayout(center_frame)

        # Available documents
        self.available_docs_card = StatCard("تعداد مدارک موجود")
        self.stat_cards['available_documents'] = self.available_docs_card
        grid_layout.addWidget(self.available_docs_card, 0, 0, 2, 1)

        # Today's invoices
        self.today_invoices_card = StatCard("فاکتورهای صادر شده امروز")
        self.stat_cards['today_invoices'] = self.today_invoices_card
        grid_layout.addWidget(self.today_invoices_card, 0, 1, 2, 1)

        # Total documents
        self.total_docs_card = StatCard("کل مدارک ترجمه شده")
        self.stat_cards['total_documents'] = self.total_docs_card
        grid_layout.addWidget(self.total_docs_card, 2, 0, 2, 1)

        # Total invoices
        self.total_invoices_card = StatCard("کل فاکتورهای صادر شده")
        self.stat_cards['total_invoices'] = self.total_invoices_card
        grid_layout.addWidget(self.total_invoices_card, 2, 1, 2, 1)

        # Add spacers
        grid_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), 0, 2)

        main_layout.addWidget(center_frame)

        # Right section - Document statistics
        self.document_stats_card = DocumentStatsCard()
        main_layout.addWidget(self.document_stats_card)

    def update_stats(self, stats: Dict[str, Any]):
        """Update all statistics cards with new data."""
        for stat_name, card in self.stat_cards.items():
            if stat_name in stats:
                card.set_value(str(stats[stat_name]))

    def get_stat_card(self, stat_name: str) -> Optional[StatCard]:
        """Get a specific stat card by name."""
        return self.stat_cards.get(stat_name)

    def update_datetime(self, date_str: str, time_str: str):
        """Update date and time display."""
        self.datetime_card.set_date(date_str)
        self.datetime_card.set_time(time_str)

    def update_document_stats(self, most_repeated: str, month_repeated: str):
        """Update document statistics."""
        self.document_stats_card.set_most_repeated(most_repeated)
        self.document_stats_card.set_month_repeated(month_repeated)

    def get_total_customers_label(self):
        """Get the total customers label widget for animations."""
        return self.customer_card.get_value_label()

    def get_total_invoices_label(self):
        """Get the total invoices label widget for animations."""
        return self.total_invoices_card.get_value_label()

    def get_today_invoices_label(self):
        """Get the today invoices label widget for animations."""
        return self.today_invoices_card.get_value_label()

    def get_total_documents_label(self):
        """Get the total documents label widget for animations."""
        return self.total_docs_card.get_value_label()

    def get_available_documents_label(self):
        """Get the available documents label widget for animations."""
        return self.available_docs_card.get_value_label()

    def set_date_time(self, date_str: str, time_str: str):
        """Set date and time display (alternative method name)."""
        self.update_datetime(date_str, time_str)


class HomePageUI(QWidget):
    """Main home page UI widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.timer = QTimer(self)

    def _setup_ui(self):
        """Setup the main UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Dashboard section
        self.dashboard = DashboardWidget()
        main_layout.addWidget(self.dashboard)

        # Invoice table section
        self.invoice_table = InvoiceTableWidget()
        main_layout.addWidget(self.invoice_table)

    def setup_timer(self, callback: Callable):
        """Setup timer for periodic updates."""
        self.timer.timeout.connect(callback)
        self.timer.start(1000)  # Update every second

    def get_dashboard(self) -> DashboardWidget:
        """Get the dashboard widget."""
        return self.dashboard

    def get_invoice_table(self) -> InvoiceTableWidget:
        """Get the invoice table widget."""
        return self.invoice_table

    def update_dashboard_stats(self, stats: Dict[str, Any]):
        """Update dashboard statistics."""
        self.dashboard.update_stats(stats)

    def update_datetime(self, date_str: str, time_str: str):
        """Update date and time display."""
        self.dashboard.update_datetime(date_str, time_str)

    def update_document_stats(self, most_repeated: str, month_repeated: str):
        """Update document statistics."""
        self.dashboard.update_document_stats(most_repeated, month_repeated)

    def populate_invoice_table(self, invoice_data: List[Dict[str, Any]],
                               button_callbacks: Dict[str, Callable] = None):
        """Populate the invoice table with data."""
        self.invoice_table.populate_data(invoice_data, button_callbacks)

    def set_invoice_row_color(self, row: int, color: QColor):
        """Set color for a specific invoice row."""
        self.invoice_table.set_row_color(row, color)

    def set_date_time(self, date_str: str, time_str: str):
        """Set date and time display."""
        self.dashboard.update_datetime(date_str, time_str)

    def get_total_customers_label(self):
        """Get the total customers label widget."""
        return self.dashboard.get_total_customers_label()

    def get_total_invoices_label(self):
        """Get the total invoices label widget."""
        return self.dashboard.get_total_invoices_label()

    def get_today_invoices_label(self):
        """Get the today invoices label widget."""
        return self.dashboard.get_today_invoices_label()

    def get_total_documents_label(self):
        """Get the total documents label widget."""
        return self.dashboard.get_total_documents_label()

    def get_available_documents_label(self):
        """Get the available documents label widget."""
        return self.dashboard.get_available_documents_label()

    def get_invoices_table(self):
        """Get the invoices table widget."""
        return self.invoice_table
