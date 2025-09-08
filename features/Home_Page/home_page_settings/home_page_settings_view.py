# features/home_page/settings/_view.py

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QVBoxLayout, QFrame, QLabel,
                               QScrollArea, QWidget, QGroupBox, QCheckBox, QColorDialog, QHBoxLayout, QPushButton)
from PySide6.QtGui import QColor
from features.Home_Page.home_page_settings.home_page_settings_models import Settings, StatCardConfig
from features.Home_Page.home_page_styles import HOME_SETTINGS_STYLES


class StatCardWidget(QFrame):
    """
    A self-contained widget for configuring a single stat card.
    It manages its own state and emits a signal when changed.
    """
    # This signal tells the parent dialog that something has changed.
    card_changed = Signal()

    def __init__(self, card_config: StatCardConfig, parent=None):
        """
        Initializes the widget with a StatCardConfig DTO.
        """
        super().__init__(parent)
        self.card_config = card_config
        self._init_ui()
        # You can add a specific stylesheet for this widget if needed
        # self.setObjectName("StatCardWidgetFrame")

    def _init_ui(self):
        """Sets up the UI elements for this widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(15)

        # 1. Enable/Disable Checkbox
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(self.card_config.enabled)
        # When the checkbox state changes, call our internal handler
        self.enabled_checkbox.stateChanged.connect(self._on_state_changed)
        layout.addWidget(self.enabled_checkbox)

        # 2. Card Title Label
        self.title_label = QLabel(self.card_config.title)
        self.title_label.setObjectName("cardTitle")
        layout.addWidget(self.title_label, 1)  # The '1' gives it stretch factor

        # 3. Color Picker Button
        self.color_button = QPushButton()
        self.color_button.setObjectName("colorButton")
        self.color_button.setFixedSize(40, 25)
        self.color_button.setToolTip("تغییر رنگ کارت")
        self.color_button.clicked.connect(self._choose_color)
        self._update_color_button_style()  # Set initial color
        layout.addWidget(self.color_button)

    def _update_color_button_style(self):
        """Applies the current color to the button's stylesheet."""
        self.color_button.setStyleSheet(f"""
            QPushButton#colorButton {{
                background-color: {self.card_config.color};
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }}
            QPushButton#colorButton:hover {{
                border-color: #7f8c8d;
            }}
        """)

    def _choose_color(self):
        """Opens a color dialog and updates the config if a valid color is chosen."""
        initial_color = QColor(self.card_config.color)
        new_color = QColorDialog.getColor(initial_color, self)

        if new_color.isValid():
            # Update the DTO stored in this widget
            self.card_config.color = new_color.name()
            # Refresh the button's appearance
            self._update_color_button_style()
            # Notify the parent dialog that a change has occurred
            self.card_changed.emit()

    def _on_state_changed(self):
        """Handles the checkbox state changing."""
        # Update the DTO stored in this widget
        self.card_config.enabled = self.enabled_checkbox.isChecked()
        # Notify the parent dialog that a change has occurred
        self.card_changed.emit()


