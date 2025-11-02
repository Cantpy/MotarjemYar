# shared/dialogs/status_change_dialog

from PySide6.QtWidgets import (QDialog, QFrame, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QComboBox)
from PySide6.QtCore import Qt, Signal

from features.Home_Page.home_page_models import StatusChangeRequest, InvoiceDTO

from shared.enums import DeliveryStatus
from shared.utils.number_utils import to_persian_number


class StepIndicator(QFrame):
    """Custom widget to display a single step in the delivery process."""

    def __init__(self, step_number: int, title: str, description: str,
                 status: str = "pending", is_current: bool = False, parent=None):
        super().__init__(parent)
        self.step_number = step_number
        self.title = title
        self.description = description
        self.status = status  # "completed", "current", "pending", "disabled"
        self.is_current = is_current

        self.setup_ui()
        self.apply_styling()

    def setup_ui(self):
        """Set up the step indicator UI."""
        self.setFixedHeight(80)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Step number circle
        self.step_circle = QLabel(str(self.step_number))
        self.step_circle.setFixedSize(40, 40)
        self.step_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_circle.setObjectName("stepCircle")

        # Step content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("stepTitle")

        self.desc_label = QLabel(self.description)
        self.desc_label.setObjectName("stepDescription")
        # self.desc_label.setWordWrap(True)

        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.desc_label)

        layout.addWidget(self.step_circle)
        layout.addLayout(content_layout)
        layout.addStretch()

    def apply_styling(self):
        """Apply styling based on step status."""
        base_style = """
        StepIndicator {
            border-radius: 12px;
            margin: 2px 0;
        }
        """

        if self.status == "completed":
            style = base_style + """
            StepIndicator {
                background-color: #e8f5e8;
                border: 2px solid #4CAF50;
            }
            QLabel#stepCircle {
                background-color: #4CAF50;
                color: white;
                border-radius: 20px;
                font-family: IranSANS;
                font-weight: bold;
                font-size: 14px;
            }
            QLabel#stepTitle {
                color: #2e7d32;
                font-weight: bold;
                font-family: IranSANS;
                font-size: 14px;
            }
            QLabel#stepDescription {
                color: #4caf50;
                font-family: IranSANS;
                font-size: 12px;
            }
            """
        elif self.status == "current":
            style = base_style + """
            StepIndicator {
                background-color: #e3f2fd;
                border: 2px solid #2196F3;
                box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
            }
            QLabel#stepCircle {
                background-color: #2196F3;
                color: white;
                border-radius: 20px;
                font-family: IranSANS;
                font-weight: bold;
                font-size: 14px;
            }
            QLabel#stepTitle {
                color: #1976d2;
                font-family: IranSANS;
                font-weight: bold;
                font-size: 15px;
            }
            QLabel#stepDescription {
                color: #1976d2;
                font-family: IranSANS;
                font-size: 12px;
                font-weight: 500;
            }
            """
        elif self.status == "pending":
            style = base_style + """
            StepIndicator {
                background-color: #f9f9f9;
                border: 2px solid #e0e0e0;
            }
            QLabel#stepCircle {
                background-color: #e0e0e0;
                color: #757575;
                border-radius: 20px;
                font-family: IranSANS;
                font-weight: bold;
                font-size: 14px;
            }
            QLabel#stepTitle {
                color: #616161;
                font-weight: normal;
                font-family: IranSANS;
                font-size: 14px;
            }
            QLabel#stepDescription {
                color: #9e9e9e;
                font-family: IranSANS;
                font-size: 12px;
            }
            """
        else:  # disabled
            style = base_style + """
            StepIndicator {
                background-color: #fafafa;
                border: 2px solid #f5f5f5;
                opacity: 0.6;
            }
            QLabel#stepCircle {
                background-color: #f5f5f5;
                color: #bdbdbd;
                border-radius: 20px;
                font-family: IranSANS;
                font-weight: normal;
                font-size: 14px;
            }
            QLabel#stepTitle {
                color: #bdbdbd;
                font-weight: normal;
                font-family: IranSANS;
                font-size: 14px;
            }
            QLabel#stepDescription {
                color: #e0e0e0;
                font-family: IranSANS;
                font-size: 12px;
            }
            """

        self.setStyleSheet(style)


