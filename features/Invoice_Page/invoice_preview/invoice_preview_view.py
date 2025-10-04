# features/Invoice_Page/invoice_preview/invoice_preview_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QSizePolicy, QScrollArea, QSpacerItem, QAbstractItemView, QGridLayout,
                               QToolButton, QMenu)
from PySide6.QtGui import QFont, QIcon, QPixmap, QAction
from PySide6.QtCore import Qt, QSize, Signal
from features.Invoice_Page.invoice_preview.invoice_preview_models import Invoice, PreviewItem
from typing import List
from features.Invoice_Page.invoice_preview.invoice_preview_assets import (PRINT_ICON_PATH, PDF_ICON_PATH,
                                                                          PNG_ICON_PATH, SHARE_ICON_PATH,
                                                                          SETTINGS_ICON_PATH)
from shared import to_persian_number

# --- Constants for Styling ---
FONT_FAMILY = "IRANSans"
A4_WIDTH_PX = 794
A4_HEIGHT_PX = 1123
PRIMARY_BACKGROUND_COLOR = "#F5F5F5"
INVOICE_BORDER_COLOR = "#D0D0D0"
HEADER_COLOR = "#FAFAFA"
SECTION_SEPARATOR_COLOR = "#EAEAEA"


def create_styled_label(text="", font_size=10, bold=False, alignment=Qt.AlignmentFlag.AlignRight, parent=None):
    label = QLabel(text, parent)
    font = QFont(FONT_FAMILY)
    font.setPointSize(font_size)
    font.setBold(bold)
    label.setFont(font)
    label.setAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
    return label


