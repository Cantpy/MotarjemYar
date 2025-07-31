# -*- coding: utf-8 -*-
"""
Main Invoice Page UI - Manages the two-step process
"""
import sys

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QSpacerItem, QSizePolicy, QFrame
)

from features.InvoicePage.ui.customer_info_ui import CustomerInfoUI
from features.InvoicePage.ui.documents_section_ui import DocumentsSectionUI


class InvoicePageUI(QWidget):
    """Main invoice page widget managing the two-step process."""

    # Signals for navigation
    customer_completed = Signal(dict)  # Emitted when customer info is complete
    invoice_ready = Signal(dict)  # Emitted when invoice is ready

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InvoicePage")
        self.customer_data = {}
        self.documents_data = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the main UI structure."""
        self.resize(932, 776)
        self.setFont(self._get_font())
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setStyleSheet("background-color: rgb(240, 240, 240);")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(50, 20, 50, 20)

        # Progress indicator
        self._create_progress_indicator()
        main_layout.addWidget(self.progress_frame)

        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("stacked_widget")

        # Create pages
        self.customer_page = CustomerInfoUI()
        self.documents_page = DocumentsSectionUI()

        # Add pages to stack
        self.stacked_widget.addWidget(self.customer_page)
        self.stacked_widget.addWidget(self.documents_page)

        main_layout.addWidget(self.stacked_widget)

        # Navigation buttons
        self._create_navigation_buttons()
        main_layout.addWidget(self.navigation_frame)

    def _create_progress_indicator(self):
        """Create progress indicator showing current step."""
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("progress_frame")
        self.progress_frame.setMaximumHeight(80)
        self.progress_frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 1px;
            }
        """)

        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(20, 15, 20, 15)

        # Step 1 indicator
        self.step1_label = QLabel("1. اطلاعات مشتری")
        self.step1_label.setObjectName("step1_label")
        self.step1_label.setFont(self._get_font(10, bold=True))
        self.step1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step1_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)

        # Arrow
        arrow_label = QLabel("←")
        arrow_label.setFont(self._get_font(16, bold=True))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Step 2 indicator
        self.step2_label = QLabel("2. اطلاعات اسناد")
        self.step2_label.setObjectName("step2_label")
        self.step2_label.setFont(self._get_font(10, bold=True))
        self.step2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step2_label.setStyleSheet("""
            QLabel {
                background-color: #ccc;
                color: #666;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)

        progress_layout.addWidget(self.step1_label)
        progress_layout.addWidget(arrow_label)
        progress_layout.addWidget(self.step2_label)
        progress_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    def _create_navigation_buttons(self):
        """Create navigation buttons."""
        self.navigation_frame = QFrame()
        self.navigation_frame.setObjectName("navigation_frame")
        self.navigation_frame.setMaximumHeight(60)

        nav_layout = QHBoxLayout(self.navigation_frame)
        nav_layout.setContentsMargins(20, 10, 20, 10)

        # Back button
        self.back_button = QPushButton("← بازگشت")
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(120, 35))
        self.back_button.setFont(self._get_font(10))
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:enabled {
                background-color: #2196F3;
                color: white;
                border: 1px solid #2196F3;
            }
            QPushButton:enabled:hover {
                background-color: #1976D2;
            }
        """)

        nav_layout.addWidget(self.back_button)
        nav_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Next button
        self.next_button = QPushButton("ادامه →")
        self.next_button.setObjectName("next_button")
        self.next_button.setMinimumSize(QSize(120, 35))
        self.next_button.setFont(self._get_font(10))
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #4CAF50;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 1px solid #cccccc;
            }
        """)

        nav_layout.addWidget(self.next_button)

    def _connect_signals(self):
        """Connect signals and slots."""
        # Navigation buttons
        self.back_button.clicked.connect(self._go_back)
        self.next_button.clicked.connect(self._go_next)

        # Customer page signals
        self.customer_page.data_changed.connect(self._on_customer_data_changed)
        self.customer_page.validation_changed.connect(self._on_customer_validation_changed)

        # Documents page signals
        self.documents_page.data_changed.connect(self._on_documents_data_changed)

    def _go_next(self):
        """Navigate to next step."""
        current_index = self.stacked_widget.currentIndex()

        if current_index == 0:  # Customer page
            if self.customer_page.is_valid():
                self.customer_data = self.customer_page.get_data()
                self.documents_page.set_customer_data(self.customer_data)
                self._switch_to_documents_page()
                self.customer_completed.emit(self.customer_data)
        elif current_index == 1:  # Documents page
            self.documents_data = self.documents_page.get_data()
            self._finalize_invoice()

    def _go_back(self):
        """Navigate to previous step."""
        current_index = self.stacked_widget.currentIndex()

        if current_index == 1:  # Documents page
            self._switch_to_customer_page()

    def _switch_to_customer_page(self):
        """Switch to customer information page."""
        self.stacked_widget.setCurrentIndex(0)
        self._update_progress_indicator(0)
        self._update_navigation_buttons(0)

    def _switch_to_documents_page(self):
        """Switch to documents page."""
        self.stacked_widget.setCurrentIndex(1)
        self._update_progress_indicator(1)
        self._update_navigation_buttons(1)

    def _update_progress_indicator(self, step):
        """Update progress indicator based on current step."""
        if step == 0:
            self.step1_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
            """)
            self.step2_label.setStyleSheet("""
                QLabel {
                    background-color: #ccc;
                    color: #666;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
            """)
        elif step == 1:
            self.step1_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    opacity: 0.7;
                }
            """)
            self.step2_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
            """)

    def _update_navigation_buttons(self, step):
        """Update navigation buttons based on current step."""
        if step == 0:
            self.back_button.setEnabled(False)
            self.next_button.setText("ادامه →")
            self.next_button.setEnabled(self.customer_page.is_valid())
        elif step == 1:
            self.back_button.setEnabled(True)
            self.next_button.setText("تکمیل فاکتور")
            self.next_button.setEnabled(True)

    def _on_customer_data_changed(self, data):
        """Handle customer data changes."""
        self.customer_data = data

    def _on_customer_validation_changed(self, is_valid):
        """Handle customer validation changes."""
        if self.stacked_widget.currentIndex() == 0:
            self.next_button.setEnabled(is_valid)

    def _on_documents_data_changed(self, data):
        """Handle documents data changes."""
        self.documents_data = data

    def _finalize_invoice(self):
        """Finalize the invoice and emit signal."""
        invoice_data = {
            'customer': self.customer_data,
            'documents': self.documents_data
        }
        self.invoice_ready.emit(invoice_data)

    def reset(self):
        """Reset the entire form."""
        self.customer_data = {}
        self.documents_data = []
        self.customer_page.reset()
        self.documents_page.reset()
        self._switch_to_customer_page()

    def get_customer_data(self):
        """Get current customer data."""
        return self.customer_data

    def get_documents_data(self):
        """Get current documents data."""
        return self.documents_data

    @staticmethod
    def _get_font(size=None, bold=False):
        """Get standard font for the application."""
        font = QFont("IRANSans")
        if size:
            font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    window = InvoicePageUI()
    window.show()
    sys.exit(app.exec())
