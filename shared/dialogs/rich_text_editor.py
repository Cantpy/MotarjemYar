"""
Rich text editor widget with formatting toolbar.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                               QFontComboBox, QSpinBox, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCharFormat, QFont


class RichTextEdit(QWidget):
    """Enhanced text editor with formatting toolbar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the widget with toolbar and text edit."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Create toolbar
        self.toolbar = self.create_toolbar()
        layout.addWidget(self.toolbar)

        # Create text edit
        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        # Connect signals
        self.text_edit.cursorPositionChanged.connect(self.update_toolbar_state)

    def create_toolbar(self):
        """Create and return the formatting toolbar."""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(5, 2, 5, 2)

        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setMaximumWidth(150)
        self.font_combo.currentFontChanged.connect(self.change_font_family)
        toolbar_layout.addWidget(self.font_combo)

        # Font size
        self.font_size_combo = QSpinBox()
        self.font_size_combo.setRange(8, 72)
        self.font_size_combo.setValue(12)
        self.font_size_combo.setMaximumWidth(60)
        self.font_size_combo.valueChanged.connect(self.change_font_size)
        toolbar_layout.addWidget(self.font_size_combo)

        # Separator
        toolbar_layout.addWidget(self.create_separator())

        # Bold
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setMaximumSize(30, 25)
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.bold_btn.clicked.connect(self.toggle_bold)
        toolbar_layout.addWidget(self.bold_btn)

        # Italic
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setMaximumSize(30, 25)
        self.italic_btn.setStyleSheet("font-style: italic;")
        self.italic_btn.clicked.connect(self.toggle_italic)
        toolbar_layout.addWidget(self.italic_btn)

        # Underline
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setMaximumSize(30, 25)
        self.underline_btn.setStyleSheet("text-decoration: underline;")
        self.underline_btn.clicked.connect(self.toggle_underline)
        toolbar_layout.addWidget(self.underline_btn)

        # Strikethrough
        self.strike_btn = QPushButton("S")
        self.strike_btn.setCheckable(True)
        self.strike_btn.setMaximumSize(30, 25)
        self.strike_btn.setStyleSheet("text-decoration: line-through;")
        self.strike_btn.clicked.connect(self.toggle_strikethrough)
        toolbar_layout.addWidget(self.strike_btn)

        # Separator
        toolbar_layout.addWidget(self.create_separator())

        # Alignment buttons
        align_left_btn = QPushButton("چپ")
        align_left_btn.setMaximumSize(40, 25)
        align_left_btn.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignLeft))
        toolbar_layout.addWidget(align_left_btn)

        align_center_btn = QPushButton("وسط")
        align_center_btn.setMaximumSize(40, 25)
        align_center_btn.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignCenter))
        toolbar_layout.addWidget(align_center_btn)

        align_right_btn = QPushButton("راست")
        align_right_btn.setMaximumSize(40, 25)
        align_right_btn.clicked.connect(lambda: self.text_edit.setAlignment(Qt.AlignmentFlag.AlignRight))
        toolbar_layout.addWidget(align_right_btn)

        # Add stretch to push everything to the left
        toolbar_layout.addStretch()

        return toolbar_widget

    def create_separator(self):
        """Create a visual separator."""
        separator = QWidget()
        separator.setFixedSize(1, 20)
        separator.setStyleSheet("background-color: #ccc;")
        return separator

    def change_font_family(self, font):
        """Change font family of selected text."""
        char_format = QTextCharFormat()
        char_format.setFontFamily(font.family())
        self.text_edit.textCursor().mergeCharFormat(char_format)

    def change_font_size(self, size):
        """Change font size of selected text."""
        char_format = QTextCharFormat()
        char_format.setFontPointSize(size)
        self.text_edit.textCursor().mergeCharFormat(char_format)

    def toggle_bold(self):
        """Toggle bold formatting."""
        char_format = QTextCharFormat()
        weight = QFont.Weight.Bold if self.bold_btn.isChecked() else QFont.Weight.Normal
        char_format.setFontWeight(weight)
        self.text_edit.textCursor().mergeCharFormat(char_format)

    def toggle_italic(self):
        """Toggle italic formatting."""
        char_format = QTextCharFormat()
        char_format.setFontItalic(self.italic_btn.isChecked())
        self.text_edit.textCursor().mergeCharFormat(char_format)

    def toggle_underline(self):
        """Toggle underline formatting."""
        char_format = QTextCharFormat()
        char_format.setFontUnderline(self.underline_btn.isChecked())
        self.text_edit.textCursor().mergeCharFormat(char_format)

    def toggle_strikethrough(self):
        """Toggle strikethrough formatting."""
        char_format = QTextCharFormat()
        char_format.setFontStrikeOut(self.strike_btn.isChecked())
        self.text_edit.textCursor().mergeCharFormat(char_format)

    def update_toolbar_state(self):
        """Update toolbar button states based on current cursor position."""
        try:
            cursor = self.text_edit.textCursor()
            char_format = cursor.charFormat()

            # Update font combo
            font_family = char_format.fontFamily()
            if font_family:
                font = QFont(font_family)
                self.font_combo.setCurrentFont(font)

            # Update font size
            font_size = char_format.fontPointSize()
            if font_size > 0:
                self.font_size_combo.setValue(int(font_size))

            # Update formatting buttons
            self.bold_btn.setChecked(char_format.fontWeight() == QFont.Weight.Bold)
            self.italic_btn.setChecked(char_format.fontItalic())
            self.underline_btn.setChecked(char_format.fontUnderline())
            self.strike_btn.setChecked(char_format.fontStrikeOut())
        except Exception:
            # Ignore any errors during state updates
            pass

    # Expose QTextEdit methods for compatibility
    def setPlainText(self, text):
        """Set plain text content."""
        self.text_edit.setPlainText(text)

    def toPlainText(self):
        """Get plain text content."""
        return self.text_edit.toPlainText()

    def setText(self, text):
        """Set HTML text content."""
        self.text_edit.setText(text)

    def toHtml(self):
        """Get HTML content."""
        return self.text_edit.toHtml()

    def setFocus(self):
        """Set focus to the text edit."""
        self.text_edit.setFocus()

    def insertPlainText(self, text):
        """Insert plain text at cursor position."""
        self.text_edit.insertPlainText(text)

    def insertHtml(self, html):
        """Insert HTML at cursor position."""
        self.text_edit.insertHtml(html)

    def clear(self):
        """Clear all text content."""
        self.text_edit.clear()

    def selectAll(self):
        """Select all text content."""
        self.text_edit.selectAll()

    def copy(self):
        """Copy selected text to clipboard."""
        self.text_edit.copy()

    def cut(self):
        """Cut selected text to clipboard."""
        self.text_edit.cut()

    def paste(self):
        """Paste text from clipboard."""
        self.text_edit.paste()

    def undo(self):
        """Undo last action."""
        self.text_edit.undo()

    def redo(self):
        """Redo last undone action."""
        self.text_edit.redo()

    def find(self, text, flags=None):
        """Find text in the editor."""
        if flags is None:
            return self.text_edit.find(text)
        return self.text_edit.find(text, flags)

    def setReadOnly(self, read_only):
        """Set read-only mode."""
        self.text_edit.setReadOnly(read_only)
        self.toolbar.setEnabled(not read_only)

    def isReadOnly(self):
        """Check if editor is in read-only mode."""
        return self.text_edit.isReadOnly()

    def textCursor(self):
        """Get the current text cursor."""
        return self.text_edit.textCursor()

    def setTextCursor(self, cursor):
        """Set the text cursor."""
        self.text_edit.setTextCursor(cursor)

    def document(self):
        """Get the text document."""
        return self.text_edit.document()

    def setDocument(self, document):
        """Set the text document."""
        self.text_edit.setDocument(document)

    def fontFamily(self):
        """Get current font family."""
        return self.text_edit.fontFamily()

    def setFontFamily(self, family):
        """Set font family."""
        self.text_edit.setFontFamily(family)

    def fontSize(self):
        """Get current font size."""
        return self.text_edit.fontSize()

    def setFontSize(self, size):
        """Set font size."""
        self.text_edit.setFontPointSize(size)

    def currentCharFormat(self):
        """Get current character format."""
        return self.text_edit.currentCharFormat()

    def setCurrentCharFormat(self, format):
        """Set current character format."""
        self.text_edit.setCurrentCharFormat(format)

    def alignment(self):
        """Get current text alignment."""
        return self.text_edit.alignment()

    def setAlignment(self, alignment):
        """Set text alignment."""
        self.text_edit.setAlignment(alignment)

    def canUndo(self):
        """Check if undo is available."""
        return self.text_edit.document().isUndoAvailable()

    def canRedo(self):
        """Check if redo is available."""
        return self.text_edit.document().isRedoAvailable()

    def isModified(self):
        """Check if document has been modified."""
        return self.text_edit.document().isModified()

    def setModified(self, modified):
        """Set document modified state."""
        self.text_edit.document().setModified(modified)