class StatusChangeDialog(QDialog):
    """Modern dialog for changing invoice status with step-by-step visualization."""

    status_change_requested = Signal(StatusChangeRequest)

    def __init__(self, invoice: InvoiceDTO, next_status: int, step_text: str, translators: list = None, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        self.next_status = next_status
        self.step_text = step_text
        self.translators = translators if translators is not None else []

        # Define all delivery steps
        self.delivery_steps = [
            {"status": DeliveryStatus.ISSUED, "title": "صدور فاکتور", "desc": "فاکتور صادر شده، در انتظار تخصیص مترجم"},
            {"status": DeliveryStatus.ASSIGNED, "title": "در حال ترجمه",
             "desc": "انتخاب و تخصیص مترجم برای این فاکتور"},
            {"status": DeliveryStatus.TRANSLATED, "title": "در انتظار تاییدات",
             "desc": "ترجمه انجام شد، در انتظار تاییدات (دادگستری، امور خارجه، و یا مترجم مسئول)"},
            {"status": DeliveryStatus.READY, "title": "آماده برای تحویل",
             "desc": "تمامی مدارک ترجمه و تایید شده، در انتظار دریافت فاکتور توسط مشتری"},
            {"status": DeliveryStatus.COLLECTED, "title": "تحویل داده شد",
             "desc": "فاکتور بدون هیچ‌گونه مشکلی به مشتری تحویل داده شد."}
        ]

        self.setup_ui()
        self.apply_stylesheet()

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("مدیریت وضعیت فاکتور")
        self.setModal(True)
        self.setFixedSize(600, 700)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # Header section
        header_layout = self.create_header_section()
        main_layout.addLayout(header_layout)

        # Invoice info card
        invoice_card = self.create_invoice_card()
        main_layout.addWidget(invoice_card)

        # Steps container
        steps_container = self.create_steps_container()
        main_layout.addWidget(steps_container)

        # Input section (if needed)
        if self.next_status == DeliveryStatus.ASSIGNED:
            input_section = self.create_input_section()
            main_layout.addWidget(input_section)

        # Action buttons
        buttons_layout = self.create_action_buttons()
        main_layout.addLayout(buttons_layout)

    def create_header_section(self) -> QVBoxLayout:
        """Create the header section."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Main title
        title_label = QLabel("مدیریت وضعیت تحویل")
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle_label = QLabel("مراحل تحویل فاکتور را مشاهده و مدیریت کنید")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        return layout

    def create_invoice_card(self) -> QFrame:
        """Create invoice information card."""
        card = QFrame()
        card.setObjectName("invoiceCard")
        card.setFixedHeight(110)
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(30)

        # Invoice number
        invoice_layout = QVBoxLayout()
        invoice_num_label = QLabel("شماره فاکتور")
        invoice_num_label.setObjectName("cardLabel")
        invoice_val_label = QLabel(to_persian_number(str(self.invoice.invoice_number)))
        invoice_val_label.setObjectName("cardValue")
        invoice_layout.addWidget(invoice_num_label)
        invoice_layout.addWidget(invoice_val_label)

        # CustomerModel name
        customer_layout = QVBoxLayout()
        customer_label = QLabel("نام مشتری")
        customer_label.setObjectName("cardLabel")
        customer_val_label = QLabel(self.invoice.customer.name)
        customer_val_label.setObjectName("cardValue")
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(customer_val_label)

        # Current status
        status_layout = QVBoxLayout()
        status_label = QLabel("وضعیت فعلی")
        status_label.setObjectName("cardLabel")
        current_status_text = DeliveryStatus.get_status_text(self.invoice.delivery_status)
        status_val_label = QLabel(current_status_text)
        status_val_label.setObjectName("cardStatusValue")
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_val_label)

        layout.addLayout(invoice_layout)
        layout.addLayout(customer_layout)
        layout.addLayout(status_layout)
        layout.addStretch()

        return card

    def create_steps_container(self) -> QFrame:
        """Create the steps visualization container."""
        container = QFrame()
        container.setObjectName("stepsContainer")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)

        # Container title
        title_label = QLabel("مراحل تحویل")
        title_label.setObjectName("containerTitle")
        layout.addWidget(title_label)

        # Scroll area for steps
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("stepsScrollArea")

        steps_widget = QWidget()
        steps_layout = QVBoxLayout(steps_widget)
        steps_layout.setSpacing(8)
        steps_layout.setContentsMargins(5, 5, 5, 5)

        # Create step indicators
        current_status = self.invoice.delivery_status
        next_status = self.next_status

        for i, step_info in enumerate(self.delivery_steps):
            step_status_value = step_info["status"]

            # Determine step status
            if step_status_value < current_status:
                status = "completed"
            elif step_status_value == current_status:
                status = "current" if step_status_value != next_status else "current"
            elif step_status_value == next_status:
                status = "current"
            elif step_status_value == current_status + 1 or step_status_value == next_status:
                status = "pending"
            else:
                status = "disabled"

            step_indicator = StepIndicator(
                step_number=i + 1,
                title=step_info["title"],
                description=step_info["desc"],
                status=status,
                is_current=(step_status_value == next_status)
            )

            steps_layout.addWidget(step_indicator)

        scroll_area.setWidget(steps_widget)
        layout.addWidget(scroll_area)

        return container

    def create_input_section(self) -> QFrame:
        """Create input section for translator selection using a ComboBox."""
        section = QFrame()
        section.setObjectName("inputSection")

        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("انتخاب مترجم")
        title_label.setObjectName("inputTitle")

        # Description
        desc_label = QLabel("مترجم مسئول این فاکتور را از لیست زیر انتخاب کنید.")
        desc_label.setObjectName("inputDescription")

        # Input field (now a QComboBox)
        self.translator_combo = QComboBox()
        self.translator_combo.setObjectName("modernInput") # Can reuse style
        self.translator_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        if self.translators:
            self.translator_combo.addItems(self.translators)
        else:
            self.translator_combo.addItem("مترجمی یافت نشد")
            self.translator_combo.setEnabled(False) # Disable if empty

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(self.translator_combo)

        return section

    def create_action_buttons(self) -> QHBoxLayout:
        """Create action buttons layout."""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("انصراف")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setFixedSize(120, 45)
        cancel_btn.clicked.connect(self.reject)

        # Confirm button
        confirm_btn = QPushButton(f"انجام: {self.step_text}")
        confirm_btn.setObjectName("confirmButton")
        confirm_btn.setFixedSize(180, 45)
        confirm_btn.clicked.connect(self.confirm_status_change)

        layout.addWidget(cancel_btn)
        layout.addWidget(confirm_btn)

        return layout

    def confirm_status_change(self):
        """Handle status change confirmation."""
        translator = None

        # Get translator from the combo box if this is the assignment step
        if self.next_status == DeliveryStatus.ASSIGNED:
            translator = self.translator_combo.currentText()
            # Handle the case where no translators were found
            if translator == "مترجمی یافت نشد":
                translator = "نامشخص"

        # Create status change request
        request = StatusChangeRequest(
            invoice_number=self.invoice.invoice_number,
            current_status=self.invoice.delivery_status,
            target_status=self.next_status,
            translator=translator
        )

        # Emit the signal
        self.status_change_requested.emit(request)

        # Close dialog
        self.accept()

    def apply_stylesheet(self):
        """Apply the modern stylesheet to the dialog."""
        self.setStyleSheet(self.get_modern_stylesheet())

    @staticmethod
    def get_modern_stylesheet() -> str:
        """Return the modern CSS stylesheet for the dialog."""
        return """
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f9fa, stop:1 #e9ecef);
            color: #343a40;
        }

        QLabel#mainTitle {
            font-family: IranSANS;
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        QLabel#subtitle {
            font-family: IranSANS;
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 10px;
        }

        QFrame#invoiceCard {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        QLabel#cardLabel {
            font-family: IranSANS;
            font-size: 12px;
            color: #6c757d;
            font-family: IranSANS;
            font-weight: 500;
            margin-bottom: 2px;
        }

        QLabel#cardValue {
            font-family: IranSANS;
            font-size: 14px;
            color: #2c3e50;
            font-weight: bold;
        }

        QLabel#cardStatusValue {
            font-family: IranSANS;
            font-size: 14px;
            color: #e67e22;
            font-weight: bold;
            background-color: #fef5e7;
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid #f39c12;
        }

        QFrame#stepsContainer {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        QLabel#containerTitle {
            font-family: IranSANS;
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e9ecef;
        }

        QScrollArea#stepsScrollArea {
            border: none;
            background-color: transparent;
        }

        QFrame#inputSection {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        QLabel#inputTitle {
            font-family: IranSANS;
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        }

        QLabel#inputDescription {
            font-family: IranSANS;
            font-size: 13px;
            color: #6c757d;
            line-height: 1.4;
        }

        QLineEdit#modernInput {
            font-family: IranSANS;
            font-size: 14px;
            padding: 12px 16px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background-color: #f8f9fa;
            color: #2c3e50;
            selection-background-color: #007bff;
        }

        QLineEdit#modernInput:focus {
            border-color: #007bff;
            background-color: white;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
        }

        QPushButton#confirmButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #28a745, stop:1 #20c997);
            color: white;
            border: none;
            border-radius: 8px;
            font-family: IranSANS;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(40,167,69,0.3);
        }

        QPushButton#confirmButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #218838, stop:1 #1e7e34);
            box-shadow: 0 4px 8px rgba(40,167,69,0.4);
        }

        QPushButton#confirmButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1e7e34, stop:1 #155724);
        }

        QPushButton#cancelButton {
            background-color: #6c757d;
            color: white;
            border: none;
            border-radius: 8px;
            font-family: IranSANS;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(108,117,125,0.3);
        }

        QPushButton#cancelButton:hover {
            background-color: #5a6268;
            box-shadow: 0 4px 8px rgba(108,117,125,0.4);
        }

        QPushButton#cancelButton:pressed {
            background-color: #495057;
        }
        """
