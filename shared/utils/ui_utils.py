"""
UI-related utility functions for Qt widgets and styling.
"""
import re
from PySide6.QtWidgets import (QMessageBox, QLineEdit, QLabel, QFormLayout, QTableWidget, QHeaderView)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter, QIcon


def show_message_box(parent, title, message, icon_type, button_text="متوجه شدم"):
    """
    Generic function to show a message box with a single button.

    Args:
        parent: Parent widget
        title (str): Window title
        message (str): MessageModel to display
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
    renderer = QSvgRenderer(str(svg_path))

    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)  # Transparent background

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    label.setPixmap(pixmap)
    label.setFixedSize(size)  # Optional: fix size to match icon


class TableColumnResizer:
    """Helper to resize QTableWidget columns based on ratios (independent of 100%)."""

    def __init__(self, table: QTableWidget, ratios: list[int | float], scrollbar_margin: int = 0):
        if not isinstance(table, QTableWidget):
            raise TypeError("table must be a QTableWidget")
        if len(ratios) != table.columnCount():
            raise ValueError("ratios length must match the number of table columns")

        self.table = table
        self.ratios = ratios
        self.scrollbar_margin = scrollbar_margin

        # Kill Qt's stretching behavior
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for i in range(header.count()):
            header.setSectionResizeMode(i, QHeaderView.Fixed)

        # Hook resize event
        original_resize_event = self.table.resizeEvent

        def _resize_event(event):
            self.resize_columns()
            original_resize_event(event)

        self.table.resizeEvent = _resize_event
        self.resize_columns()

    def resize_columns(self):
        """Resize table columns proportionally to ratios."""
        total_ratio = sum(self.ratios)
        available_width = self.table.viewport().width() - self.scrollbar_margin

        for i, ratio in enumerate(self.ratios):
            col_width = int(available_width * (ratio / total_ratio))
            self.table.setColumnWidth(i, col_width)
