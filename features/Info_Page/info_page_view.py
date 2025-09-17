# features/Info_Page/info_page_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea,
                               QFrame, QGridLayout, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


class InfoPageView(QWidget):
    """The main _view for the info page. It is a dumb component."""

    # Signal to indicate a link has been clicked
    link_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About InvoiceMaster Pro")
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

    def _create_widgets(self):
        """Create all UI elements for the _view."""
        # Main container and scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)

        # --- App Overview ---
        self.overview_label = self._create_section_header("App Overview / About")
        self.overview_text = self._create_body_text(
            "InvoiceMaster Pro is a desktop application designed to simplify and streamline your invoicing process. "
            "Our mission is to provide a reliable, efficient, and user-friendly tool for freelancers and small businesses."
        )

        # --- Version & Update Info ---
        self.version_header_label = self._create_section_header("Version & Update Info")
        self.version_label = self._create_body_text("Current Version: N/A")
        self.release_date_label = self._create_body_text("Release Date: N/A")

        # --- Changelog ---
        self.changelog_header_label = self._create_section_header("Changelog")
        self.changelog_layout = QVBoxLayout()
        self.changelog_layout.setSpacing(5)

        # --- Contact Info ---
        self.contact_header_label = self._create_section_header("Contact Information")
        self.contact_text = self._create_body_text(
            "Email: <a href='mailto:support@invoicemasterpro.com'>support@invoicemasterpro.com</a><br>"
            "Phone: +1 (800) 555-0199"
        )
        self.contact_text.setOpenExternalLinks(True)

        # --- FAQ ---
        self.faq_header_label = self._create_section_header("FAQ / Help Section")
        self.faq_layout = QVBoxLayout()
        self.faq_layout.setSpacing(10)

        # --- Feedback Button ---
        self.feedback_button = QPushButton("Submit Feedback")

    def _setup_layout(self):
        """Arrange UI elements in layouts."""
        layout = QVBoxLayout(self)

        self.main_layout.addWidget(self.overview_label)
        self.main_layout.addWidget(self.overview_text)
        self.main_layout.addWidget(self._create_separator())

        self.main_layout.addWidget(self.version_header_label)
        self.main_layout.addWidget(self.version_label)
        self.main_layout.addWidget(self.release_date_label)
        self.main_layout.addWidget(self._create_separator())

        self.main_layout.addWidget(self.changelog_header_label)
        self.main_layout.addLayout(self.changelog_layout)
        self.main_layout.addWidget(self._create_separator())

        self.main_layout.addWidget(self.contact_header_label)
        self.main_layout.addWidget(self.contact_text)
        self.main_layout.addWidget(self._create_separator())

        self.main_layout.addWidget(self.faq_header_label)
        self.main_layout.addLayout(self.faq_layout)
        self.main_layout.addWidget(self._create_separator())

        self.main_layout.addWidget(self.feedback_button, 0, Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch()

        self.scroll_area.setWidget(self.main_widget)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def _connect_signals(self):
        """Connect widget signals to internal handlers or emit signals."""
        # Example of how you would connect a link if it wasn't handled automatically
        # self.contact_text.linkActivated.connect(self.link_activated.emit)
        pass  # Most signals are connected in the controller

    # --- Public methods for the controller to use ---
    def set_version_info(self, version: str, release_date: str):
        self.version_label.setText(f"Current Version: {version}")
        self.release_date_label.setText(f"Release Date: {release_date}")

    def set_changelog(self, entries: list):
        # Clear previous entries
        for i in reversed(range(self.changelog_layout.count())):
            self.changelog_layout.itemAt(i).widget().setParent(None)

        for entry in entries:
            label = self._create_body_text(f"• {entry}")
            self.changelog_layout.addWidget(label)

    def set_faq(self, faq_items: list):
        # Clear previous entries
        for i in reversed(range(self.faq_layout.count())):
            self.faq_layout.itemAt(i).widget().setParent(None)

        for item in faq_items:
            question = QLabel(f"<b>Q: {item.question}</b>")
            answer = self._create_body_text(f"A: {item.answer}")
            self.faq_layout.addWidget(question)
            self.faq_layout.addWidget(answer)

    # --- Helper methods for creating styled widgets ---
    def _create_section_header(self, text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setPointSize(14)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        return label

    def _create_body_text(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        return label

    def _create_separator(self) -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("margin-top: 10px; margin-bottom: 10px;")
        return separator
