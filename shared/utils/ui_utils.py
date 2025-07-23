"""
UI-related utility functions for Qt widgets and styling.
"""
import re
from PySide6.QtWidgets import (QMessageBox, QLineEdit, QLabel, QFormLayout, QWidget, QVBoxLayout)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPainter, QIcon, QFont
from typing import List


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
