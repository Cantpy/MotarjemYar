# main_window.py

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QStackedWidget, QLabel,
                               QFrame, QSizePolicy)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, Slot
from typing import Dict, Any

# --- Import all the necessary components for each step ---

# Step 1: Customer Info
from features.InvoicePage.customer_info.customer_info_view import CustomerInfoView
from features.InvoicePage.customer_info.customer_info_repo import CustomerRepository

# Step 2: Document Selection
from features.InvoicePage.document_selection.document_selection_view import DocumentSelectionView
from features.InvoicePage.document_selection.document_selection_controller import DocumentSelectionController
from features.InvoicePage.document_selection.document_selection_logic import (DocumentLogic, PriceCalculationLogic,
                                                                              InvoiceLogic)
from features.InvoicePage.document_selection.document_selection_repo import DatabaseRepository as DocumentRepository

# Step 3: Invoice Details
from features.InvoicePage.invoice_details.invoice_details_view import InvoiceDetailsView
from features.InvoicePage.invoice_details.invoice_details_controller import InvoiceDetailsController
from features.InvoicePage.invoice_details.invoice_details_models import CustomerInfo

# Step 4: Invoice Preview
from features.InvoicePage.invoice_preview.invoice_preview_view import MainInvoiceWindow as InvoicePreviewWindow
from features.InvoicePage.invoice_preview.invoice_preview_controller import InvoiceController

# A central data class to hold the invoice state as it's being built
from dataclasses import dataclass, field
from shared import to_persian_number, show_error_message_box, show_warning_message_box, show_information_message_box


@dataclass
class InvoiceBuilder:
    customer_data: Dict[str, Any] = field(default_factory=dict)
    document_items: list = field(default_factory=list)
    invoice_details: Dict[str, Any] = field(default_factory=dict)


class StepProgressBar(QWidget):
    """A visual indicator for the wizard steps."""

    def __init__(self, steps: list):
        super().__init__()
        self.steps = steps
        self.current_step = 0
        self.labels = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for i, step_name in enumerate(steps):
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)

            label = QLabel(step_name)
            label.setAlignment(Qt.AlignCenter)
            self.labels.append(label)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFixedHeight(4)

            frame_layout.addWidget(label)
            frame_layout.addWidget(line)
            layout.addWidget(frame)

        self.set_step(0)

    def set_step(self, index: int):
        self.current_step = index
        for i, label in enumerate(self.labels):
            is_current = (i == index)
            is_completed = (i < index)

            font = QFont()
            font.setBold(is_current)
            label.setFont(font)

            line = label.parent().findChild(QFrame)
            if is_current:
                line.setStyleSheet("background-color: #007bff;")
            elif is_completed:
                line.setStyleSheet("background-color: #28a745;")
            else:
                line.setStyleSheet("background-color: #e0e0e0;")


