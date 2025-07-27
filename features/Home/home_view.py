""" View layer for home page. Handles UI display and user interactions using PySide6. """
import sys
from typing import List, Tuple, Dict, Optional
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, Signal, QPoint, QTimer
from PySide6.QtGui import QColor, QBrush, QFont, QAction
from PySide6.QtWidgets import (
    QWidget, QTableWidgetItem, QHeaderView, QMenu, QTableWidget, QFrame, QGridLayout, QAbstractItemView, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton
)

from features.Home.home_controller import HomePageControllerFactory
from features.Home.home_models import DashboardStats
from features.Home.home_settings import SettingsManager, StatCardConfig
from features.Home.home_settings_view import HomepageSettingsDialog
from shared.utils.path_utils import return_resource
from shared.utils.number_utils import to_persian_number, to_english_number
from shared.utils.ui_utils import (show_error_message_box, show_information_message_box, show_question_message_box,
                                   show_warning_message_box)
from shared.utils.date_utils import convert_to_persian
from shared.widgets.toast_widget import show_toast

from pathlib import Path
from datetime import date

import logging

customers_database = return_resource('databases', 'customers.db')
invoices_database = return_resource('databases', 'invoices.db')
services_database = return_resource('databases', 'services.db')

logger = logging.getLogger(__name__)