class HomepageSettingsDialog(QDialog):
    """A 'dumb' _view for editing homepage settings."""
    save_requested = Signal(Settings)   # Emits a DTO with the new values

    def __init__(self, current_settings: Settings, parent=None):
        super().__init__(parent)
        self.settings_to_display = current_settings

        self.setWindowTitle("تنظیمات داشبورد")
        self.setFixedSize(600, 700)
        self.setModal(True)
        self._settings_changed = False
        self._init_ui()
        self._apply_stylesheet()

    def _init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title_label = QLabel("تنظیمات داشبورد")
        title_label.setObjectName("dialogTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("titleSeparator")
        main_layout.addWidget(separator)

        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("settingsScroll")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # Basic settings form
        basic_group = QGroupBox("تنظیمات اصلی")
        basic_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        basic_group.setObjectName("settingsGroup")
        form_layout = QFormLayout(basic_group)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Create spinboxes with proper ranges and styling
        self.row_spin = self._create_spinbox(1, 100, self.settings_to_display.row_count)
        self.days_spin = self._create_spinbox(1, 365, self.settings_to_display.threshold_days)
        self.orange_spin = self._create_spinbox(1, 30, self.settings_to_display.orange_threshold_days)
        self.red_spin = self._create_spinbox(1, 30, self.settings_to_display.red_threshold_days)

        # Add form rows with styled labels
        form_layout.addRow(self._create_label("تعداد ردیف جدول:"), self.row_spin)
        form_layout.addRow(self._create_label("نمایش فاکتورهای تا چند روز پیش:"), self.days_spin)
        form_layout.addRow(self._create_label("آستانه نارنجی (روز):"), self.orange_spin)
        form_layout.addRow(self._create_label("آستانه قرمز (روز):"), self.red_spin)

        scroll_layout.addWidget(basic_group)

        # Stats cards configuration
        cards_group = QGroupBox("تنظیمات کارت‌های آمار")
        cards_group.setObjectName("settingsGroup")
        cards_layout = QVBoxLayout(cards_group)
        cards_layout.setSpacing(15)

        # Info label
        info_label = QLabel("کارت‌های نمایش داده شده باید مضرب ۳ باشند (۳، ۶، ۹، ...)")
        info_label.setObjectName("infoLabel")
        info_label.setWordWrap(True)
        cards_layout.addWidget(info_label)

        # Cards container
        cards_container = QWidget()
        self.cards_layout = QVBoxLayout(cards_container)
        self.cards_layout.setSpacing(5)

        # Create card widgets
        self._create_card_widgets()

        cards_layout.addWidget(cards_container)

        # Card count display
        self.card_count_label = QLabel()
        self.card_count_label.setObjectName("cardCountLabel")
        self._update_card_count_display()
        cards_layout.addWidget(self.card_count_label)

        scroll_layout.addWidget(cards_group)

        # Add stretch
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Bottom separator
        bottom_separator = QFrame()
        bottom_separator.setFrameShape(QFrame.Shape.HLine)
        bottom_separator.setFrameShadow(QFrame.Shadow.Sunken)
        bottom_separator.setObjectName("bottomSeparator")
        main_layout.addWidget(bottom_separator)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.setObjectName("dialogButtons")

        # Set Persian text for buttons
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")

        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

    def _create_card_widgets(self):
        """
        This method now works perfectly because StatCardWidget exists.
        """
        # Clear any existing widgets first
        self.card_widgets = []
        # (Assuming self.cards_layout is a QVBoxLayout)
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create the new widgets from the DTO
        for card_config in self.settings_to_display.stat_cards:
            card_widget = StatCardWidget(card_config)
            # When the child widget changes, update our count display
            card_widget.card_changed.connect(self._update_card_count_display)
            self.card_widgets.append(card_widget)
            self.cards_layout.addWidget(card_widget)

    def _update_card_count_display(self):
        """Update the card count display label."""
        enabled_count = len([w for w in self.card_widgets if w.enabled_checkbox.isChecked()])
        # ------------------------

        is_valid = enabled_count % 3 == 0

        if is_valid:
            self.card_count_label.setText(f"تعداد کارت‌های انتخاب شده: {enabled_count} ✓")
            self.card_count_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.card_count_label.setText(f"تعداد کارت‌های انتخاب شده: {enabled_count} ⚠ (باید مضرب ۳ باشد)")
            self.card_count_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def _create_spinbox(self, min_val: int, max_val: int, current_val: int) -> QSpinBox:
        """Create a styled spinbox with proper range."""
        spinbox = QSpinBox()
        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setValue(current_val)
        spinbox.setObjectName("settingsSpinBox")
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return spinbox

    def _create_label(self, text: str) -> QLabel:
        """Create a styled label."""
        label = QLabel(text)
        label.setObjectName("settingsLabel")
        return label

    def _apply_stylesheet(self):
        """Apply stylesheet that matches the homepage design."""
        self.setStyleSheet(HOME_SETTINGS_STYLES)

    def _on_accept(self):
        """Gathers data from UI fields and emits the save_requested signal."""
        # Create a new Settings DTO from the values in the spinboxes, etc.
        updated_settings = Settings(
            row_count=self.row_spin.value(),
            threshold_days=self.days_spin.value(),
            orange_threshold_days=self.orange_spin.value(),
            red_threshold_days=self.red_spin.value(),
            stat_cards=[w.card_config for w in self.card_widgets]
        )
        self.save_requested.emit(updated_settings)