class InvoiceWizardMainWindow(QMainWindow):
    """The main application window that orchestrates the 4-step wizard."""

    def __init__(self, customer_repo, doc_repo, details_controller):
        super().__init__()
        self.setWindowTitle("صدور فاکتور")
        self.setGeometry(100, 100, 1400, 900)

        # --- Central Data Store for the Wizard ---
        self.invoice_builder = InvoiceBuilder()

        # --- Repositories and Controllers ---
        self.customer_repo = customer_repo
        self.doc_repo = doc_repo
        self.details_controller = details_controller

        # --- Main UI Setup ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Progress Bar
        self.progress_bar = StepProgressBar(["مشتری", "اسناد", "جزئیات", "پیش‌نمایش"])
        main_layout.addWidget(self.progress_bar)
        main_layout.addSpacing(15)

        # 2. Stacked Widget for Pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 3. Navigation Buttons
        self.navigation_widget = self._create_navigation_buttons()
        main_layout.addWidget(self.navigation_widget)

        # --- Initialize and Add Wizard Steps ---
        self._create_and_add_steps()
        self._connect_signals()

        # Start at the first step
        self.stacked_widget.setCurrentIndex(0)
        self.update_navigation_buttons()

    def _create_navigation_buttons(self) -> QWidget:
        """Creates the Previous/Next buttons for the wizard."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        self.back_button = QPushButton("<< مرحله قبل")
        self.next_button = QPushButton("مرحله بعد >>")
        self.finish_button = QPushButton("✔ اتمام و صدور فاکتور")

        for btn in [self.back_button, self.next_button, self.finish_button]:
            btn.setMinimumHeight(40)
            font = QFont()
            font.setPointSize(11)
            font.setBold(True)
            btn.setFont(font)

        layout.addStretch()
        layout.addWidget(self.back_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.finish_button)

        return widget

    def _create_and_add_steps(self):
        """Initializes all four step widgets and adds them to the stack."""
        # --- Step 1: Customer Info ---
        self.customer_info_page = CustomerInfoView(self.customer_repo)
        self.stacked_widget.addWidget(self.customer_info_page)

        # --- Step 2: Document Selection ---
        doc_logic = DocumentLogic(self.doc_repo)
        price_logic = PriceCalculationLogic(doc_logic)
        self.doc_controller = DocumentSelectionController(doc_logic, price_logic)
        self.doc_selection_page = self.doc_controller.create_view()
        self.stacked_widget.addWidget(self.doc_selection_page)

        # --- Step 3: Invoice Details ---
        self.invoice_details_page = InvoiceDetailsView()
        self.details_controller.set_view(self.invoice_details_page)
        self.stacked_widget.addWidget(self.invoice_details_page)

        # --- Step 4: Invoice Preview ---
        self.invoice_preview_page = InvoicePreviewWindow()
        self.preview_controller = InvoiceController(self.invoice_preview_page)
        self.stacked_widget.addWidget(self.invoice_preview_page)

    def _connect_signals(self):
        """Connects signals for navigation and data transfer."""
        self.back_button.clicked.connect(self.go_to_previous_step)
        self.next_button.clicked.connect(self.go_to_next_step)
        self.finish_button.clicked.connect(self.finish_wizard)
        self.stacked_widget.currentChanged.connect(self.update_navigation_buttons)

    def update_navigation_buttons(self):
        """Shows/hides the correct navigation buttons for the current step."""
        current_index = self.stacked_widget.currentIndex()
        self.progress_bar.set_step(current_index)

        self.back_button.setVisible(current_index > 0)
        self.next_button.setVisible(current_index < self.stacked_widget.count() - 1)
        self.finish_button.setVisible(current_index == self.stacked_widget.count() - 1)

    # --- Wizard Logic and Data Transfer ---
    @Slot()
    def go_to_next_step(self):
        current_index = self.stacked_widget.currentIndex()

        # --- Data Handoff Logic ---
        if current_index == 0:  # From Customer to Documents
            customer_data = self.customer_info_page.controller.export_data()
            if not self.customer_info_page.controller.is_valid():
                show_warning_message_box(self, "خطا", "لطفاً اطلاعات مشتری را به درستی تکمیل نمایید.")
                return
            self.invoice_builder.customer_data = customer_data
            print("Step 1 -> 2: Customer data captured.")

        elif current_index == 1:  # From Documents to Details
            doc_data = self.doc_controller.export_invoice_data()
            if not doc_data['items']:
                show_warning_message_box(self, "خطا", "حداقل یک سند باید به فاکتور اضافه شود.")
                return
            self.invoice_builder.document_items = doc_data['items']
            print("Step 2 -> 3: Document data captured.")

            # 1. Extract the nested customer dictionary from the builder
            customer_dict = self.invoice_builder.customer_data.get('customer', {})

            # 2. Create the simple `CustomerInfo` object that the details controller expects
            customer_info_for_details = CustomerInfo(
                name=customer_dict.get('name', ''),
                phone=customer_dict.get('phone', ''),
                national_id=customer_dict.get('national_id', ''),
                email=customer_dict.get('email', ''),
                address=customer_dict.get('address', ''),
                total_companions=len(self.invoice_builder.customer_data.get('companions', []))
            )

            # 3. Initialize the details page with the correctly typed and structured data
            self.details_controller.initialize_invoice(
                document_count=len(doc_data['items']),
                customer_info=customer_info_for_details  # Pass the object, not the dictionary
            )
            self.details_controller.update_costs(
                translation_cost=doc_data['total_amount']
            )
        elif current_index == 2:  # From Details to Preview
            # Get data from details page
            if not self.invoice_details_page.is_valid():
                errors = "\n".join(self.invoice_details_page.get_validation_errors())
                show_warning_message_box(self, "خطا در اعتبارسنجی", f"لطفاً موارد زیر را اصلاح کنید:\n{errors}")
                return
            self.invoice_builder.invoice_details = self.invoice_details_page.get_data()
            print("Step 3 -> 4: Invoice details captured.")

            # Load the final, combined data into the preview controller
            self.preview_controller.load_new_invoice(self.invoice_builder)

        self.stacked_widget.setCurrentIndex(current_index + 1)

    @Slot()
    def go_to_previous_step(self):
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)

    @Slot()
    def finish_wizard(self):
        """Called when the final 'Finish' button is clicked."""
        # You could trigger the save_as_pdf method here, for example
        self.preview_controller.save_as_pdf()
        # Optionally, you could close the wizard or reset it
        # self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)


    # --- This is a placeholder for your actual database setup ---
    # In a real app, you would get your SQLAlchemy session here
    class MockRepo:  # Placeholder
        def get_all_customers(self, limit=100): return []

        def get_all_companions(self, limit=1000): return []


    customer_repository = MockRepo()
    document_repository = DocumentRepository()


    # The details controller needs a DB session for users/office info
    # For this demo, we'll pass None and it might raise errors if those DBs aren't found.
    # In your real app, provide the correct sessions.
    # details_controller = InvoiceDetailsController(db_session=None, current_user="Demo User")

    # To make it runnable, let's create a minimal mock controller
    class MockDetailsController:
        def set_view(self, view): self.view = view

        def initialize_invoice(self, **kwargs): print("Initializing details...")

        def update_costs(self, **kwargs): print("Updating costs...")


    details_controller = MockDetailsController()

    main_window = InvoiceWizardMainWindow(customer_repository, document_repository, details_controller)
    main_window.show()
    sys.exit(app.exec())
