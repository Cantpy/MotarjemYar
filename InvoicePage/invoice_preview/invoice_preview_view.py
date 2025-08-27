# view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QSizePolicy, QScrollArea, QSpacerItem, QAbstractItemView, QGridLayout,
                               QToolButton)
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtCore import Qt, QSize
from InvoicePage.invoice_preview.invoice_preview_models import Invoice, InvoiceItem
from typing import List, Dict
from InvoicePage.invoice_preview.invoice_preview_assets import (PRINT_ICON_PATH, PDF_ICON_PATH, PNG_ICON_PATH,
                                                                SHARE_ICON_PATH)

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
        self.main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
        self.main_layout.addWidget(self._create_section_separator())
        self.main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))
        self._create_customer_info()
        self.main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self._create_table_container()

        # The expanding spacer is key to pushing the summary to the bottom
        self.main_layout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Create the new, combined summary frame
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
        # Use QGridLayout for compact and precise placement
        grid_layout = QGridLayout(self.customer_frame)
        grid_layout.setContentsMargins(0, 5, 0, 5)
        grid_layout.setHorizontalSpacing(20)  # Space between columns
        grid_layout.setVerticalSpacing(5)  # Compact vertical space

        # Create widgets
        self.language_label = create_styled_label(font_size=10, bold=True, alignment=Qt.AlignLeft)
        self.customer_name_label = create_styled_label(font_size=11, bold=True)
        self.customer_address_label = create_styled_label(font_size=9, alignment=Qt.AlignLeft)
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
        self.items_table.setLayoutDirection(Qt.RightToLeft)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
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
        self.summary_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # The main grid layout for the entire summary section
        summary_layout = QGridLayout(self.summary_frame)
        summary_layout.setContentsMargins(0, 10, 0, 5)
        summary_layout.setHorizontalSpacing(25)

        # --- Create all necessary labels ---
        # Totals Labels
        self.subtotal_label = create_styled_label(font_size=10, bold=True)
        self.discount_label = create_styled_label(font_size=10)
        self.emergency_label = create_styled_label(font_size=10)
        self.advance_label = create_styled_label(font_size=10)
        self.payable_label = create_styled_label(font_size=11, bold=True)

        # Remarks and Signature Labels
        self.remarks_label = create_styled_label(
            font_size=9,
            alignment=Qt.AlignJustify | Qt.AlignVCenter
        )
        self.remarks_label.setWordWrap(True)
        self.remarks_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.signature_label = create_styled_label("امضاء و مهر دارالترجمه", 10, True, Qt.AlignCenter)

        # --- Populate the Grid ---
        # Column 0 & 1: Totals
        summary_layout.addWidget(create_styled_label("جمع جزء:", 10, alignment=Qt.AlignRight), 0, 1)
        summary_layout.addWidget(self.subtotal_label, 0, 0)
        summary_layout.addWidget(create_styled_label("تخفیف:", 10, alignment=Qt.AlignRight), 1, 1)
        summary_layout.addWidget(self.discount_label, 1, 0)
        summary_layout.addWidget(create_styled_label("هزینه فوریت:", 10, alignment=Qt.AlignRight), 2, 1)
        summary_layout.addWidget(self.emergency_label, 2, 0)
        summary_layout.addWidget(create_styled_label("پیش پرداخت:", 10, alignment=Qt.AlignRight), 3, 1)
        summary_layout.addWidget(self.advance_label, 3, 0)
        summary_layout.addWidget(create_styled_label("مبلغ نهایی:", 11, bold=True, alignment=Qt.AlignRight), 4, 1)
        summary_layout.addWidget(self.payable_label, 4, 0)

        # Column 2: Spacer for visual separation
        summary_layout.addItem(QSpacerItem(25, 10, QSizePolicy.Fixed, QSizePolicy.Minimum), 0, 2)

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

        self.page_label = create_styled_label("صفحه ۱ از ۱", 9, alignment=Qt.AlignCenter)
        page_footer_layout.addWidget(self.page_label)

        self.main_layout.addWidget(page_footer_frame)

    def _create_section_separator(self):
        """Creates a styled, visually distinct separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {SECTION_SEPARATOR_COLOR}; color: {SECTION_SEPARATOR_COLOR};")
        separator.setFixedHeight(1)
        return separator

    def _create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"color: {INVOICE_BORDER_COLOR};")
        return separator

    def update_content(self, invoice: Invoice, items_on_page: List[InvoiceItem], page_num: int, total_pages: int,
                       pagination_config: Dict[str, int]):

        is_first_page = (page_num == 1)
        is_last_page = (page_num == total_pages)

        # Show/hide header and customer info on first page only
        self.header_frame.setVisible(is_first_page)
        self.customer_frame.setVisible(is_first_page)

        if is_first_page:
            office = invoice.office
            customer = invoice.customer
            self.office_name_label.setText(office.name)
            self.office_details_label.setText(
                f"شماره ثبت: {to_persian_number(office.reg_no)} | مترجم مسئول: {office.representative}")
            self.office_contact_label.setText(
                f"آدرس: {office.address}\nتلفن: {to_persian_number(office.phone)} | ایمیل: {office.email} | {office.socials}")
            self.logo_label.setPixmap(QPixmap(office.logo_path))
            self.invoice_number_label.setText(f"فاکتور شماره: {to_persian_number(invoice.invoice_number)}")
            self.issuer_label.setText(f"صادر کننده: {invoice.username}")
            self.dates_label.setText(
                f"تاریخ صدور: {to_persian_number(invoice.issue_date.strftime('%Y/%m/%d'))}\nتاریخ تحویل: {to_persian_number(invoice.delivery_date.strftime('%Y/%m/%d'))}")
            self.language_label.setText(f"ترجمه از {invoice.source_language} به {invoice.target_language}")
            self.customer_name_label.setText(f"مشتری: {customer.name}")
            self.customer_details_label.setText(
                f"کد ملی: {to_persian_number(customer.national_id)} | تلفن: {to_persian_number(customer.phone)}")
            self.customer_address_label.setText(f"آدرس: {customer.address}")

        # Visibility _logic for the table container
        if not items_on_page:
            self.table_container.setVisible(False)
        else:
            self.table_container.setVisible(True)

        self.items_table.setRowCount(len(items_on_page))

        # Calculate the starting row number for the current page
        start_row_num = 0
        if not is_first_page:
            # This _logic mirrors get_items_for_page to find the first item's index
            first_page_count = pagination_config['first_page_max_rows']
            other_page_count = pagination_config['other_page_max_rows']

            # The number of items on all pages *before* the current one
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

        self.summary_frame.setVisible(is_last_page)

        if is_last_page:
            # Populate the updated summary section
            self.subtotal_label.setText(f"{to_persian_number(f'{invoice.total_amount:,.0f}')} ریال")
            self.discount_label.setText(f"{to_persian_number(f'{invoice.discount_amount:,.0f}')} ریال")
            self.emergency_label.setText(f"{to_persian_number(f'{invoice.emergency_cost:,.0f}')} ریال")
            self.advance_label.setText(f"{to_persian_number(f'{invoice.advance_payment:,.0f}')} ریال")
            self.payable_label.setText(f"{to_persian_number(f'{invoice.payable_amount:,.0f}')} ریال")
            self.remarks_label.setText(f"توضیحات: {invoice.remarks}")

        # Always update page number
        self.page_label.setText(f"صفحه {to_persian_number(page_num)} از {to_persian_number(total_pages)}")


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

        layout.addWidget(self.print_button)
        layout.addWidget(self.save_pdf_button)
        layout.addWidget(self.save_png_button)
        layout.addWidget(self.share_button)

    def _create_tool_button(self, text: str, icon_path: str) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setFixedSize(90, 80)
        button.setIconSize(QSize(32, 32))
        button.setFont(QFont(FONT_FAMILY, 10))
        button.setIcon(QIcon(icon_path))
        button.setStyleSheet("""...""")  # Stylesheet remains the same
        return button


class PaginationPanel(QWidget):
    """A panel for navigating between invoice pages with improved styling."""

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(50)

        self.prev_button = self._create_nav_button("<< صفحه قبل")
        self.next_button = self._create_nav_button("صفحه بعد >>")

        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)

    def _create_nav_button(self, text):
        button = QToolButton()
        button.setText(text)
        button.setFont(QFont(FONT_FAMILY, 10))
        button.setFixedSize(120, 35)
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid #C0C0C0;
                border-radius: 4px;
                background-color: white;
            }
            QToolButton:disabled {
                background-color: #F0F0F0;
                color: #A0A0A0;
            }
            QToolButton:hover:!disabled {
                background-color: #F0F0F0;
            }
        """)
        return button


class MainInvoiceWindow(QWidget):
    """The main application window that orchestrates all UI components."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("پیش نمایش فاکتور")
        self.setGeometry(100, 100, 1200, 900)
        self.setStyleSheet(f"background-color: {PRIMARY_BACKGROUND_COLOR};")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(10, 10, 10, 10)
        self.scroll_area = QScrollArea()
        self.invoice_preview = InvoicePreviewWidget()

        self.scroll_area.setWidget(self.invoice_preview)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.pagination_panel = PaginationPanel()

        center_layout.addWidget(self.scroll_area)
        center_layout.addWidget(self.pagination_panel)

        self.action_panel = ActionPanel()

        # Order: Central content, then the action panel on the right
        main_layout.addLayout(center_layout, 1)
        main_layout.addWidget(self.action_panel)

    def get_invoice_widget(self) -> QWidget:
        """Returns the widget to be rendered for saving/printing."""
        return self.invoice_preview
