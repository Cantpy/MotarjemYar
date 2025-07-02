from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QTableWidgetItem, QMessageBox
from PySide6.QtGui import QKeyEvent
from modules.helper_functions import (return_resource, to_persian_number, show_error_message_box)
from modules.InvoicePage.helper_function import get_fixed_price_by_label
import sqlite3
from collections import namedtuple


documents_database = return_resource('databases', 'documents.db')
prince_window_styles = return_resource("styles", "price_window.qss")


# Define a named tuple for storing cumulative invoice data
InvoiceSummary = namedtuple('InvoiceSummary', [
    'total_official_docs_count',
    'total_unofficial_docs_count',
    'total_pages_count',
    'total_judiciary_count',
    'total_foreign_affairs_count',
    'total_additional_doc_count',
    'total_translation_price'
])


class PriceWindow(QDialog):
    """Dialog window for managing document pricing and adding items to invoice."""

    def __init__(self, parent=None, document="", target_row_index=None):
        super().__init__(parent)

        from qt_designer_ui.price_window_dialog import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Store references
        self.parent_invoice_page = parent
        self.document = document
        self.row_index = target_row_index

        # Load pricing configuration
        self._load_pricing_config()

        # Initialize UI
        self._setup_ui()

    def _load_pricing_config(self):
        """Load pricing configuration from settings."""
        self.page_price = get_fixed_price_by_label("page_price_text")
        self.additional_issue_price = get_fixed_price_by_label("additional_issue_text")
        self.judiciary_seal_price = get_fixed_price_by_label("judiciary_price_text")
        self.office_price = get_fixed_price_by_label("office_price_text")

        self.row_count = self.parent_invoice_page.ui.tableWidget.rowCount()
        self.translation_price = self._calculate_translation_price()

    def _setup_ui(self):
        """Initialize UI components and connections."""
        self._setup_default_values()
        self._connect_signals()
        self._handle_dynamic_prices()

    def _setup_default_values(self):
        """Set default values for UI components."""
        self.ui.document_count_spinBox.setValue(1)
        self.ui.page_count_spinBox.setValue(1)
        self.ui.additional_issue_spinBox.setValue(0)

        self.ui.judiciary_price_label.setText("۰ تومان")
        self.ui.office_price_label.setText(f"{to_persian_number(self.office_price)} تومان")
        self.ui.translation_price_label.setText(f"{to_persian_number(self.translation_price)} تومان")

        self._update_page_price_label()
        self._update_total_price_label()
        self.ui.second_frame.hide()

    def _connect_signals(self):
        """Connect all UI signals to their respective handlers."""
        # Document count changes
        self.ui.document_count_spinBox.textChanged.connect(self._update_office_price)
        self.ui.document_count_spinBox.textChanged.connect(self._update_translation_price)
        self.ui.document_count_spinBox.textChanged.connect(self._update_judiciary_label)
        self.ui.document_count_spinBox.textChanged.connect(self._update_page_price_label)
        self.ui.document_count_spinBox.textChanged.connect(self._update_total_price_label)
        self.ui.document_count_spinBox.valueChanged.connect(self._validate_document)

        # Page count changes
        self.ui.page_count_spinBox.textChanged.connect(self._update_page_price_label)
        self.ui.page_count_spinBox.textChanged.connect(self._update_total_price_label)
        self.ui.page_count_spinBox.valueChanged.connect(self._validate_document)

        # Additional issue changes
        self.ui.additional_issue_spinBox.textChanged.connect(self._update_additional_issue_label)
        self.ui.additional_issue_spinBox.textChanged.connect(self._update_total_price_label)

        # Checkbox changes
        self.ui.judiciary_checkbox.stateChanged.connect(self._update_judiciary_label)
        self.ui.judiciary_checkbox.stateChanged.connect(self._update_total_price_label)
        self.ui.official_checkBox.toggled.connect(self._update_office_price)
        self.ui.unofficial_checkBox.toggled.connect(self._update_office_price)

        # Dynamic price changes
        self.ui.dynamic_price_1_spinBox.textChanged.connect(self._update_translation_price)
        self.ui.dynamic_price_1_spinBox.textChanged.connect(self._update_total_price_label)
        self.ui.dynamic_price_2_spinBox.textChanged.connect(self._update_translation_price)
        self.ui.dynamic_price_2_spinBox.textChanged.connect(self._update_total_price_label)

        # Button clicks
        self.ui.cancel_pbutton.clicked.connect(self.reject)
        self.ui.accept_pbutton.clicked.connect(self.add_document_to_invoice)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.add_document_to_invoice()
        else:
            super().keyPressEvent(event)

    def _validate_document(self):
        """Validate document and page counts are not zero."""
        if self.ui.document_count_spinBox.value() == 0:
            QMessageBox.warning(self, "خطای ورودی", "تعداد اسناد نمی‌تواند ۰ باشد")
            self.ui.document_count_spinBox.setValue(1)
            return False

        if self.ui.page_count_spinBox.value() == 0:
            QMessageBox.warning(self, "خطای ورودی", "تعداد صفحات سند نمی‌تواند ۰ باشد")
            self.ui.page_count_spinBox.setValue(1)
            return False

        return True

    def _get_safe_int_value(self, widget, default="1"):
        """Safely get integer value from widget text."""
        try:
            text = widget.text().strip()
            return int(text) if text else int(default)
        except (ValueError, AttributeError):
            return int(default)

    def _update_office_price(self, checked=None):
        """Update office price based on official/unofficial selection."""
        document_count = self._get_safe_int_value(self.ui.document_count_spinBox)

        if self.sender() == self.ui.official_checkBox and checked:
            self.ui.unofficial_checkBox.setChecked(False)
            self.office_price = get_fixed_price_by_label("office_price_text")
        elif self.sender() == self.ui.unofficial_checkBox and checked:
            self.ui.official_checkBox.setChecked(False)
            self.office_price = 0

        total_office_price = self.office_price * document_count
        self.ui.office_price_label.setText(f"{to_persian_number(total_office_price)} تومان")

    def _calculate_translation_price(self):
        """Calculate translation price based on current inputs."""
        try:
            document_count = self._get_safe_int_value(self.ui.document_count_spinBox)
            base_price = self.parent_invoice_page.calculate_base_price(self.document)
            formatted_base_price = base_price.replace(",", "")

            price_1 = self.parent_invoice_page.get_dynamic_price_1(self.document) or 0
            price_2 = self.parent_invoice_page.get_dynamic_price_2(self.document) or 0

            price_1_count = self._get_safe_int_value(self.ui.dynamic_price_1_spinBox, "0")
            price_2_count = self._get_safe_int_value(self.ui.dynamic_price_2_spinBox, "0")

            translation_price = (
                    (int(formatted_base_price) + (price_1 * price_1_count) + (price_2 * price_2_count)) * document_count
            )

            return translation_price

        except (sqlite3.Error, AttributeError):
            return 0

    def _update_translation_price(self):
        """Update translation price label."""
        translation_price = self._calculate_translation_price()
        price_text = to_persian_number(translation_price) if translation_price > 0 else "۰"
        self.ui.translation_price_label.setText(f"{price_text} تومان")

    def _update_page_price_label(self):
        """Update page price label."""
        try:
            document_count = self._get_safe_int_value(self.ui.document_count_spinBox)
            page_count = self._get_safe_int_value(self.ui.page_count_spinBox)

            total_page_price = (page_count * self.page_price) * document_count
            price_text = to_persian_number(total_page_price)
            self.ui.page_price_label.setText(f"{price_text} تومان")

        except (ValueError, AttributeError):
            self.ui.page_price_label.setText("۰ تومان")

    def _update_additional_issue_label(self):
        """Update additional issue price label."""
        try:
            additional_count = self._get_safe_int_value(self.ui.additional_issue_spinBox, "0")
            total_additional_price = additional_count * self.additional_issue_price
            price_text = to_persian_number(total_additional_price)
            self.ui.additional_issue_price_label.setText(f"{price_text} تومان")

        except (ValueError, AttributeError):
            self.ui.additional_issue_price_label.setText("۰ تومان")

    def _update_judiciary_label(self):
        """Update judiciary seal price label."""
        try:
            if self.ui.judiciary_checkbox.isChecked():
                document_count = self._get_safe_int_value(self.ui.document_count_spinBox)
                total_judiciary_price = self.judiciary_seal_price * document_count
                price_text = to_persian_number(total_judiciary_price)
                self.ui.judiciary_price_label.setText(f"{price_text} تومان")
            else:
                self.ui.judiciary_price_label.setText("۰ تومان")

        except (ValueError, AttributeError):
            self.ui.judiciary_price_label.setText("۰ تومان")

    def _extract_price_from_label(self, label):
        """Extract numeric price from label text."""
        try:
            price_text = label.text().split()[0]
            # Remove Persian number formatting
            return int(price_text.replace(',', ''))
        except (ValueError, AttributeError, IndexError):
            return 0

    def _update_total_price_label(self):
        """Calculate and update total price label."""
        try:
            page_price = self._extract_price_from_label(self.ui.page_price_label)
            additional_price = self._extract_price_from_label(self.ui.additional_issue_price_label)
            judiciary_price = self._extract_price_from_label(self.ui.judiciary_price_label)
            translation_price = self._extract_price_from_label(self.ui.translation_price_label)

            document_count = self._get_safe_int_value(self.ui.document_count_spinBox)
            office_cost = self.office_price * document_count

            total_price = (
                    page_price + judiciary_price + translation_price +
                    additional_price + office_cost
            )

            formatted_price = f"{total_price:,}"
            self.ui.total_price_label.setText(f"{to_persian_number(formatted_price)} تومان")

            return total_price

        except (ValueError, AttributeError):
            self.ui.total_price_label.setText("۰ تومان")
            return 0

    def _handle_dynamic_prices(self):
        """Configure dynamic pricing UI based on dynamic price columns in Services table."""
        try:
            with sqlite3.connect(documents_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, dynamic_price_name_1, dynamic_price_name_2
                    FROM Services
                """)
                services = cursor.fetchall()

            for name, price_name_1, price_name_2 in services:
                if self.document != name:
                    continue

                # Helper function to transform label
                def transform_label(label):
                    if label and label.startswith("هر"):
                        return label.replace("هر", "تعداد", 1)
                    return label or ""

                transformed_1 = transform_label(price_name_1)
                transformed_2 = transform_label(price_name_2)

                if price_name_1 and price_name_2:
                    self._show_double_dynamic_price(transformed_1, transformed_2)
                    return
                elif price_name_1 or price_name_2:
                    self._show_single_dynamic_price(transformed_1 or transformed_2)
                    return
                else:
                    base_price = self.parent_invoice_page.calculate_base_price(self.document)
                    self.ui.translation_price_label.setText(f"{base_price} تومان")
                    return

        except sqlite3.Error as e:
            show_error_message_box(
                self,
                "خطا",
                f"خطا در بررسی نوع قیمت متغیر برای سند:\n{str(e)}"
            )

    def _show_single_dynamic_price(self, label_text):
        """Show UI for single dynamic price."""
        self.ui.second_frame.show()
        self.ui.price_2_frame.hide()
        self.ui.dynamic_price_1_label.setText(label_text)
        self.ui.dynamic_price_1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _show_double_dynamic_price(self, label_1, label_2):
        """Show UI for double dynamic price."""
        self.ui.second_frame.show()
        self.ui.dynamic_price_1_label.setText(label_1)
        self.ui.dynamic_price2_label.setText(label_2)
        self.ui.dynamic_price_1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.dynamic_price2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _generate_remarks(self):
        """Generate remarks text based on dynamic pricing columns from the Services table."""
        document_name = self.document

        try:
            with sqlite3.connect(documents_database) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dynamic_price_name_1, dynamic_price_name_2
                    FROM Services
                    WHERE name = ?
                """, (document_name,))
                result = cursor.fetchone()

            if not result:
                return ""

            price_name_1, price_name_2 = result

            # Helper function to transform labels
            def transform_label(label):
                if label and label.startswith("هر"):
                    return label.replace("هر", "", 1)
                return label or ""

            title_1 = transform_label(price_name_1)
            title_2 = transform_label(price_name_2)

            count_1 = self._get_safe_int_value(self.ui.dynamic_price_1_spinBox, "0")
            count_2 = self._get_safe_int_value(self.ui.dynamic_price_2_spinBox, "0")

            if price_name_1 and price_name_2:
                if count_1 > 0 and count_2 >= 0:
                    return f"{to_persian_number(count_1)} {title_1} و {to_persian_number(count_2)} {title_2}"

            elif price_name_1 or price_name_2:
                active_title = title_1 if price_name_1 else title_2
                active_count = count_1 if price_name_1 else count_2

                if active_count > 0:
                    return f"{to_persian_number(active_count)} {active_title}"

            return ""

        except sqlite3.Error as e:
            show_error_message_box(
                self,
                "خطا",
                f"خطا در تولید توضیحات سند:\n{str(e)}"
            )
            return ""

    def _create_table_item(self, text: str, editable: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Center-align text
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _update_cumulative_data(self):
        """Update cumulative data in parent after adding document to invoice."""
        # Get current values from UI
        document_count = self._get_safe_int_value(self.ui.document_count_spinBox)
        page_count = self._get_safe_int_value(self.ui.page_count_spinBox)
        additional_count = self._get_safe_int_value(self.ui.additional_issue_spinBox, "0")
        translation_price = self._calculate_translation_price()

        # Get current cumulative data or initialize with zeros
        current_data = getattr(self.parent_invoice_page, 'invoice_summary', None)
        if current_data is None:
            # Initialize with zeros
            totals = {
                'total_official_docs_count': 0,
                'total_unofficial_docs_count': 0,
                'total_pages_count': 0,
                'total_judiciary_count': 0,
                'total_foreign_affairs_count': 0,
                'total_additional_doc_count': 0,
                'total_translation_price': 0
            }
        else:
            # Convert named tuple to dict for modification
            totals = current_data._asdict()

        # Update totals based on current document
        if self.ui.official_checkBox.isChecked():
            totals['total_official_docs_count'] += document_count

        if self.ui.unofficial_checkBox.isChecked():
            totals['total_unofficial_docs_count'] += document_count

        totals['total_pages_count'] += page_count * document_count

        if self.ui.judiciary_checkbox.isChecked():
            totals['total_judiciary_count'] += document_count

        if self.ui.foreign_affairs_checkbox.isChecked():
            totals['total_foreign_affairs_count'] += document_count

        totals['total_additional_doc_count'] += additional_count
        totals['total_translation_price'] += translation_price

        # Create new immutable tuple and store in parent
        self.parent_invoice_page.invoice_summary = InvoiceSummary(**totals)

    def add_document_to_invoice(self):
        """Add the configured document to the invoice table."""
        if not self._validate_document():
            return

        # Determine row index
        if self.row_index is None:
            row_index = self.parent_invoice_page.ui.tableWidget.rowCount()
            self.parent_invoice_page.ui.tableWidget.insertRow(row_index)
        else:
            row_index = self.row_index

        table = self.parent_invoice_page.ui.tableWidget
        total_price = self._update_total_price_label()

        # Populate table columns
        table.setItem(row_index, 0, self._create_table_item(self.document))

        official_text = "رسمی" if self.ui.official_checkBox.isChecked() else "غیررسمی"
        table.setItem(row_index, 1, self._create_table_item(official_text))

        table.setItem(row_index, 2, self._create_table_item(self.ui.document_count_spinBox.text()))

        judiciary_text = "✔" if self.ui.judiciary_checkbox.isChecked() else "-"
        table.setItem(row_index, 3, self._create_table_item(judiciary_text))

        foreign_affairs_text = "✔" if self.ui.foreign_affairs_checkbox.isChecked() else "-"
        table.setItem(row_index, 4, self._create_table_item(foreign_affairs_text))

        # Handle price column editability
        is_special_service = self.document in ("سایر خدمات", "امور خارجه")
        table.setItem(row_index, 5, self._create_table_item(f"{total_price:,}", editable=is_special_service))

        # Add remarks
        remarks_text = self._generate_remarks()
        table.setItem(row_index, 6, self._create_table_item(remarks_text))

        # Update cumulative data BEFORE updating parent interface
        self._update_cumulative_data()

        # Update parent interface
        self.parent_invoice_page.update_row_numbers()
        self.parent_invoice_page.clear_document_fields()

        self.accept()
