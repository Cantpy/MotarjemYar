from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QLabel,
    QPushButton, QSpacerItem, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

from invoice_page_controller import InvoicePageController
from invoice_page_models import WizardSteps
from invoice_details_view import InvoiceDetailsView
from invoice_preview_view import InvoicePreviewView
from share_invoice_view import ShareInvoiceView


class InvoiceWizardView(QWidget):
    """Main invoice wizard widget with progress indicator and navigation."""

    # Signals
    wizard_finished = Signal(dict)  # complete_invoice_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InvoiceWizard")

        # Initialize controller
        self.controller = InvoicePageController(self)

        # Setup UI
        self._setup_ui()
        self._connect_signals()

        # Register step views with controller
        self._register_step_views()

    def _setup_ui(self):
        """Setup the main wizard UI structure."""
        self.resize(1000, 800)
        self.setFont(self._get_font())
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # Progress indicator
        self._create_progress_indicator()
        main_layout.addWidget(self.progress_frame)

        # Stacked widget for wizard steps
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("wizard_stack")

        # Create step views (excluding customer and documents which you already have)
        self._create_step_views()

        main_layout.addWidget(self.stacked_widget)

        # Navigation buttons
        self._create_navigation_buttons()
        main_layout.addWidget(self.navigation_frame)

    def _create_progress_indicator(self):
        """Create progress indicator showing all five steps."""
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("progress_frame")
        self.progress_frame.setMaximumHeight(100)
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 12px;
                margin: 2px;
            }
        """)

        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(30, 20, 30, 20)
        progress_layout.setSpacing(15)

        # Step indicators
        self.step_labels = []

        for i, step_name in enumerate(WizardSteps.STEP_NAMES):
            # Step circle and label
            step_container = QVBoxLayout()

            # Circle indicator
            step_circle = QLabel(str(i + 1))
            step_circle.setObjectName(f"step_circle_{i}")
            step_circle.setFixedSize(40, 40)
            step_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_circle.setStyleSheet(self._get_step_circle_style(i == 0))

            # Step label
            step_label = QLabel(step_name)
            step_label.setObjectName(f"step_label_{i}")
            step_label.setFont(self._get_font(9, bold=True))
            step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_label.setWordWrap(True)

            step_container.addWidget(step_circle)
            step_container.addWidget(step_label)

            progress_layout.addLayout(step_container)
            self.step_labels.append((step_circle, step_label))

            # Add arrow between steps (except after last step)
            if i < len(WizardSteps.STEP_NAMES) - 1:
                arrow = QLabel("←")
                arrow.setFont(self._get_font(16, bold=True))
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet("color: #6c757d;")
                progress_layout.addWidget(arrow)

        progress_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    def _get_step_circle_style(self, is_active=False, is_completed=False):
        """Get CSS style for step circle indicators."""
        if is_completed:
            return """
                QLabel {
                    background-color: #28a745;
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """
        elif is_active:
            return """
                QLabel {
                    background-color: #007bff;
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """
        else:
            return """
                QLabel {
                    background-color: #e9ecef;
                    color: #6c757d;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """

    def _create_step_views(self):
        """Create step view widgets."""
        # Note: Customer and Documents views are excluded as requested
        # They should be added externally using add_step_view method

        # Add placeholder widgets for customer and documents steps
        placeholder1 = QWidget()
        placeholder1_layout = QVBoxLayout(placeholder1)
        placeholder1_label = QLabel("Customer View (External)")
        placeholder1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder1_label.setStyleSheet("color: #6c757d; font-size: 16px;")
        placeholder1_layout.addWidget(placeholder1_label)
        self.stacked_widget.addWidget(placeholder1)

        placeholder2 = QWidget()
        placeholder2_layout = QVBoxLayout(placeholder2)
        placeholder2_label = QLabel("Documents View (External)")
        placeholder2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder2_label.setStyleSheet("color: #6c757d; font-size: 16px;")
        placeholder2_layout.addWidget(placeholder2_label)
        self.stacked_widget.addWidget(placeholder2)

        # Step 3: Invoice Details
        self.invoice_details_view = InvoiceDetailsView()
        self.stacked_widget.addWidget(self.invoice_details_view)

        # Step 4: Preview
        self.preview_view = InvoicePreviewView()
        self.stacked_widget.addWidget(self.preview_view)

        # Step 5: Sharing
        self.sharing_view = ShareInvoiceView()
        self.stacked_widget.addWidget(self.sharing_view)

    def _create_navigation_buttons(self):
        """Create navigation buttons for wizard."""
        self.navigation_frame = QFrame()
        self.navigation_frame.setObjectName("navigation_frame")
        self.navigation_frame.setMaximumHeight(80)
        self.navigation_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        nav_layout = QHBoxLayout(self.navigation_frame)
        nav_layout.setContentsMargins(30, 15, 30, 15)

        # Back button
        self.back_button = QPushButton("← قبلی")
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(120, 40))
        self.back_button.setFont(self._get_font(11, bold=True))
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:enabled {
                background-color: #007bff;
            }
            QPushButton:enabled:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)

        nav_layout.addWidget(self.back_button)

        # Step indicator
        self.step_indicator = QLabel("مرحله 1 از 5")
        self.step_indicator.setFont(self._get_font(12, bold=True))
        self.step_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_indicator.setStyleSheet("color: #495057;")

        nav_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        nav_layout.addWidget(self.step_indicator)
        nav_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Next/Finish button
        self.next_button = QPushButton("بعدی →")
        self.next_button.setObjectName("next_button")
        self.next_button.setMinimumSize(QSize(120, 40))
        self.next_button.setFont(self._get_font(11, bold=True))
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)

        nav_layout.addWidget(self.next_button)

    def _connect_signals(self):
        """Connect all signals and slots."""
        # Navigation buttons
        self.back_button.clicked.connect(self._go_back)
        self.next_button.clicked.connect(self._go_next)

        # Controller signals
        self.controller.step_changed.connect(self._on_step_changed)
        self.controller.wizard_finished.connect(self.wizard_finished)
        self.controller.validation_error.connect(self._show_validation_error)

    def _register_step_views(self):
        """Register step views with the controller."""
        # Register only the views we created (invoice details, preview, sharing)
        self.controller.register_step_view(WizardSteps.INVOICE_DETAILS, self.invoice_details_view)
        self.controller.register_step_view(WizardSteps.PREVIEW, self.preview_view)
        self.controller.register_step_view(WizardSteps.SHARING, self.sharing_view)

    def add_step_view(self, step_index: int, view_widget: QWidget):
        """Add a step view widget (for external customer and documents views)."""
        if 0 <= step_index < WizardSteps.TOTAL_STEPS:
            # Replace the placeholder widget
            self.stacked_widget.removeWidget(self.stacked_widget.widget(step_index))
            self.stacked_widget.insertWidget(step_index, view_widget)

            # Register with controller
            self.controller.register_step_view(step_index, view_widget)

    def _go_next(self):
        """Navigate to next step."""
        if not self.controller.go_next():
            # Validation failed, controller will emit validation_error signal
            pass

    def _go_back(self):
        """Navigate to previous step."""
        self.controller.go_back()

    def _on_step_changed(self, step_index: int):
        """Handle step change."""
        self.stacked_widget.setCurrentIndex(step_index)
        self._update_progress_indicator(step_index)
        self._update_navigation_buttons(step_index)
        self._update_step_indicator(step_index)

    def _update_progress_indicator(self, current_step: int):
        """Update progress indicator based on current step."""
        completion_status = self.controller.get_step_completion_status()

        for i, (circle, label) in enumerate(self.step_labels):
            if completion_status.get(i, False) and i < current_step:
                # Completed step
                circle.setStyleSheet(self._get_step_circle_style(False, True))
                label.setStyleSheet("color: #28a745; font-weight: bold;")
            elif i == current_step:
                # Current step
                circle.setStyleSheet(self._get_step_circle_style(True, False))
                label.setStyleSheet("color: #007bff; font-weight: bold;")
            else:
                # Future step
                circle.setStyleSheet(self._get_step_circle_style(False, False))
                label.setStyleSheet("color: #6c757d;")

    def _update_navigation_buttons(self, step_index: int):
        """Update navigation buttons based on current step."""
        # Back button
        self.back_button.setEnabled(self.controller.can_go_back())

        # Next/Finish button
        if self.controller.is_last_step():
            self.next_button.setText("🎉 تکمیل ویزارد")
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
        else:
            self.next_button.setText("بعدی →")
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)

    def _update_step_indicator(self, step_index: int):
        """Update step indicator text."""
        self.step_indicator.setText(f"مرحله {step_index + 1} از {WizardSteps.TOTAL_STEPS}")

    def _show_validation_error(self, message: str):
        """Show validation error message."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("خطای اعتبارسنجی")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def reset_wizard(self):
        """Reset the entire wizard to initial state."""
        self.controller.reset_wizard()

    def get_wizard_data(self):
        """Get complete wizard data."""
        return self.controller.get_wizard_data()

    def set_wizard_data(self, data):
        """Set wizard data (for loading existing invoice)."""
        self.controller.set_wizard_data(data)

    def get_controller(self):
        """Get the wizard controller."""
        return self.controller

    @staticmethod
    def _get_font(size=10, bold=False):
        """Get standard font for the application."""
        font = QFont("IRANSans")
        font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font
