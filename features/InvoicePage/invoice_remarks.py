from PySide6.QtWidgets import (
    QTextEdit, QVBoxLayout, QDialog, QDialogButtonBox, QToolBar, QColorDialog, QFontComboBox, QSpinBox)
from PySide6.QtGui import QTextCharFormat, QFont, QAction
from PySide6.QtCore import Qt


class RemarksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ویرایش توضحات")
        self.setGeometry(150, 150, 500, 350)

        self.parent = parent

        # Create a toolbar for text formatting
        self.toolbar = QToolBar(self)
        self.toolbar2 = QToolBar(self)

        # Bold action
        self.bold_action = QAction("پررنگ", self)
        self.bold_action.triggered.connect(self.toggle_bold)
        self.bold_action.setCheckable(True)
        self.toolbar.addAction(self.bold_action)

        # Italic action
        self.italic_action = QAction("مورب", self)
        self.italic_action.triggered.connect(self.toggle_italic)
        self.italic_action.setCheckable(True)
        self.toolbar.addAction(self.italic_action)

        # Underline action
        self.underline_action = QAction("زیرخط‌دار", self)
        self.underline_action.triggered.connect(self.toggle_underline)
        self.underline_action.setCheckable(True)
        self.toolbar.addAction(self.underline_action)

        # Strikethrough action
        self.strikethrough_action = QAction("خط‌خورده", self)
        self.strikethrough_action.triggered.connect(self.toggle_strikethrough)
        self.strikethrough_action.setCheckable(True)
        self.toolbar.addAction(self.strikethrough_action)

        # Text color action
        self.color_action = QAction("رنگ", self)
        self.color_action.triggered.connect(self.change_text_color)
        self.toolbar.addAction(self.color_action)

        # Font selection
        self.font_box = QFontComboBox(self)
        self.font_box.currentFontChanged.connect(self.set_font)
        self.toolbar.addWidget(self.font_box)

        # Font size selection
        self.font_size_box = QSpinBox(self)
        self.font_size_box.setRange(8, 48)
        self.font_size_box.setValue(12)
        self.font_size_box.setMinimumWidth(70)
        self.font_size_box.valueChanged.connect(self.set_font_size)
        self.toolbar2.addWidget(self.font_size_box)

        # Alignment actions
        self.align_left_action = QAction("چپ‌چین", self)
        self.align_left_action.triggered.connect(lambda: self.set_alignment(Qt.AlignLeft))
        self.toolbar2.addAction(self.align_left_action)

        self.align_center_action = QAction("وسط‌چین", self)
        self.align_center_action.triggered.connect(lambda: self.set_alignment(Qt.AlignCenter))
        self.toolbar2.addAction(self.align_center_action)

        self.align_right_action = QAction("راست‌چین", self)
        self.align_right_action.triggered.connect(lambda: self.set_alignment(Qt.AlignRight))
        self.toolbar2.addAction(self.align_right_action)

        # Create QTextEdit for editing remarks
        self.text_edit = QTextEdit(self)

        # Create OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)  # Save changes
        self.button_box.rejected.connect(self.reject)  # Cancel editing

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.toolbar2)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def set_text(self, text):
        """Load existing remarks into the text editor"""
        self.text_edit.setHtml(text)

        # After setting text, sync font and size with current cursor
        cursor_format = self.text_edit.currentCharFormat()

        font = cursor_format.font()
        point_size = cursor_format.fontPointSize()

        if font:
            self.font_box.setCurrentFont(font)
        if point_size > 0:
            self.font_size_box.setValue(int(point_size))

    def get_text(self):
        """Return formatted text"""
        return self.text_edit.toHtml()

    def toggle_bold(self):
        """Toggle bold text."""
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold if not self.bold_action.isChecked() else QFont.Normal)
        self.apply_format(fmt)

    def toggle_italic(self):
        """Toggle italic text."""
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.italic_action.isChecked())
        self.apply_format(fmt)

    def toggle_underline(self):
        """Toggle underlined text."""
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.underline_action.isChecked())
        self.apply_format(fmt)

    def toggle_strikethrough(self):
        """Toggle strikethrough text."""
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(self.strikethrough_action.isChecked())
        self.apply_format(fmt)

    def change_text_color(self):
        """Open a color dialog to change text color."""
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self.apply_format(fmt)

    def set_font(self, font):
        """Set selected font."""
        fmt = QTextCharFormat()
        fmt.setFont(font)
        self.apply_format(fmt)

    def set_font_size(self, size):
        """Set selected font size."""
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self.apply_format(fmt)

    def set_alignment(self, alignment):
        """Set text alignment."""
        self.text_edit.setAlignment(alignment)

    def apply_format(self, fmt):
        """Apply text formatting to the selected text."""
        cursor = self.text_edit.textCursor()
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)