class InvoicePreviewWidget(QFrame):
    """A widget that displays the invoice content, with corrected layout."""

    def __init__(self):
        super().__init__()
        self.setObjectName("InvoicePreviewWidget")
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setFixedSize(A4_WIDTH_PX, A4_HEIGHT_PX)
        self.setStyleSheet(f"""
            #InvoicePreviewWidget {{
                background-color: white; border: 1px solid {INVOICE_BORDER_COLOR};
            }}
            #InvoicePreviewWidget * {{ background-color: transparent; border: none; }}
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(0)

        # --- Final Layout Structure ---
        self._create_header()

        self.main_layout.addSpacerItem(QSpacerItem(
            20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        self.main_layout.addWidget(self._create_section_separator())
        self.main_layout.addSpacerItem(QSpacerItem(
            20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        self._create_customer_info()
        self.main_layout.addSpacerItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self._create_table_container()
        self.main_layout.addSpacerItem(QSpacerItem(
            20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self._create_summary_frame()
        self._create_page_footer()

    def _create_header(self):
        self.header_frame = QFrame(self)
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Invoice Info
        invoice_info_layout = QVBoxLayout()
        self.invoice_number_label = create_styled_label(font_size=10, alignment=Qt.AlignmentFlag.AlignLeft)
        self.issuer_label = create_styled_label(font_size=8, alignment=Qt.AlignmentFlag.AlignLeft)
        self.dates_label = create_styled_label(font_size=9, alignment=Qt.AlignmentFlag.AlignLeft)
        invoice_info_layout.addWidget(self.invoice_number_label)
        invoice_info_layout.addWidget(self.issuer_label)
        invoice_info_layout.addWidget(self.dates_label)
        invoice_info_layout.addStretch()

        # Center: Logo
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        self.logo_label.setScaledContents(True)

        # Right: Office Info
        office_layout = QVBoxLayout()
        self.office_name_label = create_styled_label(font_size=16, bold=True)
        self.office_details_label = create_styled_label(font_size=9, alignment=Qt.AlignmentFlag.AlignRight)
        self.office_contact_label = create_styled_label(font_size=9, alignment=Qt.AlignmentFlag.AlignRight)
        office_layout.addWidget(self.office_name_label)
        office_layout.addWidget(self.office_details_label)
        office_layout.addWidget(self.office_contact_label)
        office_layout.addStretch()

        header_layout.addLayout(invoice_info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.logo_label)
        header_layout.addStretch()
        header_layout.addLayout(office_layout)

        self.main_layout.addWidget(self.header_frame)
        self.main_layout.addWidget(self._create_separator())

    def _create_customer_info(self):
        self.customer_frame = QFrame(self)

        grid_layout = QGridLayout(self.customer_frame)
        grid_layout.setContentsMargins(0, 5, 0, 5)
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(5)

        # Create widgets
        self.language_label = create_styled_label(font_size=10, bold=True, alignment=Qt.AlignmentFlag.AlignLeft)
        self.customer_name_label = create_styled_label(font_size=11, bold=True)
        self.customer_address_label = create_styled_label(font_size=9, alignment=Qt.AlignmentFlag.AlignLeft)
        self.customer_details_label = create_styled_label(font_size=10)

        # Add widgets to the grid
        # Row 0
        grid_layout.addWidget(self.language_label, 0, 0)  # Row 0, Col 0
        grid_layout.addWidget(self.customer_name_label, 0, 2)  # Row 0, Col 2
        # Row 1
        grid_layout.addWidget(self.customer_address_label, 1, 0)  # Row 1, Col 0
        grid_layout.addWidget(self.customer_details_label, 1, 2)  # Row 1, Col 2

        # Add a stretch factor to the middle column to push content to the sides
        grid_layout.setColumnStretch(1, 1)

        self.main_layout.addWidget(self.customer_frame)

    def _create_table_container(self):
        """
        This method now ONLY creates the table and its container.
        The totals have been moved out.
        """
        self.table_container = QFrame()
        table_layout = QVBoxLayout(self.table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(5)

        self.items_table = QTableWidget()
        self.items_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.setColumnCount(6)
        headers = ["شرح خدمات", "نوع", "تعداد", "مهر دادگستری", "مهر خارجه", "مبلغ کل"]
        self.items_table.setHorizontalHeaderLabels(headers)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.items_table.verticalHeader().setVisible(True)
        self.items_table.verticalHeader().setFixedWidth(40)
        self.items_table.verticalHeader().setFont(QFont(FONT_FAMILY, 10))
        self.items_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.items_table.setMaximumHeight(900)

        self.items_table.setStyleSheet(f"""
                    QHeaderView::section {{
                        background-color: {HEADER_COLOR}; padding: 4px; border: none;
                        border-bottom: 1px solid {INVOICE_BORDER_COLOR}; font-family: '{FONT_FAMILY}'; font-size: 10pt;
                    }}
                    QHeaderView::section:vertical {{ border-right: 1px solid {INVOICE_BORDER_COLOR}; }}
                    QTableWidget {{ gridline-color: #E0E0E0; }}
                """)

        table_layout.addWidget(self.items_table, 1)

        self.main_layout.addWidget(self.table_container, 1)

    def _create_summary_frame(self):
        """
        Final Change: A new, unified frame combining totals, remarks, and signature
        using a single powerful QGridLayout.
        """
        self.summary_frame = QFrame()
        self.summary_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        # The main grid layout for the entire summary section
        summary_layout = QGridLayout(self.summary_frame)
        summary_layout.setContentsMargins(0, 10, 0, 5)
        summary_layout.setHorizontalSpacing(25)

        # --- Create all necessary labels ---
        # Totals Labels
        self.subtotal_label = create_styled_label(font_size=10, bold=True)
        self.emergency_label = create_styled_label(font_size=10)
        self.discount_label = create_styled_label(font_size=10)
        self.advance_label = create_styled_label(font_size=10)
        self.payable_label = create_styled_label(font_size=11, bold=True)

        # NOW, create the rows by pairing STATIC labels with the DYNAMIC ones.
        self.subtotal_row = (create_styled_label(
            "جمع جزء:", 10, alignment=Qt.AlignmentFlag.AlignRight), self.subtotal_label)
        self.emergency_row = (create_styled_label(
            "هزینه فوریت:", 10, alignment=Qt.AlignmentFlag.AlignRight), self.emergency_label)
        self.discount_row = (create_styled_label(
            "تخفیف:", 10, alignment=Qt.AlignmentFlag.AlignRight), self.discount_label)
        self.advance_row = (create_styled_label(
            "پیش پرداخت:", 10, alignment=Qt.AlignmentFlag.AlignRight), self.advance_label)
        self.payable_row = (create_styled_label(
            "مبلغ نهایی:", 11, bold=True, alignment=Qt.AlignmentFlag.AlignRight), self.payable_label)

        # Remarks and Signature Labels
        self.remarks_label = create_styled_label(
            font_size=9,
            alignment=Qt.AlignmentFlag.AlignJustify | Qt.AlignmentFlag.AlignVCenter
        )
        self.remarks_label.setWordWrap(True)
        self.remarks_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.signature_label = create_styled_label(
            "امضاء و مهر دارالترجمه", 10, True, Qt.AlignmentFlag.AlignCenter)

        # --- Populate the Grid ---
        # Column 0 & 1: Totals
        summary_layout.addWidget(self.subtotal_row[0], 0, 1)
        summary_layout.addWidget(self.subtotal_row[1], 0, 0)

        summary_layout.addWidget(self.emergency_row[0], 1, 1)
        summary_layout.addWidget(self.emergency_row[1], 1, 0)

        summary_layout.addWidget(self.discount_row[0], 2, 1)
        summary_layout.addWidget(self.discount_row[1], 2, 0)

        summary_layout.addWidget(self.advance_row[0], 3, 1)
        summary_layout.addWidget(self.advance_row[1], 3, 0)

        summary_layout.addWidget(self.payable_row[0], 4, 1)
        summary_layout.addWidget(self.payable_row[1], 4, 0)

        # Column 2: Spacer for visual separation
        summary_layout.addItem(QSpacerItem(25, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum), 0, 2)

        # Column 3: Remarks spanning all 5 rows
        summary_layout.addWidget(self.remarks_label, 0, 3, 4, 1)

        # Row 5: Signature below everything else, spanning the remarks column
        summary_layout.addWidget(self.signature_label, 5, 3)

        # --- Set Column Stretch Factors ---
        # Let the remarks column take up most of the available space
        summary_layout.setColumnStretch(0, 0)  # Totals labels (fit to content)
        summary_layout.setColumnStretch(1, 1)  # Totals values (take some space)
        summary_layout.setColumnStretch(3, 4)  # Remarks column (take the most space)

        self.main_layout.addWidget(self.summary_frame)

    def _create_page_footer(self):
        """A new, dedicated frame at the absolute bottom for the page number."""
        page_footer_frame = QFrame(self)
        page_footer_layout = QHBoxLayout(page_footer_frame)
        page_footer_layout.setContentsMargins(0, 10, 0, 0)

        self.page_label = create_styled_label("صفحه ۱ از ۱", 9, alignment=Qt.AlignmentFlag.AlignCenter)
        page_footer_layout.addWidget(self.page_label)

        self.main_layout.addWidget(page_footer_frame)

    def _create_section_separator(self):
        """Creates a styled, visually distinct separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"background-color: {SECTION_SEPARATOR_COLOR}; color: {SECTION_SEPARATOR_COLOR};")
        separator.setFixedHeight(1)
        return separator

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"color: {INVOICE_BORDER_COLOR};")
        return separator

    def update_content(self, invoice: Invoice, items_on_page: List[PreviewItem],
                       page_num: int, total_pages: int, settings: dict):

        header_vis = settings.get("header_visibility", {})
        customer_vis = settings.get("customer_visibility", {})
        footer_vis = settings.get("footer_visibility", {})
        pagination_config = settings.get("pagination", {})

        is_first_page = (page_num == 1)
        is_last_page = (page_num == total_pages)

        # --- HEADER VISIBILITY ---
        self.header_frame.setVisible(is_first_page)
        self.customer_frame.setVisible(is_first_page)

        if is_first_page:
            office = invoice.office
            customer = invoice.customer

            self.office_name_label.setText(office.name or '')
            self.invoice_number_label.setText(f"فاکتور شماره: {to_persian_number(invoice.invoice_number)}")
            self.language_label.setText(f"ترجمه از {invoice.source_language or ''} به {invoice.target_language or ''}")

            self.issuer_label.setText(f"صادر کننده: {invoice.username or ''}")

            # Logo
            self.logo_label.setVisible(header_vis.get("show_logo", True))
            if header_vis.get("show_logo", True) and office.logo:
                pixmap = QPixmap()
                pixmap.loadFromData(office.logo)
                self.logo_label.setPixmap(pixmap)
            else:
                self.logo_label.clear()

            # Issuer
            self.issuer_label.setVisible(header_vis.get("show_issuer", True))
            self.issuer_label.setText(f"صادر کننده: {invoice.username}")

            # Office Details
            office_details_parts = []
            if header_vis.get("show_representative", True):
                office_details_parts.append(f"مترجم مسئول: {office.representative or ''}")
            self.office_details_label.setText(" | ".join(office_details_parts))
            self.office_details_label.setVisible(bool(office_details_parts))

            # Office Contact
            contact_parts = []
            if header_vis.get("show_address", True): contact_parts.append(f"آدرس: {office.address or ''}")
            if header_vis.get("show_phone", True): contact_parts.append(
                f"تلفن: {to_persian_number(office.phone or '')}")
            if header_vis.get("show_email", True): contact_parts.append(f"ایمیل: {office.email or ''}")
            if header_vis.get("show_website", True): contact_parts.append(f"وبسایت: {office.website or ''}")
            if header_vis.get("show_telegram", True): contact_parts.append(f"تلگرام: {office.telegram or ''}")
            if header_vis.get("show_whatsapp", True): contact_parts.append(f"واتساپ: {office.whatsapp or ''}")
            self.office_contact_label.setText("\n".join(contact_parts))
            self.office_contact_label.setVisible(bool(contact_parts))

            # DATES
            datetime_format = '%Y/%m/%d - %H:%M'
            self.dates_label.setText(
                f"تاریخ صدور: {to_persian_number(invoice.issue_date.strftime(datetime_format))}\n"
                f"تاریخ تحویل: {to_persian_number(invoice.delivery_date.strftime(datetime_format))}")

            # --- CUSTOMER VISIBILITY ---
            self.customer_name_label.setText(f"مشتری: {customer.name}")

            customer_details_parts = []
            if customer_vis.get("show_national_id", True):
                customer_details_parts.append(f"کد ملی: {to_persian_number(customer.national_id)}")
            if customer_vis.get("show_phone", True):
                customer_details_parts.append(f"تلفن: {to_persian_number(customer.phone)}")
            self.customer_details_label.setText(" | ".join(customer_details_parts))
            self.customer_details_label.setVisible(bool(customer_details_parts))

            self.customer_address_label.setText(f"آدرس: {customer.address}")
            self.customer_address_label.setVisible(customer_vis.get("show_address", True))

        # --- TABLE VISIBILITY (as before) ---
        self.table_container.setVisible(bool(items_on_page))

        self.items_table.setRowCount(len(items_on_page))

        if items_on_page and pagination_config:
            start_row_num = 0
            if not is_first_page:
                first_page_count = pagination_config.get('first_page_max_rows', 24)
                other_page_count = pagination_config.get('other_page_max_rows', 28)
                start_row_num = first_page_count + (page_num - 2) * other_page_count

            vertical_headers = [to_persian_number(i + 1 + start_row_num) for i in range(len(items_on_page))]
            self.items_table.setVerticalHeaderLabels(vertical_headers)

        for row, item in enumerate(items_on_page):
            columns = [item.name, item.type, to_persian_number(item.quantity), item.judiciary_seal,
                       item.foreign_affairs_seal, to_persian_number(f"{item.total_price:,.0f}")]
            for col, col_text in enumerate(columns):
                cell = QTableWidgetItem(col_text)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.items_table.setItem(row, col, cell)

        # --- FOOTER VISIBILITY ---
        self.summary_frame.setVisible(is_last_page)
        if is_last_page:

            self.subtotal_label.setText(f"{to_persian_number(f'{invoice.total_amount:,.0f}')} ریال")
            self.discount_label.setText(f"{to_persian_number(f'{invoice.discount_amount:,.0f}')} ریال")
            self.emergency_label.setText(f"{to_persian_number(f'{invoice.emergency_cost:,.0f}')} ریال")
            self.advance_label.setText(f"{to_persian_number(f'{invoice.advance_payment:,.0f}')} ریال")
            self.payable_label.setText(f"{to_persian_number(f'{invoice.payable_amount:,.0f}')} ریال")

            # Show/hide each row in the totals grid
            for widget in self.subtotal_row: widget.setVisible(footer_vis.get("show_subtotal", True))
            for widget in self.discount_row: widget.setVisible(footer_vis.get("show_discount", True))
            for widget in self.emergency_row: widget.setVisible(footer_vis.get("show_emergency_cost", True))
            for widget in self.advance_row: widget.setVisible(footer_vis.get("show_advance_payment", True))

            # Remarks and Signature
            self.remarks_label.setText(f"توضیحات: {invoice.remarks}")
            self.remarks_label.setVisible(footer_vis.get("show_remarks", True))
            self.signature_label.setVisible(footer_vis.get("show_signature", True))

        # Page Number
        self.page_label.setText(f"صفحه {to_persian_number(page_num)} از {to_persian_number(total_pages)}")
        self.page_label.setVisible(footer_vis.get("show_page_number", True))


class ActionPanel(QWidget):
    """A side panel with action buttons for the invoice, now loading from files."""

    def __init__(self):
        super().__init__()
        self.setFixedWidth(120)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.print_button = self._create_tool_button("چاپ", PRINT_ICON_PATH)
        self.save_pdf_button = self._create_tool_button("ذخیره PDF", PDF_ICON_PATH)
        self.save_png_button = self._create_tool_button("ذخیره PNG", PNG_ICON_PATH)
        self.share_button = self._create_tool_button("اشتراک گذاری", SHARE_ICON_PATH)
        self.settings_button = self._create_tool_button("تنظیمات", SETTINGS_ICON_PATH)

        layout.addWidget(self.print_button)
        layout.addWidget(self.save_pdf_button)
        layout.addWidget(self.save_png_button)
        layout.addWidget(self.share_button)
        layout.addStretch()
        layout.addWidget(self.settings_button)

    def _create_tool_button(self, text: str, icon_path: str) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setFixedSize(90, 80)
        button.setIconSize(QSize(32, 32))
        button.setFont(QFont(FONT_FAMILY, 10))
        button.setIcon(QIcon(str(icon_path)))
        button.setStyleSheet("""...""")  # Stylesheet remains the same
        return button


class ControlPanel(QWidget):
    """A panel for navigating between invoice pages with improved styling."""

    save_pdf_requested = Signal()
    save_png_requested = Signal()
    print_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(50)

        self.finish_button = self._create_button("پایان و فاکتور جدید")

        self.prev_button = self._create_button("<< صفحه قبل")

        self.issue_button = self._create_button("✔ صدور فاکتور", is_primary=True)

        self.next_button = self._create_button("صفحه بعد >>")

        self.settings_button = self._create_button("تنظیمات")

        self.export_button = self._create_button("خروجی")
        self.export_menu = QMenu(self)
        self._setup_export_menu()
        self.export_button.setMenu(self.export_menu)
        self.export_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        layout.addWidget(self.finish_button)
        layout.addStretch()
        layout.addWidget(self.prev_button)
        layout.addWidget(self.issue_button)
        layout.addWidget(self.next_button)
        layout.addStretch()
        layout.addWidget(self.export_button)
        layout.addWidget(self.settings_button)

    def _create_button(self, text, is_primary=False) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setFont(QFont("IRANSans", 10))
        button.setFixedHeight(35)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        if is_primary:
            button.setObjectName("PrimaryButton")
        return button

    def _setup_export_menu(self):
        # Create QActions which can have icons and signals
        pdf_action = QAction(QIcon(str(PDF_ICON_PATH)), "ذخیره به صورت PDF", self)
        png_action = QAction(QIcon(str(PNG_ICON_PATH)), "ذخیره به صورت PNG", self)
        print_action = QAction(QIcon(str(PRINT_ICON_PATH)), "چاپ فاکتور", self)

        # Connect the action's trigger to the panel's signals
        pdf_action.triggered.connect(self.save_pdf_requested.emit)
        png_action.triggered.connect(self.save_png_requested.emit)
        print_action.triggered.connect(self.print_requested.emit)

        # Add actions to the menu
        self.export_menu.addAction(pdf_action)
        self.export_menu.addAction(png_action)
        self.export_menu.addSeparator()
        self.export_menu.addAction(print_action)


class MainInvoicePreviewWidget(QWidget):
    """The main application window that orchestrates all UI components."""
    print_clicked = Signal()
    save_pdf_clicked = Signal()
    save_png_clicked = Signal()
    next_page_clicked = Signal()
    prev_page_clicked = Signal()
    issue_clicked = Signal()
    settings_clicked = Signal()
    finish_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("پیش نمایش فاکتور")
        self.setStyleSheet(f"background-color: {PRIMARY_BACKGROUND_COLOR};")

        main_layout = QVBoxLayout(self)  # Changed to QVBoxLayout
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Scroll area for the A4-sized preview
        self.scroll_area = QScrollArea()
        self.invoice_preview = InvoicePreviewWidget()
        self.scroll_area.setWidget(self.invoice_preview)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # --- Use the new consolidated control panel ---
        self.control_panel = ControlPanel()

        main_layout.addWidget(self.scroll_area)  # Takes up most space
        main_layout.addWidget(self.control_panel, alignment=Qt.AlignmentFlag.AlignBottom)

        self._connect_signals()

    def _connect_signals(self):
        """Connect signals from the new control panel to this widget's public signals."""
        # Navigation
        self.control_panel.prev_button.clicked.connect(self.prev_page_clicked.emit)
        self.control_panel.next_button.clicked.connect(self.next_page_clicked.emit)

        # Core Actions
        self.control_panel.issue_button.clicked.connect(self.issue_clicked.emit)
        self.control_panel.settings_button.clicked.connect(self.settings_clicked.emit)

        # Export Menu Actions
        self.control_panel.save_pdf_requested.connect(self.save_pdf_clicked.emit)
        self.control_panel.save_png_requested.connect(self.save_png_clicked.emit)
        self.control_panel.print_requested.connect(self.print_clicked.emit)

        # Workflow Action
        self.control_panel.finish_button.clicked.connect(self.finish_clicked.emit)

    def update_view(self, invoice, items_on_page, current_page, total_pages, settings: dict, is_issued=False):
        """Public slot to refresh the entire display."""
        self.invoice_preview.update_content(
            invoice=invoice, items_on_page=items_on_page, page_num=current_page, total_pages=total_pages,
            settings=settings
        )
        # Update button states in the new control panel
        self.control_panel.prev_button.setEnabled(current_page > 1)
        self.control_panel.next_button.setEnabled(current_page < total_pages)
        self.control_panel.issue_button.setEnabled(not is_issued)
        # Export and print options are usually enabled if an invoice exists
        can_export = invoice is not None
        self.control_panel.export_button.setEnabled(can_export)

    def get_invoice_widget_for_render(self) -> QWidget:
        """Returns the widget to be rendered for saving/printing."""
        return self.invoice_preview
