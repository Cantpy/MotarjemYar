# features/Home_Page/home_page_view.py

from typing import List, Tuple, Dict, Optional
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, Signal, QPoint, Slot
from PySide6.QtGui import QColor, QBrush, QFont, QAction
from PySide6.QtWidgets import (
    QWidget, QTableWidgetItem, QHeaderView, QMenu, QTableWidget, QFrame, QGridLayout, QAbstractItemView, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QApplication
)

from shared.utils.number_utils import to_persian_number
from shared.utils.date_utils import convert_to_persian
from shared.widgets.toast_widget import show_toast
from features.Home_Page.home_page_styles import HOME_PAGE_STYLES
from features.Home_Page.home_page_models import DashboardStats
from features.Home_Page.home_page_settings.home_page_settings_models import StatCardConfig, Settings

import logging

logger = logging.getLogger(__name__)


class HomePageView(QWidget):
    """
    Main _view class for the home page dashboard.
    Displays statistics, recent invoices, and provides navigation controls.
    This is a "Passive View" - it holds no logic.
    """
    # Signals emitted by the _view for the controller to act upon
    refresh_requested = Signal()
    settings_requested = Signal()
    reset_settings_requested = Signal()
    import_settings_requested = Signal()
    export_settings_requested = Signal()
    invoice_selected = Signal(int)
    view_invoice_pdf_requested = Signal(int)
    change_invoice_status_requested = Signal(int)
    operations_menu_requested = Signal(int, QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.stats_cards: Dict[str, QFrame] = {}
        self._table_data_cache = []
        self._current_stats_dto: Optional[DashboardStats] = None
        self._init_ui()
        self.setup_connections()

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
        self.setStyleSheet(HOME_PAGE_STYLES)

    def _setup_settings_menu(self):
        """Setup the settings dropdown menu."""
        settings_menu = QMenu(self)

        settings_action = QAction("تنظیمات داشبورد", self)
        settings_action.triggered.connect(self.settings_requested.emit) # EMIT SIGNAL
        settings_menu.addAction(settings_action)

        settings_menu.addSeparator()

        reset_action = QAction("بازگردانی به پیش‌فرض", self)
        reset_action.triggered.connect(self.reset_settings_requested.emit) # EMIT SIGNAL
        settings_menu.addAction(reset_action)

        export_action = QAction("صادرات تنظیمات", self)
        export_action.triggered.connect(self.export_settings_requested.emit) # EMIT SIGNAL
        settings_menu.addAction(export_action)

        import_action = QAction("واردات تنظیمات", self)
        import_action.triggered.connect(self.import_settings_requested.emit) # EMIT SIGNAL
        settings_menu.addAction(import_action)

        self.settings_btn.setMenu(settings_menu)

    @Slot(object)  # The object is the Settings data class
    def apply_settings(self, settings: Settings):
        """
        PUBLIC SLOT: Apply the given settings to the UI elements.
        Called by the Controller.
        """
        logger.info(f"Applying settings from controller: {settings}")
        if hasattr(self, 'invoices_table'):
            self.invoices_table.setRowCount(settings.row_count)

        self._update_stats_cards(settings.get_enabled_cards())

        if hasattr(self, 'section_title'):
            self.section_title.setText(f"فاکتورهای {settings.threshold_days} روز اخیر")

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

        # # Create stats cards based on current settings
        # self._update_stats_cards()

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
        """Update the values displayed in all visible stat cards using the cached DTO."""
        if not self._current_stats_dto:
            return

        for card_id, card_widget in self.stats_cards.items():
            layout = card_widget.layout()
            if layout and layout.count() >= 2:
                value_label = layout.itemAt(1).widget()
                if isinstance(value_label, QLabel):
                    # Get value from the cached DTO
                    value = self._current_stats_dto.get_value_by_id(card_id)
                    value_label.setText(str(value))

    def _update_stats_cards(self, enabled_cards_config: List[StatCardConfig]):
        """
        Update statistics cards based on the provided configuration.
        This method is now stateless and only uses its arguments.
        """
        self._clear_stats_layout()
        self.stats_cards.clear()

        # CORRECT: Use the argument passed by the controller.
        if not enabled_cards_config:
            # Show "no cards configured" message
            no_cards_label = QLabel("هیچ کارت آماری انتخاب نشده است")
            no_cards_label.setObjectName("noCardsLabel")
            no_cards_label.setAlignment(Qt.AlignCenter)
            self.stats_layout.addWidget(no_cards_label, 0, 0, 1, 3)
            return

        # Create and arrange cards in grid (3 cards per row)
        for index, card_config in enumerate(enabled_cards_config):
            row = index // 3
            col = index % 3
            card_widget = self._create_stat_card(card_config)
            self.stats_cards[card_config.id] = card_widget
            self.stats_layout.addWidget(card_widget, row, col)

            # After rebuilding the cards, refresh their values if we have data.
        if self._current_stats_dto:
            self._update_card_values()

    @Slot(object)  # The object is the DashboardStats DTO
    def update_stats_display(self, stats: DashboardStats):
        """PUBLIC SLOT: Caches the new stats and updates all card values."""
        # Cache the latest stats DTO from the controller
        self._current_stats_dto = stats
        self._update_card_values()  # Call the helper to apply the new values
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
        """
        Setup signal-slot connections.
        Connects UI element events to this _view's own signals.
        """
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.invoices_table.cellDoubleClicked.connect(self._on_invoice_double_clicked)
        self.invoices_table.customContextMenuRequested.connect(self._on_context_menu_requested)

    def animate_stats_update(self):
        """Animate the statistics update."""
        self.stats_animation = QVariantAnimation()
        self.stats_animation.setDuration(500)
        self.stats_animation.setStartValue(0.0)
        self.stats_animation.setEndValue(1.0)
        self.stats_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.stats_animation.start()

    @Slot(list)  # List of tuples (InvoiceModel, priority)
    def populate_invoices_table(self, invoices_with_priority: List[Tuple]):
        """
        PUBLIC SLOT: Populates the table.
        It also caches the data for later use (like context menus).
        """
        self._table_data_cache = invoices_with_priority
        self.invoices_table.setRowCount(len(invoices_with_priority))

        for row, (invoice_dto, priority) in enumerate(invoices_with_priority):
            persian_number = to_persian_number(row + 1)
            self.invoices_table.setVerticalHeaderItem(row, QTableWidgetItem(persian_number))

            # Invoice number - 1st row
            invoice_num_item = QTableWidgetItem(to_persian_number(str(invoice_dto.invoice_number)))
            invoice_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 0, invoice_num_item)

            # CustomerModel name
            customer_item = QTableWidgetItem(invoice_dto.name)
            customer_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 1, customer_item)

            # Due date
            gregorian_date = invoice_dto.delivery_date.strftime("%Y/%m/%d")
            jalali_date_item = QTableWidgetItem(convert_to_persian(gregorian_date))
            jalali_date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 2, jalali_date_item)

            # Translator
            translator_item = QTableWidgetItem(invoice_dto.translator)
            translator_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 3, translator_item)

            # Amount
            raw_amount = f"{invoice_dto.final_amount:,}"
            amount_item = QTableWidgetItem(f"{to_persian_number(raw_amount)} تومان")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 4, amount_item)

            # Status
            status_text = self._get_status_text(invoice_dto.delivery_status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 5, status_item)

            # Actions button
            action_btn = self._create_operations_button(row)
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

    # --- Internal Signal Handlers and UI Helpers ---
    def _create_operations_button(self, row: int) -> QPushButton:
        """
        Creates the '...' button. When clicked, it emits a signal
        with the invoice number and the button's global position.
        """
        button = QPushButton("⋮", self)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setProperty("row", row)  # Store the row number in the button

        def on_button_clicked():
            # Retrieve the row and find the invoice number from our cache
            clicked_row = button.property("row")
            if 0 <= clicked_row < len(self._table_data_cache):
                invoice_dto, _ = self._table_data_cache[clicked_row]
                # Calculate the position to show the menu
                global_pos = button.mapToGlobal(button.rect().bottomLeft())
                # EMIT THE SIGNAL for the controller
                self.operations_menu_requested.emit(invoice_dto.invoice_number, global_pos)

        button.clicked.connect(on_button_clicked)
        return button

    def _on_context_menu_requested(self, pos: QPoint):
        """Handles the right-click event on the table."""
        index = self.invoices_table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        if 0 <= row < len(self._table_data_cache):
            invoice_dto, _ = self._table_data_cache[row]
            # Convert local position to global for the menu
            global_pos = self.invoices_table.viewport().mapToGlobal(pos)
            # EMIT THE SIGNAL for the controller
            self.operations_menu_requested.emit(invoice_dto.invoice_number, global_pos)

    def _on_invoice_double_clicked(self, row: int, column: int):
        """Handles invoice table double click."""
        if 0 <= row < len(self._table_data_cache):
            invoice_dto, _ = self._table_data_cache[row]
            QApplication.clipboard().setText(str(invoice_dto.invoice_number))
            self.invoice_selected.emit(invoice_dto.invoice_number)
            show_toast(self, "✅ شماره فاکتور کپی شد")
