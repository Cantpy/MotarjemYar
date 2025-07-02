import json
import sqlite3

import jdatetime
from PySide6.QtCore import QTimer, QTime, Qt, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (QWidget, QMessageBox, QTableWidgetItem, QPushButton, QHeaderView)

from shared import (return_resource, to_persian_number, NotificationDialog, show_question_message_box,
                    parse_jalali_date, ColorDelegate, open_pdf)


customers_database = return_resource("databases", "customers.db")
invoices_database = return_resource("databases", "invoices.db")
documents_database = return_resource('databases', "documents.db")


class HomePage(QWidget):
    """Main home page widget displaying dashboard and invoice information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        self._initialize_data()

    def _setup_ui(self):
        """Initialize the UI components."""
        from qt_designer_ui.ui_home_page import Ui_Form
        self.ui = Ui_Form()
        self.ui.setupUi(self)

    def _setup_timer(self):
        """Set up timer for updating time display."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_and_date)
        self.timer.start(1000)  # Update every second

    def _initialize_data(self):
        """Initialize dashboard data and load invoices."""
        self.update_time_and_date()
        self.update_dashboard()
        self.load_invoices_into_table()

    def showEvent(self, event):
        """Handle widget show event - refresh dashboard and invoices."""
        super().showEvent(event)
        self.update_dashboard()
        self.load_invoices_into_table()

    def update_time_and_date(self):
        """Update the time and date labels with Persian formatting."""
        self._update_time_display()
        self._update_date_display()

    def _update_time_display(self):
        """Update the time label with current time in Persian numerals."""
        current_time = QTime.currentTime().toString("HH:mm:ss")
        persian_time = to_persian_number(current_time)
        self.ui.time_label.setText(persian_time)

    def _update_date_display(self):
        """Update the date label with Persian date formatting."""
        jalali_date = jdatetime.date.today()

        persian_weekdays = {
            "Saturday": "شنبه", "Sunday": "یکشنبه", "Monday": "دوشنبه",
            "Tuesday": "سه‌شنبه", "Wednesday": "چهارشنبه",
            "Thursday": "پنج‌شنبه", "Friday": "جمعه"
        }

        persian_months = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
            5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
            9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند"
        }

        weekday = persian_weekdays[jalali_date.strftime("%A")]
        month = persian_months[jalali_date.month]

        date_str = (f"{weekday}، {to_persian_number(jalali_date.day)} "
                    f"{month} {to_persian_number(jalali_date.year)}")
        self.ui.date_label.setText(date_str)

    def update_dashboard(self):
        """Update all dashboard statistics with animations."""
        try:
            stats = self._get_dashboard_statistics()
            self._animate_dashboard_labels(stats)
        except Exception as e:
            QMessageBox.critical(self, "خطای داشبورد", f"خطا در بروزرسانی داشبورد: {e}")

    def _get_dashboard_statistics(self):
        """Retrieve all dashboard statistics from databases."""
        stats = {}

        # Get customer count
        with sqlite3.connect(customers_database) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            stats['total_customers'] = cursor.fetchone()[0]

        # Get invoice statistics
        with sqlite3.connect(invoices_database) as conn:
            cursor = conn.cursor()

            # Total invoices
            cursor.execute("SELECT COUNT(*) FROM issued_invoices")
            stats['total_invoices'] = cursor.fetchone()[0]

            # Today's invoices
            today_jalali = jdatetime.date.today().strftime("%Y/%m/%d")
            cursor.execute(
                "SELECT COUNT(*) FROM issued_invoices WHERE issue_date LIKE ?",
                (f"{to_persian_number(today_jalali)}%",)
            )
            stats['today_invoices'] = cursor.fetchone()[0]

        # Get document counts
        doc_stats = self._get_document_counts()
        stats.update(doc_stats)

        return stats

    def _get_document_counts(self):
        """Count total and available documents from invoice items."""
        total_docs = 0
        available_docs = 0

        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ii.items, i.delivery_status
                    FROM invoice_items ii 
                    JOIN issued_invoices i ON ii.invoice_number = i.invoice_number
                """)
                rows = cursor.fetchall()

                for items_json, delivery_status in rows:
                    doc_count = self._parse_document_count(items_json)
                    total_docs += doc_count

                    if delivery_status == 0:  # Available status (not yet delivered)
                        available_docs += doc_count

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در خواندن اسناد: {e}")
            return {'total_documents': 0, 'available_documents': 0}

        return {
            'total_documents': total_docs,
            'available_documents': available_docs
        }

    def _parse_document_count(self, items_json):
        """Parse JSON items and count documents."""
        try:
            items_list = json.loads(items_json)
            doc_count = 0

            for item in items_list:
                if isinstance(item, list) and len(item) > 2:
                    try:
                        doc_count += int(item[2])
                    except (ValueError, TypeError):
                        doc_count += 1  # Default count if parsing fails

            return doc_count

        except json.JSONDecodeError:
            return 0  # Return 0 for malformed JSON

    def _animate_dashboard_labels(self, stats):
        """Animate dashboard labels with the provided statistics."""
        label_mappings = [
            (self.ui.total_customers_label, stats['total_customers']),
            (self.ui.total_issued_invoices_label, stats['total_invoices']),
            (self.ui.today_issued_invoices_label, stats['today_invoices']),
            (self.ui.total_documents_label, stats['total_documents']),
            (self.ui.available_documents_label, stats['available_documents'])
        ]

        for label, value in label_mappings:
            self.animate_label(label, 0, value)

    def animate_label(self, label, start_value, end_value, duration=1500):
        """Animate label value from start to end with smooth transition."""
        if end_value <= 0:
            label.setText(to_persian_number(0))
            return

        animation = QVariantAnimation(self)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        animation.valueChanged.connect(
            lambda value: label.setText(to_persian_number(int(value)))
        )
        animation.start()

    def load_invoices_into_table(self):
        """Load and display invoices in the dashboard table."""
        try:
            invoice_data = self._fetch_invoice_data()
            if not invoice_data:
                return

            filtered_data = self._filter_and_sort_invoices(invoice_data)
            self._populate_table(filtered_data[:20])  # Show top 20

        except Exception as e:
            QMessageBox.critical(self, "خطای جدول", f"خطا در بارگذاری فاکتورها: {e}")

    def _fetch_invoice_data(self):
        """Fetch invoice data from database."""
        with sqlite3.connect(invoices_database) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT invoice_number, name, phone, delivery_date, 
                       translator, pdf_file_path, delivery_status
                FROM issued_invoices
            """)
            return cursor.fetchall()

    def _filter_and_sort_invoices(self, invoice_data):
        """Filter out invalid dates and sort by delivery date."""
        today = jdatetime.date.today().togregorian()
        valid_invoices = []

        for invoice in invoice_data:
            delivery_date_str = invoice[3].strip()  # Updated index after removing issue_date

            if delivery_date_str == "نامشخص":
                continue

            delivery_date = parse_jalali_date(delivery_date_str)
            if delivery_date:
                valid_invoices.append((invoice, delivery_date))

        # Sort by delivery date (overdue first)
        return sorted(valid_invoices, key=lambda x: x[1])

    def _populate_table(self, invoice_data):
        """Populate the invoices table with data and styling."""
        self._setup_table_structure(len(invoice_data))

        today = jdatetime.date.today().togregorian()
        cell_colors = {}

        for row_idx, (invoice, delivery_date) in enumerate(invoice_data):
            bg_color = self._get_row_color(delivery_date, today)

            # Add data cells (excluding issue_date, including delivery_status)
            data_columns = invoice[:5]  # invoice_number, name, phone, delivery_date, translator
            for col_idx, value in enumerate(data_columns):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QBrush(QColor("black")))
                self.ui.tableWidget.setItem(row_idx, col_idx, item)

                if bg_color:
                    cell_colors[(row_idx, col_idx)] = bg_color

            # Add view button
            self._add_view_button(row_idx, invoice[5], bg_color, cell_colors)  # pdf_file_path

            # Add ready for delivery button
            self._add_ready_delivery_button(row_idx, invoice[0], bg_color, cell_colors)  # invoice_number

            # Add delivery confirmation button
            self._add_delivery_confirmation_button(row_idx, invoice[0], invoice[6], bg_color,
                                                   cell_colors)  # invoice_number, delivery_status

        # Apply custom styling
        self.ui.tableWidget.setItemDelegate(
            ColorDelegate(cell_colors, self.ui.tableWidget)
        )

    def _setup_table_structure(self, row_count):
        """Configure table structure and headers."""
        self.ui.tableWidget.setRowCount(row_count)
        self.ui.tableWidget.setColumnCount(8)
        self.ui.tableWidget.setHorizontalHeaderLabels([
            "شماره فاکتور", "نام", "شماره تماس", "تاریخ تحویل",
            "مترجم", "مشاهده فاکتور", "آماده تحویل", "تحویل"
        ])

        header = self.ui.tableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

    def _get_row_color(self, delivery_date, today):
        """Determine row background color based on delivery date."""
        days_diff = (delivery_date - today).days

        if days_diff <= 0:
            return QColor(255, 102, 102)  # Red for overdue
        elif days_diff <= 2:
            return QColor(255, 255, 200)  # Yellow for soon
        else:
            return QColor(255, 255, 255)  # White for normal

    def _add_view_button(self, row_idx, pdf_path, bg_color, cell_colors):
        """Add view PDF button to table row."""
        btn = QPushButton("نشان بده")
        btn.clicked.connect(lambda _, path=pdf_path: open_pdf(path))
        self.ui.tableWidget.setCellWidget(row_idx, 5, btn)

        if bg_color:
            cell_colors[(row_idx, 5)] = bg_color

    def _add_ready_delivery_button(self, row_idx, invoice_number, bg_color, cell_colors):
        """Add ready for delivery notification button to table row."""
        btn = QPushButton("آماده تحویل")
        btn.clicked.connect(lambda _, inv_num=invoice_number: self._handle_ready_delivery(inv_num))
        self.ui.tableWidget.setCellWidget(row_idx, 6, btn)

        if bg_color:
            cell_colors[(row_idx, 6)] = bg_color

    def _add_delivery_confirmation_button(self, row_idx, invoice_number, delivery_status, bg_color, cell_colors):
        """Add delivery confirmation button to table row."""
        if delivery_status == 1:
            btn = QPushButton("تحویل شده")
            btn.setEnabled(False)
            btn.setStyleSheet("background-color: #90EE90;")  # Light green for delivered
        else:
            btn = QPushButton("تحویل")
            btn.clicked.connect(lambda _, inv_num=invoice_number: self._handle_delivery_confirmation(inv_num))

        self.ui.tableWidget.setCellWidget(row_idx, 7, btn)

        if bg_color:
            cell_colors[(row_idx, 7)] = bg_color

    def _handle_ready_delivery(self, invoice_number):
        """Handle ready for delivery button click - show notification dialog."""
        title = "اطلاع‌رسانی آماده تحویل"
        message = "آیا می‌خواهید به مشتری اطلاع دهید که فاکتور آماده تحویل است؟"
        button1 = "بله، می‌خواهم اطلاع دهم"
        button2 = "خیر"
        show_question_message_box(self, title, message, button1,
                                  lambda: self._show_notification_dialog(invoice_number), button2)

    def _handle_delivery_confirmation(self, invoice_number):
        """Handle delivery confirmation button click - confirm customer has collected invoice."""
        title = "تأیید تحویل"
        message = "آیا مشتری فاکتور خود را دریافت کرده است؟"

        reply = QMessageBox.question(self, title, message,
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._mark_invoice_as_delivered(invoice_number)

    def _mark_invoice_as_delivered(self, invoice_number):
        """Mark invoice as delivered in database and refresh table."""
        try:
            with sqlite3.connect(invoices_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE issued_invoices 
                    SET delivery_status = 1 
                    WHERE invoice_number = ?
                """, (invoice_number,))

                if cursor.rowcount > 0:
                    conn.commit()
                    QMessageBox.information(self, "موفقیت", "فاکتور به عنوان تحویل شده علامت‌گذاری شد.")
                    # Refresh the table to show updated status
                    self.load_invoices_into_table()
                    # Update dashboard to reflect new available document count
                    self.update_dashboard()
                else:
                    QMessageBox.warning(self, "خطا", "فاکتور مورد نظر یافت نشد.")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطای پایگاه داده", f"خطا در به‌روزرسانی وضعیت تحویل: {e}")

    def _show_notification_dialog(self, invoice_number):
        """Show SMS/Email notification dialog."""
        dialog = NotificationDialog(invoice_number, invoices_database, customers_database, self)
        dialog.exec_()
