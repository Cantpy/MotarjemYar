# wizard_host/invoice_page_wizard.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget
from PySide6.QtCore import Signal


class MainWindowView(QWidget):
    """
    The main UI container for the wizard. It is a 'dumb' widget.
    - It creates the visual structure (top/bottom bars, stacked widget).
    - It emits signals when the user clicks navigation buttons.
    - It has public slots that allow the Logic/Controller to command it.
    """
    # Signals reporting user's intent to navigate
    next_button_clicked = Signal()
    prev_button_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("InvoiceWizard")
        self.setWindowTitle("ایجاد فاکتور جدید")

        # --- UI Attributes ---
        self.step_labels = []
        self.stacked_widget = QStackedWidget()

        # --- Create the UI ---
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        """Builds the main visual structure of the wizard."""
        self.main_layout = QVBoxLayout(self)
        self._create_top_bar()
        self._create_bottom_bar()  # Create bottom bar before adding stacked_widget

        self.main_layout.addLayout(self.top_bar_layout)
        self.main_layout.addWidget(self.stacked_widget)
        self.main_layout.addLayout(self.bottom_bar_layout)

    def _create_top_bar(self):
        self.top_bar_layout = QHBoxLayout()
        self.top_bar_layout.setObjectName('top_bar_layout')
        self.top_bar_layout.setContentsMargins(20, 10, 20, 10)
        steps = ["۱. اطلاعات مشتری", "۲. انتخاب اسناد", "۳. تخصیص اسناد", "۴. جزئیات فاکتور", "۵. پیش‌نمایش"]
        for i, text in enumerate(steps):
            label = QLabel(text)
            label.setObjectName("StepLabel")
            self.step_labels.append(label)
            self.top_bar_layout.addWidget(label)
            if i < len(steps) - 1:
                self.top_bar_layout.addStretch()

    def _create_bottom_bar(self):
        self.bottom_bar_layout = QHBoxLayout()
        self.prev_button = QPushButton("مرحله قبل")
        self.next_button = QPushButton("مرحله بعد")
        self.next_button.setObjectName("PrimaryButton")
        self.bottom_bar_layout.addStretch()
        self.bottom_bar_layout.addWidget(self.prev_button)
        self.bottom_bar_layout.addWidget(self.next_button)

    def _connect_internal_signals(self):
        """Connects internal buttons to this widget's public signals."""
        self.prev_button.clicked.connect(self.prev_button_clicked.emit)
        self.next_button.clicked.connect(self.next_button_clicked.emit)

    # --- Public Slots for the Controller/Logic to Call ---

    def set_current_step(self, index: int):
        """Commands the view to switch to a specific page index."""
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            self._update_step_ui(index)

    def _update_step_ui(self, current_index: int):
        """Updates the visual style of the top bar and enables/disables buttons."""
        for i, label in enumerate(self.step_labels):
            label.setProperty("state", "active" if i == current_index else "inactive")
            label.style().unpolish(label)
            label.style().polish(label)

        self.prev_button.setEnabled(current_index > 0)
        self.next_button.setEnabled(current_index < self.stacked_widget.count() - 1)
