# features/Invoice_Page/invoice_details/invoice_details_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QSpacerItem, QGroupBox, QFormLayout, QGridLayout, QLabel,
    QComboBox, QTextEdit
)
from PySide6.QtCore import Signal, Qt, QTimer
from features.Invoice_Page.invoice_details.invoice_details_models import InvoiceDetails, Language
from shared import to_persian_number
from shared.widgets.collapsable_box import CollapsibleBox


class InvoiceDetailsWidget(QWidget):

    user_input_changed = Signal(dict)
    percent_changed = Signal(str, float)  # field_name, percentage
    amount_changed = Signal(str, int)  # field_name, amount
    other_input_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InvoiceDetailsView")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._is_programmatically_updating = False

        # Update timer to prevent too frequent updates
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._emit_changes)
        self._update_timer.setSingleShot(True)

        self._init_widgets()
        self._setup_ui()
        self._connect_signals()

    def _init_widgets(self):
        """Initialize all widgets."""
        # Invoice group widgets (labels instead of line edits)
        self.invoice_number_label = QLabel('نامشخص')
        self.total_documents = QLabel("۰")
        self.issue_date_label = QLabel('نامشخص')
        self.user_label = QLabel("نامشخص")
        from shared.widgets.persian_calendar import DataDatePicker
        self.delivery_date_edit = DataDatePicker()
        self.source_language = QComboBox()
        self.target_language = QComboBox()
        self.translation_direction_label = QLabel()

        # Financial group - cost labels
        self.total_before_discount_label = QLabel('۰ تومان')
        self.translation_cost_label = QLabel('۰ تومان')
        self.confirmation_cost_label = QLabel('۰ تومان')
        self.office_affairs_cost_label = QLabel('۰ تومان')
        self.copy_cert_cost_label = QLabel('۰ تومان')

        from shared.widgets.persian_tools import NormalSpinBox, PersianDoubleSpinBox
        self.emergency_percent = PersianDoubleSpinBox()
        self.emergency_amount = NormalSpinBox()

        self.discount_percent = PersianDoubleSpinBox()
        self.discount_amount = NormalSpinBox()

        self.advance_payment_percent = PersianDoubleSpinBox()
        self.advance_payment_amount = NormalSpinBox()

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

        # Create main layout with four columns
        main_layout = QHBoxLayout()

        # First column - Invoice details
        invoice_group = self._create_invoice_group()

        # Second column - CustomerModel information
        customer_group = self._create_customer_group()

        # Third column - Financial details
        financial_group = self._create_financial_group()

        # Fourth column - Translation office info
        office_group = self._create_office_group()

        main_layout.addWidget(invoice_group, stretch=1)
        main_layout.addWidget(customer_group, stretch=1)
        main_layout.addWidget(financial_group, stretch=1)
        main_layout.addWidget(office_group, stretch=1)
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
        Creates the financial details group with a balanced, two-column layout.
        """
        group = QGroupBox("اطلاعات مالی")
        # The main layout for this group is a vertical box
        main_v_layout = QVBoxLayout(group)
        main_v_layout.setSpacing(15)

        # --- 1. Summary Section ---
        summary_layout = QFormLayout()

        self._style_cost_label(self.total_before_discount_label)
        self._style_cost_label(self.final_amount)

        summary_layout.addRow("<b>جمع کل هزینه‌ها:</b>", self.total_before_discount_label)
        main_v_layout.addLayout(summary_layout)

        # --- 2. Collapsible Details Section ---
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

        # --- 3. User Input Section (Horizontal) ---
        input_group = QGroupBox("تنظیمات پرداخت")   
        input_group.setStyleSheet("QGroupBox { border: none; margin-top: 0; }")
        input_layout = QGridLayout(input_group)

        # Make the input columns stretch horizontally
        input_layout.setColumnStretch(1, 1)
        input_layout.setColumnStretch(2, 1)

        # Row 0: Emergency
        input_layout.addWidget(QLabel("هزینه فوریت:"), 0, 0)
        input_layout.addWidget(self.emergency_percent, 0, 1)
        input_layout.addWidget(self.emergency_amount, 0, 2)

        # Row 1: Discount
        input_layout.addWidget(QLabel("تخفیف:"), 1, 0)
        input_layout.addWidget(self.discount_percent, 1, 1)
        input_layout.addWidget(self.discount_amount, 1, 2)

        # Row 2: Advance Payment
        input_layout.addWidget(QLabel("پیش‌پرداخت:"), 2, 0)
        input_layout.addWidget(self.advance_payment_percent, 2, 1)
        input_layout.addWidget(self.advance_payment_amount, 2, 2)

        # Add a stretchable empty row (row 3) BEFORE the final amount.
        # This will absorb all extra vertical space and push the final row down.
        input_layout.setRowStretch(3, 1)

        # Row 4: Final Amount
        final_amount_title_label = QLabel("<b>مبلغ نهایی:</b>")
        input_layout.addWidget(final_amount_title_label, 4, 0, 1, 1)
        input_layout.addWidget(self.final_amount, 4, 1, 1, 2)  # Span 2 columns

        main_v_layout.addWidget(input_group)

        return group

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

        self.remarks_text.setPlaceholderText("توضیحات و یادداشت‌های اینجا در فاکتور نشان داده می‌شود...")
        self.remarks_text.setMaximumHeight(100)
        layout.addWidget(self.remarks_text)

        return group

    def _setup_widgets_properties(self):
        """Setup widget properties and initial values."""
        # Set object names for styling
        self.invoice_number_label.setObjectName("invoice_number_label")
        self.total_documents.setObjectName("total_documents")
        self.issue_date_label.setObjectName("receive_date_label")
        self.user_label.setObjectName("username_label")
        self.delivery_date_edit.setObjectName("delivery_date")
        self.source_language.setObjectName("source_language")
        self.target_language.setObjectName("target_language")
        self.emergency_amount.setObjectName("emergency_cost_amount")
        self.discount_amount.setObjectName("discount_amount")
        self.advance_payment_amount.setObjectName("advance_payment_amount")
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

        # Two-way bound inputs
        self.discount_percent.valueChanged.connect(
            lambda val: self._emit_if_user('percent_changed', 'discount', val))
        self.discount_amount.valueChanged.connect(
            lambda val: self._emit_if_user('amount_changed', 'discount', val))

        self.emergency_percent.valueChanged.connect(
            lambda val: self._emit_if_user('percent_changed', 'emergency', val))
        self.emergency_amount.valueChanged.connect(
            lambda val: self._emit_if_user('amount_changed', 'emergency', val))

        self.advance_payment_percent.valueChanged.connect(
            lambda val: self._emit_if_user('percent_changed', 'advance', val))
        self.advance_payment_amount.valueChanged.connect(
            lambda val: self._emit_if_user('amount_changed', 'advance', val))

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

    def _schedule_update(self):
        """Schedules the _emit_changes call to avoid rapid firing."""
        self._update_timer.start(200)  # 200ms delay

    def _emit_if_user(self, signal_name, *args):
        """A helper that checks the flag before emitting a signal for two-way binding."""
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

    def _emit_changes(self):
        """Gathers raw data from all user-editable UI fields and emits the signal."""
        if self._is_programmatically_updating:
            return

        raw_data = {
            "delivery_date": self.delivery_date_edit.text(),
            "src_lng": self.source_language.currentText(),
            "trgt_lng": self.target_language.currentText(),
            "remarks": self.remarks_text.toPlainText(),
            "discount_percent": self.discount_percent.value(),
            "discount_amount": self.discount_amount.value(),
            "emergency_percent": self.emergency_percent.value(),
            "emergency_amount": self.emergency_amount.value(),
            "advance_percent": self.advance_payment_percent.value(),
            "advance_amount": self.advance_payment_amount.value(),
        }
        self.user_input_changed.emit(raw_data)

    def display_static_info(self, customer, office_info):
        """Populates the non-editable fields once at the beginning."""
        # Invoice Info
        self.user_label.setText("محمد سجادی")

        # Customer Info
        self.customer_name.setText(customer.name)
        self.customer_national_id.setText(customer.national_id)
        self.customer_phone.setText(customer.phone)
        self.customer_email.setText(customer.email)
        self.customer_address.setText(customer.address)
        self.companions_num.setText(to_persian_number(len(customer.companions)))

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

        for w in [self.discount_percent, self.discount_amount,
                  self.emergency_percent, self.emergency_amount,
                  self.advance_payment_percent, self.advance_payment_amount]:
            w.blockSignals(True)

        try:
            # Invoice Info
            self.invoice_number_label.setText(to_persian_number(details.invoice_number))
            self.total_documents.setText(to_persian_number(details.docu_num))
            self.issue_date_label.setText(details.issue_date)
            self.remarks_text.setPlainText(details.remarks)

            # Financial Info (both calculated and user-input)
            self.total_before_discount_label.setText(to_persian_number(f"{details.total_before_discount:,} تومان"))
            self.translation_cost_label.setText(to_persian_number(f"{details.translation_cost:,} تومان"))
            self.confirmation_cost_label.setText(to_persian_number(f"{details.confirmation_cost:,} تومان"))
            self.copy_cert_cost_label.setText(to_persian_number(f"{details.certified_copy_costs:,} تومان"))
            self.office_affairs_cost_label.setText(to_persian_number(f"{details.office_costs:,} تومان"))

            # Set values for the two-way bound fields
            self.discount_percent.setValue(details.discount_percent)
            self.discount_amount.setValue(details.discount_amount)

            self.emergency_percent.setValue(details.emergency_cost_percent)
            self.emergency_amount.setValue(details.emergency_cost_amount)

            self.advance_payment_percent.setValue(details.advance_payment_percent)
            self.advance_payment_amount.setValue(details.advance_payment_amount)

            self.final_amount.setText(to_persian_number(f"{details.final_amount:,} تومان"))

        finally:
            self._is_programmatically_updating = False

        self._update_translation_direction()

        # Unblock signals
        for w in [self.discount_percent, self.discount_amount,
                  self.emergency_percent, self.emergency_amount,
                  self.advance_payment_percent, self.advance_payment_amount]:
            w.blockSignals(False)

    @staticmethod
    def _set_font(size=10, bold=False):
        """Get standard font for the application."""
        from shared.fonts.font_manager import FontManager
        return FontManager.get_font(size=size, bold=bold)
