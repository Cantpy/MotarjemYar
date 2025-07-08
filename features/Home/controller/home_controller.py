"""
Controller for the home page, managing UI interactions and business logic.
"""
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (QWidget, QMessageBox, QTableWidgetItem, QPushButton, QHeaderView)
from features.Home import HomePageBackend, AnimationManager, HomePageUI
from shared import (return_resource, ColorDelegate, open_file, NotificationDialog, show_question_message_box)


class HomePageController(QWidget):
    """Main controller for the home page."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize paths
        self.customers_db = return_resource("databases", "customers.db")
        self.invoices_db = return_resource("databases", "invoices.db")

        # Initialize components
        self.ui = HomePageUI(self)
        self.backend = HomePageBackend(self.customers_db, self.invoices_db, self)
        self.animation_manager = AnimationManager(self)

        # Setup timer for periodic updates
        self._setup_timer()

        # Connect signals
        self._connect_signals()

        # Initialize data
        self._initialize_data()

    def _setup_timer(self):
        """Set up timer for updating time display."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.backend.update_datetime)
        self.timer.start(1000)  # Update every second

    def _connect_signals(self):
        """Connect backend signals to UI update methods."""
        self.backend.stats_updated.connect(self._update_dashboard_display)
        self.backend.invoices_updated.connect(self._update_invoices_table)
        self.backend.datetime_updated.connect(self._update_datetime_display)
        self.backend.error_occurred.connect(self._show_error_message)

    def _initialize_data(self):
        """Initialize all data on startup."""
        self.backend.update_datetime()
        self.backend.update_dashboard_stats()
        self.backend.update_invoices_table()

    def showEvent(self, event):
        """Handle widget show event - refresh data."""
        super().showEvent(event)
        self.backend.update_dashboard_stats()
        self.backend.update_invoices_table()

    def _update_datetime_display(self, date_str: str, time_str: str):
        """Update date and time labels."""
        self.ui.set_date_time(date_str, time_str)

    def _update_dashboard_display(self, stats: dict):
        """Update dashboard statistics with animations."""
        label_mappings = [
            (self.ui.get_total_customers_label(), stats['total_customers']),
            (self.ui.get_total_invoices_label(), stats['total_invoices']),
            (self.ui.get_today_invoices_label(), stats['today_invoices']),
            (self.ui.get_total_documents_label(), stats['total_documents']),
            (self.ui.get_available_documents_label(), stats['available_documents'])
        ]

        for label, value in label_mappings:
            self.animation_manager.animate_label(label, 0, value)

    def _update_invoices_table(self, processed_invoices: list):
        """Update the invoices table with processed data."""
        table = self.ui.get_invoices_table()

        # Setup table structure
        table.setRowCount(len(processed_invoices))
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "شماره فاکتور", "نام", "شماره تماس", "تاریخ تحویل",
            "مترجم", "مشاهده فاکتور", "آماده تحویل", "تحویل"
        ])

        # Configure table headers
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Populate table
        cell_colors = {}

        for row_idx, invoice_data in enumerate(processed_invoices):
            invoice = invoice_data['invoice']
            row_color = invoice_data['row_color']

            # Get background color
            bg_color = self._get_background_color(row_color)

            # Add data cells
            data_values = [
                invoice.invoice_number,
                invoice.name,
                invoice.phone,
                invoice.delivery_date,
                invoice.translator
            ]

            for col_idx, value in enumerate(data_values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QBrush(QColor("black")))
                table.setItem(row_idx, col_idx, item)

                if bg_color:
                    cell_colors[(row_idx, col_idx)] = bg_color

            # Add action buttons
            self._add_view_button(table, row_idx, invoice.pdf_file_path, bg_color, cell_colors)
            self._add_ready_delivery_button(table, row_idx, invoice.invoice_number, bg_color, cell_colors)
            self._add_delivery_confirmation_button(table, row_idx, invoice.invoice_number,
                                                   invoice.delivery_status, bg_color, cell_colors)

        # Apply custom styling
        table.setItemDelegate(ColorDelegate(cell_colors, table))

    def _get_background_color(self, row_color: str) -> QColor:
        """Get background color based on row color type."""
        color_map = {
            'overdue': QColor(255, 102, 102),  # Red
            'soon': QColor(255, 255, 200),  # Yellow
            'normal': QColor(255, 255, 255)  # White
        }
        return color_map.get(row_color, QColor(255, 255, 255))

    def _add_view_button(self, table, row_idx: int, pdf_path: str, bg_color: QColor, cell_colors: dict):
        """Add view PDF button to table row."""
        btn = QPushButton("نشان بده")
        btn.clicked.connect(lambda: open_file(pdf_path))
        table.setCellWidget(row_idx, 5, btn)

        if bg_color:
            cell_colors[(row_idx, 5)] = bg_color

    def _add_ready_delivery_button(self, table, row_idx: int, invoice_number: str,
                                   bg_color: QColor, cell_colors: dict):
        """Add ready for delivery notification button to table row."""
        btn = QPushButton("آماده تحویل")
        btn.clicked.connect(lambda: self._handle_ready_delivery(invoice_number))
        table.setCellWidget(row_idx, 6, btn)

        if bg_color:
            cell_colors[(row_idx, 6)] = bg_color

    def _add_delivery_confirmation_button(self, table, row_idx: int, invoice_number: str,
                                          delivery_status: int, bg_color: QColor, cell_colors: dict):
        """Add delivery confirmation button to table row."""
        if delivery_status == 1:
            btn = QPushButton("تحویل شده")
            btn.setEnabled(False)
            btn.setStyleSheet("background-color: #90EE90;")  # Light green
        else:
            btn = QPushButton("تحویل")
            btn.clicked.connect(lambda: self._handle_delivery_confirmation(invoice_number))

        table.setCellWidget(row_idx, 7, btn)

        if bg_color:
            cell_colors[(row_idx, 7)] = bg_color

    def _handle_ready_delivery(self, invoice_number: str):
        """Handle ready for delivery button click."""
        title = "اطلاع‌رسانی آماده تحویل"
        message = "آیا می‌خواهید به مشتری اطلاع دهید که فاکتور آماده تحویل است؟"
        button1 = "بله، می‌خواهم اطلاع دهم"
        button2 = "خیر"

        show_question_message_box(
            self, title, message, button1,
            lambda: self._show_notification_dialog(invoice_number), button2
        )

    def _handle_delivery_confirmation(self, invoice_number: str):
        """Handle delivery confirmation button click."""
        title = "تأیید تحویل"
        message = "آیا مشتری فاکتور خود را دریافت کرده است؟"
        button1 = "بله"
        button2 = "خیر"

        def handle_confirmation():
            success = self.backend.mark_invoice_delivered(invoice_number)
            if success:
                QMessageBox.information(self, "موفقیت", "فاکتور به عنوان تحویل شده علامت‌گذاری شد.")
            else:
                QMessageBox.warning(self, "خطا", "فاکتور مورد نظر یافت نشد.")

        show_question_message_box(self, title, message, button1, handle_confirmation(), button2)

    def _show_notification_dialog(self, invoice_number: str):
        """Show SMS/Email notification dialog."""
        dialog = NotificationDialog(invoice_number, self.invoices_db, self.customers_db, self)
        dialog.exec_()

    def _show_error_message(self, title: str, message: str):
        """Show error message box."""
        QMessageBox.critical(self, title, message)

    def cleanup(self):
        """Clean up resources when closing."""
        self.timer.stop()
        self.animation_manager.stop_all_animations()
        self.backend.db_manager.close()
