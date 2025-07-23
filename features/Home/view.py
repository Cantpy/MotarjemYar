""" View layer for home page. Handles UI display and user interactions using PySide6. """
import sys
from typing import List, Dict, Tuple
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, Signal, QTimer, QSize, QPoint
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPixmap, QAction
from PySide6.QtWidgets import (
    QWidget, QMessageBox, QTableWidgetItem, QPushButton, QHeaderView, QMenu,
    QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QFrame, QGridLayout, QAbstractItemView
)

from features.Home.controller import HomePageController, HomePageControllerFactory
from features.Home.models import DashboardStats, InvoiceTableRow
from shared import (return_resource, to_persian_number, to_english_number,
                    show_error_message_box, show_information_message_box, show_toast)
from datetime import date


customers_database = return_resource('databases', 'customers.db')
invoices_database = return_resource('databases', 'invoices.db')
services_database = return_resource('databases', 'services.db')


class HomePageView(QWidget):
    """
    Main view class for the home page dashboard.
    Displays statistics, recent invoices, and provides navigation controls.
    """

    # Signals
    invoice_selected = Signal(int)  # Emitted when an invoice is selected
    refresh_requested = Signal()  # Emitted when refresh is requested

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = HomePageControllerFactory.create_controller(customers_db_path=customers_database,
                                                                      documents_db_path=invoices_database,
                                                                      invoices_db_path=services_database)
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()

    def setup_ui(self):
        """Initialize the user interface components."""
        self.setObjectName("HomePageView")
        self.setStyleSheet(self.get_stylesheet())

        self.setGeometry(100, 100, 1200, 800)
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # Dashboard stats
        stats_widget = self.create_dashboard_stats()
        main_layout.addWidget(stats_widget)

        # Recent invoices section
        invoices_widget = self.create_recent_invoices_section()
        main_layout.addWidget(invoices_widget)

        # Stretch to fill remaining space
        main_layout.addStretch()

    def create_header(self) -> QHBoxLayout:
        """Create the header section with title and refresh button."""
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("داشبورد")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Refresh button
        self.refresh_btn = QPushButton("بروزرسانی")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.setMaximumWidth(120)

        header_layout.addWidget(self.refresh_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)

        return header_layout

    def create_dashboard_stats(self) -> QWidget:
        """Create the dashboard statistics section."""
        stats_widget = QWidget()
        stats_widget.setObjectName("statsWidget")

        stats_layout = QGridLayout(stats_widget)
        stats_layout.setSpacing(15)

        # Create stat cards
        self.total_customers_card = self.create_stat_card("تعداد مشتریان", "0", "#2980b9")
        self.total_invoices_card = self.create_stat_card("کل فاکتورها", "0", "#3498db")
        self.today_invoices_card = self.create_stat_card("فاکتورهای امروز", "0", "#1abc9c")
        self.total_documents_card = self.create_stat_card("کل مدارک", "0", "#8e44ad")
        self.available_documents_card = self.create_stat_card("مدارک موجود در دفتر", "0", "#e67e22")
        self.most_repeated_document_card = self.create_stat_card("پرتکرارترین مدرک", "0", "#27ae60")

        # Add cards to grid (3 per row)
        stats_layout.addWidget(self.total_customers_card, 0, 0)
        stats_layout.addWidget(self.total_invoices_card, 0, 1)
        stats_layout.addWidget(self.today_invoices_card, 0, 2)
        stats_layout.addWidget(self.total_documents_card, 1, 0)
        stats_layout.addWidget(self.available_documents_card, 1, 1)
        stats_layout.addWidget(self.most_repeated_document_card, 1, 2)

        return stats_widget

    @staticmethod
    def create_stat_card(title: str, value: str, color: str) -> QFrame:
        """Create a single statistics card."""
        card = QFrame()
        card.setObjectName("statCard")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                border-right: 4px solid {color};
            }}
            QFrame#statCard:hover {{
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 5px;")

        # Value
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card

    def create_recent_invoices_section(self) -> QWidget:
        """Create the recent invoices table section."""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setSpacing(15)

        # Section header
        header_layout = QHBoxLayout()

        section_title = QLabel("فاکتورهای اخیر")
        section_title.setObjectName("sectionTitle")
        section_title.setAlignment(Qt.AlignmentFlag.AlignRight)

        view_all_btn = QPushButton("مشاهده همه")
        view_all_btn.setObjectName("viewAllButton")
        view_all_btn.setMaximumWidth(100)

        header_layout.addWidget(view_all_btn)
        header_layout.addStretch()
        header_layout.addWidget(section_title)

        section_layout.addLayout(header_layout)

        # Invoices table
        self.invoices_table = QTableWidget()
        self.invoices_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_invoices_table()
        section_layout.addWidget(self.invoices_table)

        return section_widget

    def setup_invoices_table(self):
        """Set up the recent invoices table."""
        self.invoices_table.setObjectName("invoicesTable")
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.invoices_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.invoices_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.invoices_table.customContextMenuRequested.connect(self.contextMenuEvent)
        self.invoices_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Column headers (Persian)
        headers = ["شماره فاکتور", "مشتری", "تاریخ تحویل", "مترجم", "مانده (تومان)", "وضعیت", "عملیات‌ها"]
        self.invoices_table.setColumnCount(len(headers))
        self.invoices_table.setHorizontalHeaderLabels(headers)

        # Configure table appearance
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set table properties
        self.invoices_table.setMaximumHeight(400)
        self.invoices_table.setSortingEnabled(True)

    def setup_connections(self):
        """Setup signal-slot connections."""
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        self.invoices_table.cellDoubleClicked.connect(self.on_invoice_double_clicked)

    def load_initial_data(self):
        """Load initial data from the controller."""
        try:
            self.refresh_dashboard_stats()
            self.refresh_recent_invoices()
        except Exception as e:
            self.show_error_message(f"خطا در بارگذاری داده‌ها: {str(e)}")

    def refresh_dashboard_stats(self):
        """Refresh dashboard statistics."""
        try:
            stats = self.controller.update_dashboard()
            self.update_stats_display(stats)
        except Exception as e:
            self.show_error_message(f"خطا در بارگذاری آمار: {str(e)}")

    def update_stats_display(self, stats: DashboardStats):
        """Update the statistics display with new data."""
        self.total_customers_card.findChild(QLabel, "statValue").setText(
            to_persian_number(str(stats.total_customers))
        )
        self.total_invoices_card.findChild(QLabel, "statValue").setText(
            to_persian_number(str(stats.total_invoices))
        )
        self.today_invoices_card.findChild(QLabel, "statValue").setText(
            to_persian_number(str(stats.today_invoices))
        )
        self.total_documents_card.findChild(QLabel, "statValue").setText(
            to_persian_number(str(stats.total_documents))
        )
        self.available_documents_card.findChild(QLabel, "statValue").setText(
            to_persian_number(str(stats.available_documents))
        )
        self.most_repeated_document_card.findChild(QLabel, "statValue").setText(
            f"{(str(stats.most_repeated_document)) if stats.most_repeated_document else "نامشخص"}"
        )

        self.animate_stats_update()

    def animate_stats_update(self):
        """Animate the statistics update."""
        self.stats_animation = QVariantAnimation()
        self.stats_animation.setDuration(500)
        self.stats_animation.setStartValue(0.0)
        self.stats_animation.setEndValue(1.0)
        self.stats_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.stats_animation.start()

    def refresh_recent_invoices(self):
        """Refresh the recent invoices table."""
        try:
            invoices = self.controller.get_recent_invoices()
            self.populate_invoices_table(invoices)
        except Exception as e:
            self.show_error_message(f"خطا در بارگذاری فاکتورها: {str(e)}")

    @staticmethod
    def create_operations_menu(file_path: str, invoice_number: int, controller, parent=None) -> QMenu:
        """
        Create and return a QMenu with actions related to an invoice.

        Args:
            file_path (str): Path to the invoice PDF.
            invoice_number (int): Invoice identifier.
            controller: Controller instance to handle actions.
            parent: Optional QWidget parent.

        Returns:
            QMenu: The menu with bound actions.
        """
        menu = QMenu(parent)

        view_invoice = QAction("مشاهده فاکتور", menu)
        view_invoice.triggered.connect(lambda: controller.handle_view_pdf_request(file_path))

        mark_delivered = QAction("آماده تحویل", menu)
        mark_delivered.triggered.connect(lambda: controller.handle_ready_delivery_request(invoice_number, parent))

        mark_collected = QAction("تحویل به مشتری", menu)
        mark_collected.triggered.connect(
            lambda: controller.handle_delivery_confirmation_request(invoice_number, parent))

        menu.addActions([view_invoice, mark_delivered, mark_collected])
        return menu

    def create_operations_button(self, file_path: str, invoice_number: int, controller) -> QPushButton:
        """
        Create a button with a vertical ellipsis icon to show the operations menu.

        Args:
            file_path (str): Path to the invoice PDF.
            invoice_number (int): Invoice identifier.
            controller: Controller instance to handle actions.
            parent: Optional QWidget parent.

        Returns:
            QPushButton: The button that shows the menu on click.
        """
        button = QPushButton("⋮", self)
        button.setCursor(Qt.PointingHandCursor)
        button.setFlat(True)
        button.setFont(QFont("Tahoma", 15))

        menu = self.create_operations_menu(file_path, invoice_number, controller, self)

        def show_menu():
            menu.popup(button.mapToGlobal(button.rect().bottomLeft()))

        button.clicked.connect(show_menu)
        return button

    def contextMenuEvent(self, pos: QPoint):
        index = self.invoices_table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        item = self.invoices_table.item(row, 0)
        if item is None:
            return

        try:
            invoice_number = int(to_english_number(item.text()))
        except ValueError:
            return

        invoice = self.controller.invoice_data_for_context_menu(invoice_number)
        if invoice is None:
            return

        file_path = invoice.pdf_file_path

        # Optional: visually select the row
        self.invoices_table.selectRow(row)

        # Create and show the menu
        menu = self.create_operations_menu(file_path, invoice_number, self.controller, self)
        menu.exec(self.invoices_table.viewport().mapToGlobal(pos))

    def populate_invoices_table(self, invoices_with_priority: List[Tuple]):
        """
        Populate the invoices table with data and apply color coding.

        Args:
            invoices_with_priority: List of tuples containing (invoice, priority_label)
        """
        self.invoices_table.setRowCount(len(invoices_with_priority))

        for row, (invoice, priority) in enumerate(invoices_with_priority):
            # Invoice number - 1st row
            invoice_num_item = QTableWidgetItem(to_persian_number(str(invoice.invoice_number)))
            invoice_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 0, invoice_num_item)

            # Customer name
            customer_item = QTableWidgetItem(invoice.name)
            customer_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 1, customer_item)

            # Due date
            date_item = QTableWidgetItem(invoice.delivery_date.strftime("%Y/%m/%d"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 2, date_item)

            # Translator
            translator_item = QTableWidgetItem(invoice.translator)
            translator_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 3, translator_item)

            # Amount
            amount_item = QTableWidgetItem(f"{to_persian_number(str(invoice.final_amount))} تومان")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 4, amount_item)

            # Status
            status_text = self._get_status_text(invoice.delivery_status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 5, status_item)

            # Actions button
            action_btn = self.create_operations_button(invoice.pdf_file_path, invoice.invoice_number, self.controller)
            self.invoices_table.setCellWidget(row, 6, action_btn)

        # Apply row color based on priority
        self._apply_color_on_rows(invoices_with_priority)

    def _apply_color_on_rows(self, invoice_rows_with_priority: List[Tuple]):
        for row_index, (invoice, priority) in enumerate(invoice_rows_with_priority):
            if priority == 'urgent':
                color = QColor(255, 200, 200)  # Light red
            elif priority == 'needs_attention':
                color = QColor(255, 220, 150)  # Orange-yellow
            else:
                continue

            for col_idx in range(self.invoices_table.columnCount() - 1):  # Skip column with button
                item = self.invoices_table.item(row_index, col_idx)
                if item is not None:
                    # Use QBrush for more reliable color application
                    brush = QBrush(color)
                    item.setBackground(brush)
                    # Also set a role-based approach as backup
                    item.setData(Qt.ItemDataRole.BackgroundRole, brush)

    @staticmethod
    def _get_status_text(delivery_status: int) -> str:
        """
        Convert delivery status code to Persian text.

        Args:
            delivery_status: Status code

        Returns:
            Persian status text
        """
        status_map = {
            0: "تحویل گرفته شده",
            1: "در حال ترجمه",
            2: "ترجمه شده، نیاز به تاییدات",
            3: "آماده تحویل",
            4: "دریافت توسط مشتری"
        }
        return status_map.get(delivery_status, "نامشخص")

    def on_refresh_clicked(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()
        self.load_initial_data()

    def on_invoice_double_clicked(self, row: int):
        """Handle invoice table double click."""
        invoice_number = self.get_invoice_id_from_row(row)
        if invoice_number:
            # Copy to clipboard
            QApplication.clipboard().setText(str(invoice_number))

            # Emit signal
            self.invoice_selected.emit(invoice_number)

            # Show confirmation
            show_toast(self, "✅ شماره فاکتور کپی شد")

    def on_invoice_view_clicked(self, invoice_id: int):
        """Handle invoice view button click."""
        self.invoice_selected.emit(invoice_id)

    def get_invoice_id_from_row(self, row: int) -> int:
        """Get invoice ID from table row."""
        try:
            invoice_number = self.invoices_table.item(row, 0).text()
            # Convert from Persian number and return as int
            return int(to_english_number(invoice_number))
        except (AttributeError, ValueError):
            return 0

    @staticmethod
    def get_stylesheet() -> str:
        """Return the CSS stylesheet for the view."""
        return """
        QWidget#HomePageView {
            background-color: #f5f5f5;
        }

        QLabel#pageTitle {
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        QLabel#sectionTitle {
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
            margin-bottom: 10px;
        }

        QPushButton#refreshButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }

        QPushButton#refreshButton:hover {
            background-color: #2980b9;
        }

        QPushButton#refreshButton:pressed {
            background-color: #21618c;
        }

        QPushButton#viewAllButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-size: 12px;
        }

        QPushButton#viewAllButton:hover {
            background-color: #7f8c8d;
        }

        QPushButton#actionButton {
            background-color: #27ae60;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 4px 8px;
            font-size: 12px;
        }

        QPushButton#actionButton:hover {
            background-color: #229954;
        }

        QWidget#statsWidget {
            background-color: transparent;
        }

        QTableWidget#invoicesTable {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            selection-background-color: #e3f2fd;
            gridline-color: #f0f0f0;
        }
        
        QTableWidget#invoicesTable::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }

        QHeaderView::section {
            background-color: #f8f9fa;
            color: #495057;
            padding: 10px;
            border: 1px solid #dee2e6;
            font-weight: bold;
        }
        """


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    window = HomePageView()
    window.show()
    sys.exit(app.exec())


