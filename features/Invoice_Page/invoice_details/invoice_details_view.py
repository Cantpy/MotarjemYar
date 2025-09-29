# features/Invoice_Page/invoice_details/invoice_details_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QSpacerItem, QGroupBox, QFormLayout, QGridLayout, QLabel,
    QComboBox, QTextEdit, QPushButton
)
from PySide6.QtCore import Signal, Qt
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails, Language
from shared.utils.persian_tools import to_persian_numbers
from shared.widgets.persian_tools import PlainDoubleSpinBox
from shared.utils.text_utils import amount_to_persian_words


class InvoiceDetailsWidget(QWidget):
    """
    The main widget for displaying and editing invoice details. It includes sections for invoice info,
    customer info, financial details, translation office info, and remarks.
    """
    settings_requested = Signal()
    financial_input_changed = Signal(str, float, str)
    other_input_changed = Signal(dict)

    def __init__(self, settings_manager: "SettingsManager", parent=None):
        super().__init__(parent)
        self.setObjectName("InvoiceDetailsView")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.settings_manager = settings_manager

        self._is_programmatically_updating = False

        self._init_widgets()
        self._setup_ui()
        self._connect_signals()

    def _init_widgets(self):
        """Initialize all widgets."""
        self.settings_button = QPushButton("تنظیمات")

        self.invoice_number_label = QLabel('نامشخص')
        self.total_documents = QLabel("۰")
        self.issue_date_label = QLabel('نامشخص')
        self.user_label = QLabel("نامشخص")
        from shared.widgets.persian_calendar import InvoiceDatePicker
        self.delivery_date_edit = InvoiceDatePicker()
        self.source_language = QComboBox()
        self.target_language = QComboBox()
        self.translation_direction_label = QLabel()

        # Financial group - cost labels
        self.total_before_discount_label = QLabel('۰ تومان')
        self.translation_cost_label = QLabel('۰ تومان')
        self.confirmation_cost_label = QLabel('۰ تومان')
        self.office_affairs_cost_label = QLabel('۰ تومان')
        self.copy_cert_cost_label = QLabel('۰ تومان')

        self.emergency_input = PlainDoubleSpinBox()
        self.emergency_toggle = QPushButton("٪")
        self.emergency_display_label = QLabel()

        self.discount_input = PlainDoubleSpinBox()
        self.discount_toggle = QPushButton("٪")
        self.discount_display_label = QLabel()

        self.advance_input = PlainDoubleSpinBox()
        self.advance_toggle = QPushButton("٪")
        self.advance_display_label = QLabel()

        self.final_amount = QLabel("۰ تومان")

        # Translation office info widgets (labels instead of line edits)
        self.office_name = QLabel("نامشخص")
        self.office_license = QLabel("نامشخص")
        self.office_translator = QLabel("نامشخص")
        self.office_address = QLabel("نامشخص")
        self.office_phone = QLabel("نامشخص")
        self.office_email = QLabel("نامشخص")

        # CustomerModel info widgets
        self.customer_name = QLabel("نامشخص")
        self.customer_phone = QLabel("نامشخص")
        self.customer_national_id = QLabel("نامشخص")
        self.customer_email = QLabel("نامشخص")
        self.customer_address = QLabel("نامشخص")
        self.companions_num = QLabel("۰")

        # Remarks
        self.remarks_text = QTextEdit()

    def _setup_ui(self):
        """Setup the invoice details UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.settings_button)
        layout.addLayout(top_bar_layout)

        # Create main layout with four columns
        main_layout = QHBoxLayout()

        # First column - Invoice details
        self.invoice_group = self._create_invoice_group()

        # Second column - CustomerModel information
        self.customer_group = self._create_customer_group()

        # Third column - Financial details
        self.financial_group = self._create_financial_group()

        # Fourth column - Translation office info
        self.office_group = self._create_office_group()

        main_layout.addWidget(self.invoice_group, stretch=1)
        main_layout.addWidget(self.customer_group, stretch=1)
        main_layout.addWidget(self.financial_group, stretch=1)
        main_layout.addWidget(self.office_group, stretch=1)
        layout.addLayout(main_layout)

        # Remarks section (full width)
        remarks_group = self._create_remarks_group()
        layout.addWidget(remarks_group)

        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Apply styling
        from features.Invoice_Page.invoice_details.invoice_details_qss import INVOICE_DETAILS_QSS
        self.setStyleSheet(INVOICE_DETAILS_QSS)
        self._setup_widgets_properties()

    def _create_invoice_group(self) -> QGroupBox:
        """Create invoice information group."""
        group = QGroupBox("اطلاعات فاکتور")
        form = QFormLayout(group)
        form.setSpacing(12)

        # Set current date/time for receive date
        from shared.utils.date_utils import get_persian_date
        current_jalali_datetime = get_persian_date()
        self.issue_date_label.setText(current_jalali_datetime)

        # Setup language combos
        languages = [lang.value for lang in Language]
        self.source_language.addItems(languages)
        self.target_language.addItems(languages)
        self.source_language.setCurrentText(Language.FARSI.value)
        self.target_language.setCurrentText(Language.ENGLISH.value)

        # Style the labels
        self._style_info_label(self.invoice_number_label)
        self._style_info_label(self.total_documents)
        self._style_info_label(self.issue_date_label)
        self._style_info_label(self.user_label)

        # Update translation direction label
        self._update_translation_direction()

        form.addRow("شماره رسید:", self.invoice_number_label)
        form.addRow("تعداد اسناد:", self.total_documents)
        form.addRow("تاریخ صدور:", self.issue_date_label)
        form.addRow("تاریخ تحویل:", self.delivery_date_edit)
        form.addRow("کاربر:", self.user_label)
        form.addRow("زبان مبدأ:", self.source_language)
        form.addRow("زبان مقصد:", self.target_language)
        form.addRow("", self.translation_direction_label)

        return group

    def apply_settings(self):
        """Applies settings from the manager to the UI (visibility, default text)."""
        # Apply visibility
        visibility = self.settings_manager.get("group_box_visibility")
        self.invoice_group.setVisible(visibility.get("invoice", True))
        self.customer_group.setVisible(visibility.get("customer", True))
        self.financial_group.setVisible(visibility.get("financial", True))
        self.office_group.setVisible(visibility.get("office", True))

        # Apply default remarks only if the field is currently empty
        # if not self.remarks_text.toPlainText().strip():
        default_remarks = self.settings_manager.get("default_remarks")
        self.remarks_text.setPlainText(default_remarks)

    def _create_customer_group(self) -> QGroupBox:
        """Create customer information group."""
        group = QGroupBox("اطلاعات مشتری")
        form = QFormLayout(group)
        form.setSpacing(12)

        # Style customer info labels
        self._style_info_label(self.customer_name)
        self._style_info_label(self.customer_phone)
        self._style_info_label(self.customer_national_id)
        self._style_info_label(self.customer_email)
        self._style_info_label(self.customer_address)
        self._style_info_label(self.companions_num)

        # CustomerModel information section
        form.addRow("نام مشتری:", self.customer_name)
        form.addRow("تلفن مشتری:", self.customer_phone)
        form.addRow("کد ملی:", self.customer_national_id)
        form.addRow("ایمیل مشتری:", self.customer_email)
        form.addRow("آدرس مشتری:", self.customer_address)
        form.addRow("تعداد همراهان:", self.companions_num)

        return group

    def _create_financial_group(self) -> QGroupBox:
        """
        Creates the financial details group with the new input/display design.
        """
        group = QGroupBox("اطلاعات مالی")
        main_v_layout = QVBoxLayout(group)
        main_v_layout.setSpacing(15)

        # --- Summary Section (same as before) ---
        summary_layout = QFormLayout()
        self._style_cost_label(self.total_before_discount_label)
        summary_layout.addRow("<b>جمع کل هزینه‌ها:</b>", self.total_before_discount_label)
        main_v_layout.addLayout(summary_layout)

        # --- Collapsible Details Section (same as before) ---
        from shared.widgets.collapsable_box import CollapsibleBox
        self.details_box = CollapsibleBox("نمایش ریز هزینه‌ها")
        details_layout = QFormLayout()
        details_layout.setContentsMargins(20, 5, 5, 5)  # Indent the details
        details_layout.setHorizontalSpacing(20)
        details_layout.setVerticalSpacing(10)
        details_layout.addRow("هزینه ترجمه:", self.translation_cost_label)
        details_layout.addRow("هزینه تاییدات:", self.confirmation_cost_label)
        details_layout.addRow("امور دفتری:", self.office_affairs_cost_label)
        details_layout.addRow("هزینه کپی برابر اصل:", self.copy_cert_cost_label)

        self.details_box.setContentLayout(details_layout)
        main_v_layout.addWidget(self.details_box)

        # --- 4. REBUILT User Input Section with the new design ---
        input_group = QGroupBox("تنظیمات پرداخت")
        input_group.setStyleSheet("QGroupBox { border: none; margin-top: 0; }")
        input_layout = QGridLayout(input_group)
        input_layout.setColumnStretch(1, 1)  # Give stretch to the input column

        # --- Style the new display labels ---
        for label in [self.emergency_display_label, self.discount_display_label, self.advance_display_label]:
            label.setStyleSheet("color: #2b6cb0; font-size: 10px; padding-right: 5px;")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Setup and style the rows
        self._setup_financial_row(
            input_layout, 0, "فوریت:", self.emergency_input, self.emergency_toggle, self.emergency_display_label
        )
        self._setup_financial_row(
            input_layout, 2, "تخفیف:", self.discount_input, self.discount_toggle, self.discount_display_label
        )
        self._setup_financial_row(
            input_layout, 4, "پیش‌پرداخت:", self.advance_input, self.advance_toggle, self.advance_display_label
        )

        input_layout.setRowStretch(6, 1)  # Spacer

        # Final Amount Row
        final_amount_title_label = QLabel("<b>مبلغ نهایی:</b>")
        self._style_cost_label(self.final_amount)
        input_layout.addWidget(final_amount_title_label, 7, 0)
        input_layout.addWidget(self.final_amount, 7, 1, 1, 2)  # Span 2 columns

        main_v_layout.addWidget(input_group)
        return group

    def _setup_financial_row(self, layout: QGridLayout, row: int, title: str,
                             spinbox: PlainDoubleSpinBox, button: QPushButton, display_label: QLabel):
        """Helper function to create one compact row in the financial grid."""
        layout.addWidget(QLabel(title), row, 0)
        layout.addWidget(spinbox, row, 1)
        layout.addWidget(button, row, 2)
        layout.addWidget(display_label, row + 1, 1, 1, 2)  # Display label on next row, spanning 2 columns

        button.setFixedSize(40, spinbox.sizeHint().height())
        button.setObjectName("modeToggleButton")  # For styling

        display_label.setStyleSheet("color: #2b6cb0; font-size: 10px; padding-right: 5px;")
        display_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _create_office_group(self) -> QGroupBox:
        """Create translation office information group."""
        group = QGroupBox("اطلاعات دارالترجمه")
        form = QFormLayout(group)
        form.setSpacing(12)

        # Style office info labels
        self._style_info_label(self.office_name)
        self._style_info_label(self.office_address)
        self._style_info_label(self.office_phone)
        self._style_info_label(self.office_email)
        self._style_info_label(self.office_license)
        self._style_info_label(self.office_translator)

        form.addRow("نام:", self.office_name)
        form.addRow("شماره ثبت:", self.office_license)
        form.addRow("مترجم مسئول:", self.office_translator)
        form.addRow("آدرس:", self.office_address)
        form.addRow("تلفن:", self.office_phone)
        form.addRow("ایمیل:", self.office_email)

        return group

    def _create_remarks_group(self) -> QGroupBox:
        """Create remarks section."""
        group = QGroupBox("توضیحات فاکتور")
        layout = QVBoxLayout(group)

        self.remarks_text.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.remarks_text.setPlaceholderText("توضیحات و یادداشت‌های اینجا در فاکتور نشان داده می‌شود...")
        self.remarks_text.setMaximumHeight(100)
        layout.addWidget(self.remarks_text)

        return group

    def _setup_widgets_properties(self):
        """Setup widget properties and initial values."""
        self.invoice_number_label.setObjectName("invoice_number_label")
        self.total_documents.setObjectName("total_documents")
        self.issue_date_label.setObjectName("receive_date_label")
        self.user_label.setObjectName("username_label")
        self.delivery_date_edit.setObjectName("delivery_date")
        self.source_language.setObjectName("source_language")
        self.target_language.setObjectName("target_language")
        self.final_amount.setObjectName("final_amount")
        self.remarks_text.setObjectName("remarks_text")

    @staticmethod
    def _style_info_label(label: QLabel):
        """Apply styling to info display labels."""
        label.setStyleSheet("""
            QLabel {
                padding: 8px;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: #f8f9fa;
                color: #495057;
                min-width: 150px;
            }
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)

    @staticmethod
    def _style_cost_label(label: QLabel):
        """Apply styling to cost display labels."""
        label.setStyleSheet("""
            QLabel {
                padding: 8px;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: #f8f9fa;
                color: #495057;
                font-weight: bold;
                min-width: 100px;
            }
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def _connect_signals(self):
        """Connect only user-editable widgets to the data changed signal."""
        self.delivery_date_edit.textChanged.connect(self._emit_other_changes_if_user)
        self.source_language.currentTextChanged.connect(self._emit_other_changes_if_user)
        self.target_language.currentTextChanged.connect(self._emit_other_changes_if_user)
        self.remarks_text.textChanged.connect(self._emit_other_changes_if_user)
        self.settings_button.clicked.connect(self.settings_requested.emit)

        def connect_row(field_name: str, spinbox: PlainDoubleSpinBox, button: QPushButton):
            # When the spinbox value changes, emit the main signal
            spinbox.valueChanged.connect(lambda value: self._emit_if_user(
                'financial_input_changed',
                field_name,
                value,
                'percent' if button.text() == '٪' else 'amount'
            ))
            # When the button is clicked, toggle the mode
            button.clicked.connect(lambda: self._toggle_input_mode(spinbox, button))

        connect_row('emergency', self.emergency_input, self.emergency_toggle)
        connect_row('discount', self.discount_input, self.discount_toggle)
        connect_row('advance', self.advance_input, self.advance_toggle)

    def _toggle_input_mode(self, spinbox: PlainDoubleSpinBox, button: QPushButton):
        """Toggles a spinbox between percentage and currency amount mode."""
        self._is_programmatically_updating = True
        try:
            if button.text() == '٪':
                # Switch to Amount mode
                button.setText("تومان")
                spinbox.setDecimals(0)
                spinbox.setRange(0, 999_999_999)
                spinbox.setSingleStep(1000)
            else:
                # Switch to Percent mode
                button.setText("٪")
                spinbox.setDecimals(2)
                spinbox.setRange(0.0, 100.0)
                spinbox.setSingleStep(0.5)
            spinbox.setValue(0)  # Reset value to prevent confusion
        finally:
            self._is_programmatically_updating = False
        # Manually trigger a signal emission with the new mode and a value of 0
        spinbox.valueChanged.emit(0)

    def _update_translation_direction(self):
        """Update the translation direction label."""
        source = self.source_language.currentText()
        target = self.target_language.currentText()
        direction_text = f"ترجمه از {source} به {target}"
        self.translation_direction_label.setText(direction_text)
        self.translation_direction_label.setStyleSheet("""
            QLabel {
                color: #007bff;
                font-weight: bold;
                padding: 5px;
                background-color: #f0f8ff;
                border-radius: 4px;
            }
        """)

    def _emit_if_user(self, signal_name, *args):
        """A helper that checks the flag before emitting a signal."""
        if not self._is_programmatically_updating:
            getattr(self, signal_name).emit(*args)

    def _emit_other_changes_if_user(self):
        """
        A helper for the 'other_input_changed' signal.
        """
        # If the program is setting the text, do not proceed.
        if self._is_programmatically_updating:
            return

        data = {
            'delivery_date': self.delivery_date_edit.text(),
            'src_lng': self.source_language.currentText(),
            'trgt_lng': self.target_language.currentText(),
            'remarks': self.remarks_text.toPlainText()
        }
        self.other_input_changed.emit(data)

    def display_static_info(self, customer, office_info):
        """Populates the non-editable fields once at the beginning."""
        # Invoice Info
        self.user_label.setText("محمد سجادی")

        # Customer Info
        self.customer_name.setText(customer.name)
        self.customer_national_id.setText(str(customer.national_id))
        self.customer_phone.setText(customer.phone)
        self.customer_email.setText(customer.email)
        self.customer_address.setText(customer.address)
        self.companions_num.setText(to_persian_numbers(len(customer.companions)))

        # Office Info
        self.office_name.setText(office_info.name)
        self.office_license.setText(office_info.reg_no)
        self.office_translator.setText(office_info.representative)
        self.office_address.setText(office_info.address)
        self.office_phone.setText(office_info.phone)
        self.office_email.setText(office_info.email)

    def update_display(self, details: InvoiceDetails):
        """Public slot to update all data display, both static and calculated."""
        self._is_programmatically_updating = True

        # Use the correct new widget names
        for w in [self.discount_input, self.emergency_input, self.advance_input]:
            w.blockSignals(True)

        try:
            # Invoice Info
            self.invoice_number_label.setText(to_persian_numbers(details.invoice_number))
            self.total_documents.setText(to_persian_numbers(details.docu_num))
            self.issue_date_label.setText(details.issue_date)
            # Prevent cursor jump by only updating if text is different
            if self.remarks_text.toPlainText() != details.remarks:
                self.remarks_text.setPlainText(details.remarks)

            # Financial Info (calculated labels)
            self.total_before_discount_label.setText(to_persian_numbers(f"{details.total_before_discount:,} تومان"))
            self.translation_cost_label.setText(to_persian_numbers(f"{details.translation_cost:,} تومان"))
            self.confirmation_cost_label.setText(to_persian_numbers(f"{details.confirmation_cost:,} تومان"))
            self.copy_cert_cost_label.setText(to_persian_numbers(f"{details.certified_copy_costs:,} تومان"))
            self.office_affairs_cost_label.setText(to_persian_numbers(f"{details.office_costs:,} تومان"))

            # --- FIX: REMOVED ALL setValue calls to the old, non-existent widgets ---
            # The new design only updates the display labels, not the input fields themselves.

            # Update the display labels with word-based amounts
            discount_words = amount_to_persian_words(details.discount_amount)
            if discount_words:
                formatted_percent = to_persian_numbers(f"{details.discount_percent:.2f}")
                self.discount_display_label.setText(f"{discount_words} تومان ({formatted_percent}٪)")
            else:
                self.discount_display_label.clear()

            emergency_words = amount_to_persian_words(details.emergency_cost_amount)
            if emergency_words:
                formatted_percent = to_persian_numbers(f"{details.emergency_cost_percent:.2f}")
                self.emergency_display_label.setText(f"{emergency_words} تومان ({formatted_percent}٪)")
            else:
                self.emergency_display_label.clear()

            advance_words = amount_to_persian_words(details.advance_payment_amount)
            if advance_words:
                formatted_percent = to_persian_numbers(f"{details.advance_payment_percent:.2f}")
                self.advance_display_label.setText(f"{advance_words} تومان ({formatted_percent}٪)")
            else:
                self.advance_display_label.clear()

            self.final_amount.setText(to_persian_numbers(f"{details.final_amount:,} تومان"))

        finally:
            self._is_programmatically_updating = False
            self._update_translation_direction()
            # Unblock signals for the correct new widgets
            for w in [self.discount_input, self.emergency_input, self.advance_input]:
                w.blockSignals(False)

    @staticmethod
    def _set_font(size=10, bold=False):
        """Get standard font for the application."""
        from shared.fonts.font_manager import FontManager
        return FontManager.get_font(size=size, bold=bold)
