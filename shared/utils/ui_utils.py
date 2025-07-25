"""
UI-related utility functions for Qt widgets and styling.
"""
import re
from PySide6.QtWidgets import (QMessageBox, QLineEdit, QLabel, QFormLayout, QWidget, QVBoxLayout, QDialog, QHBoxLayout,
                               QPushButton, QFrame, QScrollArea)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QPixmap, QPainter, QIcon
from typing import List

from features.Home.models import StatusChangeRequest, DeliveryStatus
from shared.utils.number_utils import to_persian_number
from shared.entities.entities import Invoice


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

    def __init__(self, invoice: Invoice, next_status: int, step_text: str, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        self.next_status = next_status
        self.step_text = step_text

        # Define all delivery steps
        self.delivery_steps = [
            {"status": DeliveryStatus.ISSUED, "title": "صدور فاکتور", "desc": "فاکتور صادر شده، در انتظار تخصیص مترجم"},
            {"status": DeliveryStatus.ASSIGNED, "title": "در حال ترجمه",
             "desc": "انتخاب و تخصیص مترجم برای این فاکتور"},
            {"status": DeliveryStatus.TRANSLATED, "title": "در انتظار تاییدات",
             "desc": "ترجمه انجام شد، در انتظار تاییدات (دادگستری، امور خارجه، و یا مترجم)"},
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

        # Customer name
        customer_layout = QVBoxLayout()
        customer_label = QLabel("نام مشتری")
        customer_label.setObjectName("cardLabel")
        customer_val_label = QLabel(self.invoice.name)
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
        """Create input section for translator selection."""
        section = QFrame()
        section.setObjectName("inputSection")

        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("انتخاب مترجم")
        title_label.setObjectName("inputTitle")

        # Description
        desc_label = QLabel("نام مترجم مورد نظر را وارد کنید یا خالی بگذارید تا 'نامشخص' ثبت شود")
        desc_label.setObjectName("inputDescription")
        # desc_label.setWordWrap(True)

        # Input field
        self.translator_input = QLineEdit()
        self.translator_input.setObjectName("modernInput")
        self.translator_input.setPlaceholderText("نام مترجم...")
        self.translator_input.setText("نامشخص")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(self.translator_input)

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

        # Get translator input if this is step 1
        if self.next_status == DeliveryStatus.ASSIGNED:
            translator = self.translator_input.text().strip()
            if not translator:
                translator = "نامشخص"

        # Create status change request
        request = StatusChangeRequest(
            invoice_number=int(self.invoice.invoice_number),
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


class Toast(QWidget):
    def __init__(self, parent, message: str, duration=3000, on_close=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.on_close = on_close

        self.label = QLabel(message)
        self.label.setStyleSheet("""
            background-color: #333;
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.mousePressEvent = self.dismiss_on_click

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.adjustSize()

        self.setWindowOpacity(0.0)
        self.show()

        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()

        QTimer.singleShot(duration, self.close_with_fade)

    def dismiss_on_click(self, event):
        self.close_with_fade()

    def close_with_fade(self):
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self._final_close)
        self.fade_out.start()

    def _final_close(self):
        self.close()
        if self.on_close:
            self.on_close(self)


class ToastManager:
    def __init__(self, parent):
        self.parent = parent
        self.active_toasts: List[Toast] = []

    def show(self, message: str, duration: int = 3000):
        toast = Toast(self.parent, message, duration, on_close=self._remove_toast)
        self.active_toasts.append(toast)
        self._reposition_toasts()

    def _remove_toast(self, toast):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            self._reposition_toasts()

    def _reposition_toasts(self):
        margin = 10
        spacing = 10
        bottom_offset = 40

        for index, toast in enumerate(reversed(self.active_toasts)):
            toast.adjustSize()
            parent_rect = self.parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - toast.width()) // 2
            y = (parent_rect.y() + parent_rect.height() - toast.height() -
                 bottom_offset - index * (toast.height() + spacing))
            toast.move(x, y)


_toast_manager = None


def show_toast(parent, message: str, duration=3000):
    global _toast_manager
    if _toast_manager is None or _toast_manager.parent != parent:
        _toast_manager = ToastManager(parent)
    _toast_manager.show(message, duration)


def show_message_box(parent, title, message, icon_type, button_text="متوجه شدم"):
    """
    Generic function to show a message box with a single button.

    Args:
        parent: Parent widget
        title (str): Window title
        message (str): Message to display
        icon_type: QMessageBox.Icon type (Critical, Warning, Information)
        button_text (str): Text for the button
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon_type)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.addButton(button_text, QMessageBox.ButtonRole.AcceptRole)
    msg_box.exec()


def show_error_message_box(parent, title, message):
    """Show an error message box."""
    show_message_box(parent, title, message, QMessageBox.Icon.Critical)


def show_warning_message_box(parent, title, message):
    """Show a warning message box."""
    show_message_box(parent, title, message, QMessageBox.Icon.Warning)


def show_information_message_box(parent, title, message):
    """Show an information message box."""
    show_message_box(parent, title, message, QMessageBox.Icon.Information)


def show_question_message_box(parent, title, message, button_1, yes_func,
                              button_2, button_3=None, action_func=None):
    """
    Show a question message box with 2 or 3 buttons and execute functions based on selection.

    Args:
        parent: Parent widget
        title (str): Window title
        message (str): Question message
        button_1 (str): Text for first button (Yes role)
        yes_func (callable): Function to call when first button is clicked
        button_2 (str): Text for second button (No role)
        button_3 (str, optional): Text for third button (Action role)
        action_func (callable, optional): Function to call when third button is clicked
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    # Add buttons
    yes_button = msg_box.addButton(button_1, QMessageBox.ButtonRole.YesRole)
    no_button = msg_box.addButton(button_2, QMessageBox.ButtonRole.NoRole)

    action_button = None
    if button_3:
        action_button = msg_box.addButton(button_3, QMessageBox.ButtonRole.ActionRole)

    msg_box.exec()
    clicked_button = msg_box.clickedButton()

    # Execute appropriate function based on clicked button
    if clicked_button == yes_button and yes_func:
        yes_func()
    elif clicked_button == no_button:
        msg_box.reject()
    elif button_3 and clicked_button == action_button and action_func:
        action_func()


def show_field_error_form(line_edit: QLineEdit, message: str, form_layout: QFormLayout):
    """Highlight input field and show error message under it in layout."""
    line_edit.setStyleSheet("border: 2px solid red; border-radius: 4px;")

    if not hasattr(line_edit, "error_label"):
        error_label = QLabel()
        error_label.setStyleSheet("color: red; font-size: 11px;")
        error_label.setWordWrap(True)
        line_edit.error_label = error_label

        # Find the row of the line_edit
        row_index = -1
        for i in range(form_layout.rowCount()):
            field_widget = form_layout.itemAt(i, QFormLayout.FieldRole)
            if field_widget and field_widget.widget() == line_edit:
                row_index = i
                break

        if row_index != -1:
            # Insert error label in the row just after the input field
            form_layout.insertRow(row_index + 1, "", error_label)

    line_edit.error_label.setText(message)
    line_edit.error_label.show()


def show_field_error(line_edit: QLineEdit, message):
    """Highlight input field with red border and display error message below it."""
    line_edit.setStyleSheet("border: 2px solid red; border-radius: 4px;")

    # Check if the error label already exists, if not, create it
    if not hasattr(line_edit, "error_label"):
        line_edit.error_label = QLabel(line_edit.parent())
        line_edit.error_label.setStyleSheet("color: red; font-size: 11px;")
        line_edit.error_label.setWordWrap(True)

    line_edit.error_label.setText(message)
    line_edit.error_label.setGeometry(line_edit.x(), line_edit.y() + line_edit.height() + 2, line_edit.width(), 20)
    line_edit.error_label.show()


def clear_field_error(line_edit: QLineEdit):
    """Clear error styling and message from a line edit field."""
    line_edit.setStyleSheet("")  # Clear red border
    if hasattr(line_edit, "error_label"):
        line_edit.error_label.hide()


def render_colored_svg(svg_path, size, color_hex):
    """
    Render an SVG file with a specific color.

    Args:
        svg_path (str): Path to SVG file
        size (QSize): Size for the rendered icon
        color_hex (str): Hex color code

    Returns:
        QIcon: Rendered colored icon
    """
    # Read SVG content
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Replace 'currentColor' with actual color hex in fill and stroke
    svg_content = re.sub(r'fill="currentColor"', f'fill="{color_hex}"', svg_content)
    svg_content = re.sub(r'stroke="currentColor"', f'stroke="{color_hex}"', svg_content)

    # Load the modified SVG content
    svg_bytes = bytes(svg_content, encoding='utf-8')
    renderer = QSvgRenderer(svg_bytes)

    # Render to pixmap
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def set_svg_icon(svg_path: str, size: QSize, label: QLabel):
    """
    Set an SVG icon to a QLabel.

    Args:
        svg_path (str): Path to SVG file
        size (QSize): Size for the icon
        label (QLabel): Label widget to set icon on
    """
    renderer = QSvgRenderer(svg_path)

    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)  # Transparent background

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    label.setPixmap(pixmap)
    label.setFixedSize(size)  # Optional: fix size to match icon
