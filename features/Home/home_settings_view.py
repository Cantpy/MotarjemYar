import sys

from PySide6.QtWidgets import (QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QVBoxLayout, QFrame, QLabel,
                               QColorDialog, QCheckBox, QHBoxLayout, QPushButton, QScrollArea, QWidget, QGroupBox, )
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from features.Home.home_settings import StatCardConfig, Settings
import logging
from shared.utils.ui_utils import show_warning_message_box, show_error_message_box, show_information_message_box
from typing import List

logger = logging.getLogger(__name__)


class StatCardWidget(QFrame):
    """Widget for configuring a single stat card."""

    card_changed = Signal()

    def __init__(self, card_config: StatCardConfig, parent=None):
        super().__init__(parent)
        self.card_config = card_config
        self._init_ui()
        self._apply_stylesheet()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(15)

        # Enable checkbox
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(self.card_config.enabled)
        self.enabled_checkbox.stateChanged.connect(self._on_changed)
        layout.addWidget(self.enabled_checkbox)

        # Card title
        self.title_label = QLabel(self.card_config.title)
        self.title_label.setObjectName("cardTitle")
        layout.addWidget(self.title_label, 1)

        # Color button
        self.color_button = QPushButton()
        self.color_button.setObjectName("colorButton")
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self._choose_color)
        self._update_color_button()
        layout.addWidget(self.color_button)

    def _update_color_button(self):
        """Update the color button appearance."""
        self.color_button.setStyleSheet(f"""
            QPushButton#colorButton {{
                background-color: {self.card_config.color};
                border: 2px solid #bdc3c7;
                border-radius: 4px;
            }}
            QPushButton#colorButton:hover {{
                border-color: #95a5a6;
            }}
        """)

    def _choose_color(self):
        """Open color dialog to choose card color."""
        color = QColorDialog.getColor(QColor(self.card_config.color), self)
        if color.isValid():
            self.card_config.color = color.name()
            self._update_color_button()
            self.card_changed.emit()

    def _on_changed(self):
        """Handle checkbox state change."""
        self.card_config.enabled = self.enabled_checkbox.isChecked()
        self.card_changed.emit()

    def _apply_stylesheet(self):
        """Apply styling to the widget."""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin: 2px 0;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border-color: #bdc3c7;
            }
            QLabel#cardTitle {
                font-family: IranSANS;
                font-size: 13px;
                color: #2c3e50;
                font-weight: normal;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #bdc3c7;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url(:/icons/check.png);
            }
            QCheckBox::indicator:hover {
                border-color: #95a5a6;
            }
        """)


class HomepageSettingsDialog(QDialog):
    """Settings page for manipulating the design of the homepage."""
    settingsChanged = Signal()

    def __init__(self, current_settings: Settings, max_cards: int = 6, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات داشبورد")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.settings = current_settings
        self.max_cards = max_cards
        self.setFixedSize(600, 700)
        self.setModal(True)
        self._settings_changed = False
        self.card_widgets: List[StatCardWidget] = []
        self.settingsChanged.connect(self._on_settings_changed)
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
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
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
        basic_group.setObjectName("settingsGroup")
        form_layout = QFormLayout(basic_group)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Create spinboxes with proper ranges and styling
        self.row_spin = self._create_spinbox(1, 100, self.settings.row_count)
        self.days_spin = self._create_spinbox(1, 365, self.settings.threshold_days)
        self.orange_spin = self._create_spinbox(1, 30, self.settings.orange_threshold_days)
        self.red_spin = self._create_spinbox(1, 30, self.settings.red_threshold_days)

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
        bottom_separator.setFrameShape(QFrame.HLine)
        bottom_separator.setFrameShadow(QFrame.Sunken)
        bottom_separator.setObjectName("bottomSeparator")
        main_layout.addWidget(bottom_separator)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setObjectName("dialogButtons")

        # Set Persian text for buttons
        buttons.button(QDialogButtonBox.Ok).setText("تایید")
        buttons.button(QDialogButtonBox.Cancel).setText("لغو")

        buttons.accepted.connect(self._accept_settings)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

    def _create_card_widgets(self):
        """Create widgets for all available stat cards."""
        for card in self.settings.get_available_cards():
            card_widget = StatCardWidget(card)
            card_widget.card_changed.connect(self._on_card_changed)
            self.card_widgets.append(card_widget)
            self.cards_layout.addWidget(card_widget)

    def _on_card_changed(self):
        """Handle changes in card configuration."""
        self._settings_changed = True
        self._update_card_count_display()
        self.settingsChanged.emit()

    def _update_card_count_display(self):
        """Update the card count display label."""
        enabled_count = len([card for card in self.settings.stat_cards if card.enabled])
        is_valid = enabled_count % 3 == 0

        if is_valid:
            self.card_count_label.setText(f"تعداد کارت‌های انتخاب شده: {enabled_count} ✓")
            self.card_count_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.card_count_label.setText(f"تعداد کارت‌های انتخاب شده: {enabled_count} ⚠ (باید مضرب ۳ باشد)")
            self.card_count_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def _accept_settings(self):
        """Handle OK button press with validation."""
        enabled_count = len([card for card in self.settings.stat_cards if card.enabled])

        if enabled_count % 3 != 0:
            show_warning_message_box(
                self,
                "خطا در تنظیمات",
                "تعداد کارت‌های انتخاب شده باید مضرب ۳ باشد.\n"
                "لطفاً تعداد کارت‌ها را به ۳، ۶، ۹ یا ... تغییر دهید."
            )
            return

        if enabled_count > self.max_cards:
            show_warning_message_box(
                self,
                "خطا در تنظیمات",
                f"در حال حاضر حداکثر {self.max_cards} کارت قابل نمایش است.\n"
                f"تعداد انتخاب شده: {enabled_count}"
            )
            return

        self.accept()

    def _create_spinbox(self, min_val: int, max_val: int, current_val: int) -> QSpinBox:
        """Create a styled spinbox with proper range."""
        spinbox = QSpinBox()
        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setValue(current_val)
        spinbox.setObjectName("settingsSpinBox")
        spinbox.setAlignment(Qt.AlignCenter)
        spinbox.valueChanged.connect(self._emit_settings_changed)
        return spinbox

    def _create_label(self, text: str) -> QLabel:
        """Create a styled label."""
        label = QLabel(text)
        label.setObjectName("settingsLabel")
        return label

    def _emit_settings_changed(self):
        self._settings_changed = True
        self.settingsChanged.emit()

    def _on_settings_changed(self):
        logger.info("Settings changed in dialog.")

    def has_changes(self) -> bool:
        return self._settings_changed

    def _apply_stylesheet(self):
        """Apply stylesheet that matches the homepage design."""
        self.setStyleSheet("""
            /* Dialog background */
            QDialog {
                background-color: #f5f5f5;
                font-family: IranSANS;
                border-radius: 10px;
            }

            /* Scroll area */
            QScrollArea#settingsScroll {
                border: none;
                background-color: transparent;
            }
            QScrollArea#settingsScroll QScrollBar:vertical {
                background-color: #ecf0f1;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollArea#settingsScroll QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollArea#settingsScroll QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }

            /* Dialog title */
            QLabel#dialogTitle {
                font-family: IranSANS;
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background-color: transparent;
            }

            /* Group boxes */
            QGroupBox#settingsGroup {
                font-family: IranSANS;
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: #f5f5f5;
            }

            /* Info label */
            QLabel#infoLabel {
                font-family: IranSANS;
                font-size: 12px;
                color: #7f8c8d;
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #3498db;
            }

            /* Card count label */
            QLabel#cardCountLabel {
                font-family: IranSANS;
                font-size: 14px;
                padding: 8px;
                border-radius: 4px;
                background-color: #ecf0f1;
            }

            /* Separators */
            QFrame#titleSeparator, QFrame#bottomSeparator {
                color: #bdc3c7;
                background-color: #bdc3c7;
                border: none;
                height: 1px;
                margin: 5px 0;
            }

            /* Settings labels */
            QLabel#settingsLabel {
                font-family: IranSANS;
                font-size: 14px;
                font-weight: normal;
                color: #34495e;
                padding: 8px 10px;
                background-color: transparent;
                min-width: 200px;
            }

            /* SpinBox styling to match homepage buttons */
            QSpinBox#settingsSpinBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 10px 15px;
                font-family: IranSANS;
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
                selection-background-color: #3498db;
                selection-color: white;
                min-width: 100px;
                max-width: 120px;
            }

            QSpinBox#settingsSpinBox:hover {
                border-color: #95a5a6;
                background-color: #fafafa;
            }

            QSpinBox#settingsSpinBox:focus {
                border-color: #3498db;
                background-color: white;
                outline: none;
            }

            /* SpinBox buttons */
            QSpinBox#settingsSpinBox::up-button {
                background-color: #ecf0f1;
                border: none;
                border-left: 1px solid #bdc3c7;
                border-radius: 0 4px 0 0;
                width: 18px;
                height: 15px;
            }

            QSpinBox#settingsSpinBox::up-button:hover {
                background-color: #d5dbdb;
            }

            QSpinBox#settingsSpinBox::up-button:pressed {
                background-color: #bdc3c7;
            }

            QSpinBox#settingsSpinBox::down-button {
                background-color: #ecf0f1;
                border: none;
                border-left: 1px solid #bdc3c7;
                border-radius: 0 0 4px 0;
                width: 18px;
                height: 15px;
            }

            QSpinBox#settingsSpinBox::down-button:hover {
                background-color: #d5dbdb;
            }

            QSpinBox#settingsSpinBox::down-button:pressed {
                background-color: #bdc3c7;
            }

            /* SpinBox arrows */
            QSpinBox#settingsSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #7f8c8d;
                width: 0;
                height: 0;
            }

            QSpinBox#settingsSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #7f8c8d;
                width: 0;
                height: 0;
            }

            /* Dialog buttons container */
            QDialogButtonBox#dialogButtons {
                background-color: transparent;
                border: none;
                padding: 10px 0;
            }

            /* OK Button - matches refreshButton style */
            QDialogButtonBox#dialogButtons QPushButton:default {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-family: IranSANS;
                font-size: 14px;
                font-weight: bold;
                min-width: 90px;
                margin: 0 5px;
            }

            QDialogButtonBox#dialogButtons QPushButton:default:hover {
                background-color: #2980b9;
            }

            QDialogButtonBox#dialogButtons QPushButton:default:pressed {
                background-color: #21618c;
            }

            /* Cancel Button - matches settingsButton style */
            QDialogButtonBox#dialogButtons QPushButton:!default {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-family: IranSANS;
                font-size: 14px;
                font-weight: bold;
                min-width: 90px;
                margin: 0 5px;
            }

            QDialogButtonBox#dialogButtons QPushButton:!default:hover {
                background-color: #7f8c8d;
            }

            QDialogButtonBox#dialogButtons QPushButton:!default:pressed {
                background-color: #6c7b7d;
            }

            /* Form layout spacing adjustments */
            QFormLayout {
                spacing: 20px;
            }
        """)

    def get_updated_settings(self) -> Settings:
        """Get updated settings from the dialog."""
        # Update basic settings
        self.settings.row_count = self.row_spin.value()
        self.settings.threshold_days = self.days_spin.value()
        self.settings.orange_threshold_days = self.orange_spin.value()
        self.settings.red_threshold_days = self.red_spin.value()

        # Update total cards number based on enabled cards
        enabled_cards = [card for card in self.settings.stat_cards if card.enabled]
        self.settings.total_cards_number = len(enabled_cards)

        return self.settings

    def closeEvent(self, event):
        """Handle window close event - save settings before closing."""
        try:
            if self._settings_changed:
                SettingsManager.save_settings(self.settings)
                logger.info("Settings saved on window close")
        except Exception as e:
            logger.error(f"Error saving settings on close: {e}")

        event.accept()


def show_homepage_settings_dialog(current_settings: Settings, parent=None) -> Settings:
    """
    Show the homepage settings dialog with error handling.

    Args:
        current_settings: The current Settings instance
        parent: Parent widget

    Returns:
        Updated Settings instance or original if cancelled/failed
    """
    try:
        dialog = HomepageSettingsDialog(current_settings, parent)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_updated_settings()

            # Validate new settings before returning
            if _validate_dialog_settings(new_settings, parent):
                return new_settings
            else:
                return current_settings  # Return original if validation failed

        return current_settings  # Return original settings if cancelled

    except Exception as e:
        logger.error(f"Error in settings dialog: {e}")
        if parent:
            show_error_message_box(parent, "خطا", f"خطا در نمایش تنظیمات: {str(e)}")
        return current_settings


def _validate_dialog_settings(settings: Settings, parent=None) -> bool:
    """Validate settings from dialog with user feedback."""
    errors = []

    if settings.red_threshold_days >= settings.orange_threshold_days:
        errors.append("آستانه قرمز باید کمتر از آستانه نارنجی باشد")

    if settings.orange_threshold_days >= settings.threshold_days:
        errors.append("آستانه نارنجی باید کمتر از حد آستانه کلی باشد")

    if errors and parent:
        message = str.join("خطا در تنظیمات", "\n".join(errors))
        show_warning_message_box(parent, "خطا", message)
        return False

    return True


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from features.Home.home_settings_repo import SettingsManager
    settings = SettingsManager.load_settings()
    app = QApplication([])
    window = HomepageSettingsDialog(settings)
    window.show()
    sys.exit(app.exec())