class HomePageView(QWidget):
    """
    Main view class for the home page dashboard.
    Displays statistics, recent invoices, and provides navigation controls.
    """

    # Signals
    invoice_selected = Signal(int)  # Emitted when an invoice is selected
    refresh_requested = Signal()  # Emitted when refresh is requested
    settings_changed = Signal()  # Emitted when settings are changed
    settings_requested = Signal()  # Emitted when settings button is clicked

    def __init__(self, max_cards: int = 6, parent=None):
        super().__init__(parent)
        self.controller = HomePageControllerFactory.create_controller(customers_db_path=customers_database,
                                                                      documents_db_path=invoices_database,
                                                                      invoices_db_path=services_database)
        self.max_cards = max_cards
        self.current_settings = SettingsManager.load_settings(max_cards)
        self.stats_cards: Dict[str, QFrame] = {}  # Map card ID to widget
        self.current_stats: Optional[DashboardStats] = None
        logger.info(f"Loaded settings: {self.current_settings}")

        self._settings_changed = False
        self._init_ui()
        self.apply_settings()  # Apply loaded settings immediately
        self.setup_connections()
        self.load_initial_data()

    def _init_ui(self):
        """Initialize the user interface."""
        self.setObjectName("HomePageView")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header section
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # Stats section (will be populated based on settings)
        stats_widget = self.create_dashboard_stats()
        main_layout.addWidget(stats_widget)

        # Recent invoices section
        invoices_widget = self.create_recent_invoices_section()
        main_layout.addWidget(invoices_widget)

        # Apply stylesheet
        self.setStyleSheet(self.get_stylesheet())

    def _setup_settings_menu(self):
        """Setup the settings dropdown menu."""
        settings_menu = QMenu(self)

        # Main settings action
        settings_action = QAction("تنظیمات داشبورد", self)
        settings_action.triggered.connect(self._open_settings_dialog)
        settings_menu.addAction(settings_action)

        settings_menu.addSeparator()

        # Reset to defaults
        reset_action = QAction("بازگردانی به پیش‌فرض", self)
        reset_action.triggered.connect(self.reset_settings_to_default)
        settings_menu.addAction(reset_action)

        # Export settings
        export_action = QAction("صادرات تنظیمات", self)
        export_action.triggered.connect(self.export_settings)
        settings_menu.addAction(export_action)

        # Import settings
        import_action = QAction("واردات تنظیمات", self)
        import_action.triggered.connect(self.import_settings)
        settings_menu.addAction(import_action)

        self.settings_btn.setMenu(settings_menu)

    def reset_settings_to_default(self):
        """Reset settings to default values."""
        title = "تایید بازگردانی"
        message = "آیا مطمئن هستید که می‌خواهید تنظیمات را به حالت پیش‌فرض بازگردانید؟"
        button1 = "بله"
        button2 = "خیر"

        def yes_func():
            try:
                self.current_settings = SettingsManager.reset_to_defaults()
                self.apply_settings()
                show_information_message_box(self, "موفقیت", "تنظیمات به پیش‌فرض بازگردانده شد")
                logger.info("Settings reset to defaults")
            except Exception as e:
                logger.error(f"Error resetting settings: {e}")
                show_information_message_box(self, "خطا", f"خطا در بازگردانی تنظیمات: {str(e)}")

        show_question_message_box(self, title, message, button1, yes_func, button2)

    def reload_settings(self):
        """Reload settings from file and update display."""
        self.current_settings = SettingsManager.load_settings(self.max_cards)
        self._update_stats_cards()
        logger.info("Settings reloaded from file")

    def export_settings(self):
        """Export settings to file."""
        from PySide6.QtWidgets import QFileDialog

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "صادرات تنظیمات",
                "homepage_settings_export.json",
                "JSON Files (*.json)"
            )

            if file_path:
                success = SettingsManager.export_settings(Path(file_path), self.current_settings)
                if success:
                    show_information_message_box(self, "موفقیت", f"تنظیمات در {file_path} ذخیره شد")
                else:
                    show_error_message_box(self, "خطا", "خطا در صادرات تنظیمات")

        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            show_error_message_box(self, "خطا", f"خطا در صادرات: {str(e)}")

    def import_settings(self):
        """Import settings from file."""
        from PySide6.QtWidgets import QFileDialog

        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "واردات تنظیمات",
                "",
                "JSON Files (*.json)"
            )

            if file_path:
                imported_settings = SettingsManager.import_settings(Path(file_path))
                if imported_settings:
                    # Ask for confirmation
                    title = "تایید بارگذاری"
                    message = "آیا مطمئن هستید که می‌خواهید تنظیمات انتخاب شده را جایگزین کنید؟"
                    button1 = "بله"
                    button2 = "خیر"

                    def yes_func():
                        self.current_settings = imported_settings
                        success = SettingsManager.save_settings(self.current_settings)

                        if success:
                            self.apply_settings()
                            show_information_message_box(self, "موفقیت", "تنظیمات با موفقیت وارد شد")
                        else:
                            show_error_message_box(self, "خطا", "خطا در ذخیره تنظیمات وارد شده")

                    show_question_message_box(self, title, message, button1, yes_func, button2)

                else:
                    show_error_message_box(self, "خطا", "فایل تنظیمات نامعتبر است")

        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            show_error_message_box(self, "خطا", f"خطا در واردات: {str(e)}")

    def apply_settings(self):
        """Apply the current settings to the UI elements."""
        try:
            logger.info(f"Applying settings: {self.current_settings}")

            # Apply table settings
            if hasattr(self, 'invoices_table'):
                # Set row count (this might need adjustment based on your data loading logic)
                self.invoices_table.setRowCount(self.current_settings.row_count)

            # Update stats cards count
            self._update_stats_cards()

            # Update section title to reflect current settings
            if hasattr(self, 'section_title'):
                self.section_title.setText(
                    f"فاکتورهای {self.current_settings.threshold_days} روز اخیر"
                )

            # Refresh data with new settings
            self.on_refresh_clicked()
            self.settings_changed.emit()

            logger.info("Settings applied successfully")

        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            show_warning_message_box(self, "هشدار", f"خطا در اعمال تنظیمات: {str(e)}")

    def create_header(self) -> QHBoxLayout:
        """Create the header section with title and refresh button."""
        header_layout = QHBoxLayout()

        # Title
        title_label = QLabel("داشبورد")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Refresh button
        self.refresh_btn = QPushButton("بروزرسانی")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.setMaximumWidth(120)

        # Settings button
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFont(QFont("Tahoma", 18))
        self.settings_btn.setObjectName("settingsButton")
        self._setup_settings_menu()

        # Add buttons and title
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.settings_btn)
        header_layout.addStretch()
        header_layout.addWidget(title_label)

        return header_layout

    def create_dashboard_stats(self) -> QWidget:
        """Create the dashboard statistics section."""
        stats_widget = QWidget()
        stats_widget.setObjectName("statsWidget")

        self.stats_layout = QGridLayout(stats_widget)
        self.stats_layout.setSpacing(15)

        # Create stats cards based on current settings
        self._update_stats_cards()

        return stats_widget

    @staticmethod
    def _create_stat_card(card_config: StatCardConfig) -> QFrame:
        """Create a single statistics card based on configuration."""
        card = QFrame()
        card.setObjectName("statCard")
        card.setFrameStyle(QFrame.Shape.Box)

        # Apply dynamic styling with the card's color
        card.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                border-right: 4px solid {card_config.color};
                min-height: 100px;
            }}
            QFrame#statCard:hover {{
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border-color: #d0d0d0;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title_label = QLabel(card_config.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_label.setObjectName("statTitle")
        title_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 5px;")

        # Value
        value_label = QLabel("در حال بارگذاری...")
        value_label.setObjectName("statValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setStyleSheet(f"""
            font-size: 24px; 
            font-weight: bold; 
            color: {card_config.color};
            margin-top: 5px;
        """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        # Store card config in the widget for later reference
        card.card_config = card_config

        return card

    def _update_card_values(self):
        """Update the values displayed in all stat cards."""
        if not self.current_stats:
            return

        for card_id, card_widget in self.stats_cards.items():
            # Find the value label (it's the second child in the layout)
            layout = card_widget.layout()
            if layout and layout.count() >= 2:
                value_label = layout.itemAt(1).widget()
                if isinstance(value_label, QLabel):
                    # Get value from stats
                    value = self.current_stats.get_value_by_id(card_id)
                    value_label.setText(value)

    def _update_stats_cards(self):
        """Update statistics cards based on current settings."""
        # Clear existing cards
        self._clear_stats_layout()
        self.stats_cards.clear()

        # Get enabled cards from settings
        enabled_cards = self.current_settings.get_enabled_cards()

        if not enabled_cards:
            # Show "no cards configured" message
            no_cards_label = QLabel("هیچ کارت آماری انتخاب نشده است")
            no_cards_label.setObjectName("noCardsLabel")
            no_cards_label.setAlignment(Qt.AlignCenter)
            self.stats_layout.addWidget(no_cards_label, 0, 0, 1, 3)
            return

        # Create and arrange cards in grid (3 cards per row)
        for index, card_config in enumerate(enabled_cards):
            row = index // 3
            col = index % 3

            # Create card widget
            card_widget = self._create_stat_card(card_config)
            self.stats_cards[card_config.id] = card_widget

            # Add to grid layout
            self.stats_layout.addWidget(card_widget, row, col)

        # Update card values if we have current stats
        if self.current_stats:
            self._update_card_values()

    def update_stats_display(self, stats: DashboardStats):
        """
        Update all stat cards with the latest data from the stats object.
        """
        self.current_stats = stats  # Save reference for later refreshes

        for card_id, card_widget in self.stats_cards.items():
            layout = card_widget.layout()
            if layout and layout.count() >= 2:
                value_label = layout.itemAt(1).widget()
                if isinstance(value_label, QLabel):
                    value = stats.get_value_by_id(card_id)
                    if isinstance(value, int):
                        value_label.setText(to_persian_number(str(value)))
                    elif isinstance(value, str):
                        value_label.setText(value if value else "نامشخص")
                    else:
                        value_label.setText("نامشخص")

        self.animate_stats_update()

    def _clear_stats_layout(self):
        """Clear all widgets from the stats layout."""
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def create_recent_invoices_section(self) -> QWidget:
        """Create the recent invoices table section."""
        section_widget = QWidget()
        section_layout = QVBoxLayout(section_widget)
        section_layout.setSpacing(15)

        # Section header
        header_layout = QHBoxLayout()

        section_title = QLabel("فاکتورهای اخیر")
        section_title.setObjectName("sectionTitle")
        section_title.setAlignment(Qt.AlignmentFlag.AlignRight)

        view_all_btn = QPushButton("مشاهده همه")
        view_all_btn.setObjectName("viewAllButton")
        view_all_btn.setMaximumWidth(100)

        header_layout.addWidget(view_all_btn)
        header_layout.addStretch()
        header_layout.addWidget(section_title)

        section_layout.addLayout(header_layout)

        # Invoices table
        self.invoices_table = QTableWidget()
        self.setup_invoices_table()
        section_layout.addWidget(self.invoices_table)

        return section_widget

    def setup_invoices_table(self):
        """Set up the recent invoices table."""
        self.invoices_table.setObjectName("invoicesTable")
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.invoices_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.invoices_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.invoices_table.customContextMenuRequested.connect(self.contextMenuEvent)
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.invoices_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter | Qt.AlignRight)

        # Column headers (Persian)
        headers = ["شماره فاکتور", "مشتری", "تاریخ تحویل", "مترجم", "مانده (تومان)", "وضعیت", "عملیات‌ها"]
        self.invoices_table.setColumnCount(len(headers))
        self.invoices_table.setHorizontalHeaderLabels(headers)

        # Configure table appearance
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set table properties
        self.invoices_table.setMaximumHeight(400)
        self.invoices_table.setSortingEnabled(True)

    def setup_connections(self):
        """Setup signal-slot connections."""
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        self.invoices_table.cellDoubleClicked.connect(self.on_invoice_double_clicked)

    def load_initial_data(self):
        """Load initial data from the controller."""
        try:
            self.refresh_dashboard_stats()
            self.refresh_recent_invoices()
        except Exception as e:
            show_error_message_box(self, "خطا", f"خطا در بارگذاری داده‌ها: {str(e)}")

    def refresh_dashboard_stats(self):
        """Refresh dashboard statistics."""
        try:
            stats = self.controller.update_dashboard()
            self.update_stats_display(stats)
        except Exception as e:
            show_error_message_box(self, "خطا", f"خطا در بارگذاری آمار: {str(e)}")

    def _setup_auto_save(self):
        """Setup auto-save timer for settings."""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_settings)
        self.auto_save_timer.start(300000)  # 5 minutes
        self._settings_changed = False

    def _auto_save_settings(self):
        """Auto-save settings if they were changed."""
        if self._settings_changed:
            success = SettingsManager.save_settings(self.current_settings)
            if success:
                logger.info("Auto-saved settings")
                self._settings_changed = False

    def _open_settings_dialog(self):
        """Open the settings dialog."""
        dialog = HomepageSettingsDialog(self.current_settings, self.max_cards, self)

        if dialog.exec() == HomepageSettingsDialog.Accepted:
            # Get updated settings
            updated_settings = dialog.get_updated_settings()

            # Save settings
            if SettingsManager.save_settings(updated_settings):
                self.current_settings = updated_settings
                # Refresh the stats cards display
                self._update_stats_cards()
                logger.info("Settings updated and saved successfully")
            else:
                logger.error("Failed to save updated settings")

    def animate_stats_update(self):
        """Animate the statistics update."""
        self.stats_animation = QVariantAnimation()
        self.stats_animation.setDuration(500)
        self.stats_animation.setStartValue(0.0)
        self.stats_animation.setEndValue(1.0)
        self.stats_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.stats_animation.start()

    def refresh_recent_invoices(self):
        """Refresh the recent invoices table."""
        try:
            invoices = self.controller.get_recent_invoices()
            self.populate_invoices_table(invoices)
        except Exception as e:
            show_error_message_box(self, "خطا", f"خطا در بارگذاری فاکتورها: {str(e)}")

    @staticmethod
    def create_operations_menu(file_path: str, invoice_number: int, controller, parent=None) -> QMenu:
        """
        Create and return a QMenu with actions related to an invoice.

        Args:
            file_path (str): Path to the invoice PDF.
            invoice_number (int): Invoice identifier.
            controller: Controller instance to handle actions.
            parent: Optional QWidget parent.

        Returns:
            QMenu: The menu with bound actions.
        """
        from shared.dialogs.status_change_dialog import StatusChangeDialog
        menu = QMenu(parent)

        view_invoice = QAction("مشاهده فاکتور", menu)
        view_invoice.triggered.connect(lambda: controller.handle_view_pdf_request(file_path))

        change_status = QAction("تغییر وضعیت", menu)
        change_status.triggered.connect(
            lambda: controller.handle_change_invoice_status_request(invoice_number, StatusChangeDialog, parent)
        )

        # Then add it to the menu actions:
        menu.addActions([view_invoice, change_status])
        return menu

    def create_operations_button(self, file_path: str, invoice_number: int, controller) -> QPushButton:
        """
        Create a button with a vertical ellipsis icon to show the operations' menu.

        Args:
            file_path (str): Path to the invoice PDF.
            invoice_number (int): Invoice identifier.
            controller: Controller instance to handle actions.
        Returns:
            QPushButton: The button that shows the menu on click.
        """
        button = QPushButton("⋮", self)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFlat(True)
        button.setFont(QFont("Tahoma", 15))

        menu = self.create_operations_menu(file_path, invoice_number, controller, self)

        def show_menu():
            menu.popup(button.mapToGlobal(button.rect().bottomLeft()))

        button.clicked.connect(show_menu)
        return button

    def contextMenuEvent(self, pos: QPoint):
        index = self.invoices_table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        item = self.invoices_table.item(row, 0)
        if item is None:
            return

        try:
            invoice_number = int(to_english_number(item.text()))
        except ValueError:
            return

        invoice = self.controller.invoice_data_for_context_menu(invoice_number)
        if invoice is None:
            return

        file_path = invoice.pdf_file_path

        # Optional: visually select the row
        self.invoices_table.selectRow(row)

        # Create and show the menu
        menu = self.create_operations_menu(file_path, invoice_number, self.controller, self)
        menu.exec(self.invoices_table.viewport().mapToGlobal(pos))

    def populate_invoices_table(self, invoices_with_priority: List[Tuple]):
        """
        Populate the invoices table with data and apply color coding.

        Args:
            invoices_with_priority: List of tuples containing (invoice, priority_label)
        """
        self.invoices_table.setRowCount(len(invoices_with_priority))

        for row, (invoice, priority) in enumerate(invoices_with_priority):
            persian_number = to_persian_number(row + 1)
            self.invoices_table.setVerticalHeaderItem(row, QTableWidgetItem(persian_number))

            # Invoice number - 1st row
            invoice_num_item = QTableWidgetItem(to_persian_number(str(invoice.invoice_number)))
            invoice_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 0, invoice_num_item)

            # Customer name
            customer_item = QTableWidgetItem(invoice.name)
            customer_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 1, customer_item)

            # Due date
            gregorian_date = invoice.delivery_date.strftime("%Y/%m/%d")
            jalali_date_item = QTableWidgetItem(convert_to_persian(gregorian_date))
            jalali_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 2, jalali_date_item)

            # Translator
            translator_item = QTableWidgetItem(invoice.translator)
            translator_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 3, translator_item)

            # Amount
            raw_amount = f"{invoice.final_amount:,}"
            amount_item = QTableWidgetItem(f"{to_persian_number(raw_amount)} تومان")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 4, amount_item)

            # Status
            status_text = self._get_status_text(invoice.delivery_status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 5, status_item)

            # Actions button
            action_btn = self.create_operations_button(invoice.pdf_file_path, invoice.invoice_number, self.controller)
            self.invoices_table.setCellWidget(row, 6, action_btn)

        # Apply row color based on priority
        self._apply_color_on_rows(invoices_with_priority)

    def _apply_color_on_rows(self, invoice_rows_with_priority: List[Tuple]):
        for row_index, (invoice, priority) in enumerate(invoice_rows_with_priority):
            if priority == 'urgent':
                color = QColor(255, 200, 200)  # Light red
            elif priority == 'needs_attention':
                color = QColor(255, 220, 150)  # Orange-yellow
            else:
                continue

            for col_idx in range(self.invoices_table.columnCount() - 1):  # Skip column with button
                item = self.invoices_table.item(row_index, col_idx)
                if item is not None:
                    # Use QBrush for more reliable color application
                    brush = QBrush(color)
                    item.setBackground(brush)
                    # Also set a role-based approach as backup
                    item.setData(Qt.ItemDataRole.BackgroundRole, brush)

    @staticmethod
    def _get_status_text(delivery_status: int) -> str:
        """
        Convert delivery status code to Persian text.

        Args:
            delivery_status: Status code

        Returns:
            Persian status text
        """
        status_map = {
            0: "تحویل گرفته شده",
            1: "در حال ترجمه",
            2: "ترجمه شده، نیاز به تاییدات",
            3: "آماده تحویل",
            4: "دریافت توسط مشتری"
        }
        return status_map.get(delivery_status, "نامشخص")

    def on_refresh_clicked(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()
        self.load_initial_data()

    def on_invoice_double_clicked(self, row: int):
        """Handle invoice table double click."""
        invoice_number = self.get_invoice_id_from_row(row)
        if invoice_number:
            # Copy to clipboard
            QApplication.clipboard().setText(str(invoice_number))

            # Emit signal
            self.invoice_selected.emit(invoice_number)

            # Show confirmation
            show_toast(self, "✅ شماره فاکتور کپی شد")

    def on_invoice_view_clicked(self, invoice_id: int):
        """Handle invoice view button click."""
        self.invoice_selected.emit(invoice_id)

    def get_invoice_id_from_row(self, row: int) -> int:
        """Get invoice ID from table row."""
        try:
            invoice_number = self.invoices_table.item(row, 0).text()
            # Convert from Persian number and return as int
            return int(to_english_number(invoice_number))
        except (AttributeError, ValueError):
            return 0

    @staticmethod
    def get_stylesheet() -> str:
        """Return the CSS stylesheet for the view."""
        return """
        QWidget#HomePageView {
            background-color: #f5f5f5;
        }

        QLabel#pageTitle {
            font-family: IranSANS;
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        QLabel#sectionTitle {
            font-family: IranSANS;
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
            margin-bottom: 10px;
        }

        QPushButton#refreshButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-family: IranSANS;
            font-size: 14px;
            font-weight: bold;
        }

        QPushButton#refreshButton:hover {
            background-color: #2980b9;
        }

        QPushButton#refreshButton:pressed {
            background-color: #21618c;
        }

        QPushButton#settingsButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 18px;
        }

        QPushButton#settingsButton:hover {
            background-color: #7f8c8d;
        }

        QPushButton#viewAllButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 6px 12px;
            font-family: IranSANS;
            font-size: 12px;
        }

        QPushButton#viewAllButton:hover {
            background-color: #7f8c8d;
        }

        QPushButton#actionButton {
            background-color: #27ae60;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 4px 8px;
            font-family: IranSANS;
            font-size: 12px;
        }

        QPushButton#actionButton:hover {
            background-color: #229954;
        }

        QWidget#statsWidget {
            background-color: transparent;
        }

        QTableWidget#invoicesTable {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            selection-background-color: #e3f2fd;
            gridline-color: #f0f0f0;
        }

        QTableWidget#invoicesTable::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }

        QHeaderView::section {
            background-color: #f8f9fa;
            color: #495057;
            padding: 10px;
            border: 1px solid #dee2e6;
            font-family: IranSANS;
            font-weight: bold;
        }
        """


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = HomePageView()
    window.show()
    sys.exit(app.exec())
