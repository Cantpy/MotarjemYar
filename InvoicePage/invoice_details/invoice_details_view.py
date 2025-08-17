from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSpinBox, QTextEdit, QGroupBox,
                               QComboBox, QCheckBox, QSizePolicy, QSpacerItem)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from datetime import datetime
from typing import Dict, Any
from InvoicePage.invoice_details import InvoiceData, Language, TranslationOfficeInfo
from shared.widgets.persian_tools import NormalSpinBox
from shared import to_persian_number, get_persian_date, DatePickerLineEdit


class InvoiceDetailsView(QWidget):
    """Step 3: Invoice Details view - Refactored with MVC pattern."""

    # Signals
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InvoiceDetailsView")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Update timer to prevent too frequent updates
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._emit_data_changed)
        self._update_timer.setSingleShot(True)

        # Initialize widgets
        self._init_widgets()
        self._setup_ui()
        self._connect_signals()

    def _init_widgets(self):
        """Initialize all widgets."""
        # Invoice group widgets (labels instead of line edits)
        self.receipt_number_label = QLabel("نامشخص")
        self.total_documents = QLabel("۰")
        self.receive_date_label = QLabel()
        self.username_label = QLabel("نامشخص")
        self.delivery_date = DatePickerLineEdit()

        # Language selection
        self.source_language = QComboBox()
        self.target_language = QComboBox()
        self.translation_direction_label = QLabel()

        # Financial widgets - cost labels
        self.translation_cost_label = QLabel("۰ تومان")
        self.confirmation_cost_label = QLabel("۰ تومان")
        self.office_affairs_cost_label = QLabel("۰ تومان")
        self.copy_cert_cost_label = QLabel("۰ تومان")

        # Emergency cost widgets
        self.emergency_checkbox = QCheckBox("هزینه فوریت")
        self.emergency_cost_spinbox = NormalSpinBox()
        self.emergency_cost_spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.emergency_cost_spinbox.setSingleStep(1000)

        # Other financial widgets
        self.discount_amount = NormalSpinBox()
        self.discount_amount.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.advance_payment = NormalSpinBox()
        self.advance_payment.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
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
        layout.setSpacing(20)

        # Title
        title = QLabel("مرحله 3: جزئیات فاکتور")
        title.setFont(self._get_font(16, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        layout.addWidget(title)

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
        self._apply_form_styling()
        self._setup_widgets_properties()

    def _create_invoice_group(self) -> QGroupBox:
        """Create invoice information group."""
        group = QGroupBox("اطلاعات فاکتور")
        form = QFormLayout(group)
        form.setSpacing(15)

        # Set current date/time for receive date
        current_datetime = get_persian_date()
        self.receive_date_label.setText(current_datetime)

        # Setup language combos
        languages = [lang.value for lang in Language]
        self.source_language.addItems(languages)
        self.target_language.addItems(languages)
        self.source_language.setCurrentText(Language.FARSI.value)
        self.target_language.setCurrentText(Language.ENGLISH.value)

        # Style the labels
        self._style_info_label(self.receipt_number_label)
        self._style_info_label(self.total_documents)
        self._style_info_label(self.receive_date_label)
        self._style_info_label(self.username_label)

        # Update translation direction label
        self._update_translation_direction()

        form.addRow("شماره رسید:", self.receipt_number_label)
        form.addRow("تعداد اسناد:", self.total_documents)
        form.addRow("تاریخ صدور:", self.receive_date_label)
        form.addRow("تاریخ تحویل:", self.delivery_date)
        form.addRow("کاربر:", self.username_label)
        form.addRow("زبان مبدأ:", self.source_language)
        form.addRow("زبان مقصد:", self.target_language)
        form.addRow("", self.translation_direction_label)

        return group

    def _create_customer_group(self) -> QGroupBox:
        """Create customer information group."""
        group = QGroupBox("اطلاعات مشتری")
        form = QFormLayout(group)
        form.setSpacing(15)

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
        """Create financial details group."""
        group = QGroupBox("اطلاعات مالی")
        form = QFormLayout(group)
        form.setSpacing(15)

        # Cost labels (read-only display)
        self._style_cost_label(self.translation_cost_label)
        self._style_cost_label(self.confirmation_cost_label)
        self._style_cost_label(self.office_affairs_cost_label)
        self._style_cost_label(self.copy_cert_cost_label)
        self._style_cost_label(self.final_amount)

        # Emergency cost setup
        self.emergency_cost_spinbox.setEnabled(False)
        self.emergency_cost_spinbox.setGroupSeparatorShown(True)

        # Create emergency layout with label for visual grouping
        self.emergency_label = QLabel("مبلغ فوریت:")
        self.emergency_label.setEnabled(False)  # Initially disabled

        # Other financial inputs
        self.discount_amount.setGroupSeparatorShown(True)
        self.advance_payment.setGroupSeparatorShown(True)

        form.addRow("هزینه ترجمه:", self.translation_cost_label)
        form.addRow("هزینه تاییدات:", self.confirmation_cost_label)
        form.addRow("امور دفتری:", self.office_affairs_cost_label)
        form.addRow("هزینه کپی برابر اصل:", self.copy_cert_cost_label)
        form.addRow("", self.emergency_checkbox)
        form.addRow(self.emergency_label, self.emergency_cost_spinbox)
        form.addRow("تخفیف:", self.discount_amount)
        form.addRow("پیش‌پرداخت:", self.advance_payment)
        form.addRow("مبلغ نهایی:", self.final_amount)

        return group

    def _create_office_group(self) -> QGroupBox:
        """Create translation office information group."""
        group = QGroupBox("اطلاعات دارالترجمه")
        form = QFormLayout(group)
        form.setSpacing(15)

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
        group = QGroupBox("توضیحات اضافی")
        layout = QVBoxLayout(group)

        self.remarks_text.setPlaceholderText("توضیحات و یادداشت‌های اضافی...")
        self.remarks_text.setMaximumHeight(100)
        layout.addWidget(self.remarks_text)

        return group

    def _setup_widgets_properties(self):
        """Setup widget properties and initial values."""
        # Set object names for styling
        self.receipt_number_label.setObjectName("receipt_number_label")
        self.total_documents.setObjectName("total_documents")
        self.receive_date_label.setObjectName("receive_date_label")
        self.username_label.setObjectName("username_label")
        self.delivery_date.setObjectName("delivery_date")
        self.source_language.setObjectName("source_language")
        self.target_language.setObjectName("target_language")
        self.emergency_cost_spinbox.setObjectName("emergency_cost_spinbox")
        self.discount_amount.setObjectName("discount_amount")
        self.advance_payment.setObjectName("advance_payment")
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

    def _apply_form_styling(self):
        """Apply consistent styling to form elements."""
        form_style = """
            QLineEdit, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QComboBox {
                padding: 8px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #007bff;
            }
            QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, 
            QTextEdit:focus, QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QDateEdit::drop-down, QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #e9ecef;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #f8f9fa;
            }
            QDateEdit::down-arrow, QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
            QCheckBox {
                spacing: 8px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #e9ecef;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #495057;
            }
        """
        self.setStyleSheet(form_style)

    def _connect_signals(self):
        """Connect form signals."""
        # Connect form elements to data_changed signal
        self.delivery_date.textChanged.connect(self._schedule_data_changed)
        self.source_language.currentTextChanged.connect(self._on_language_changed)
        self.target_language.currentTextChanged.connect(self._on_language_changed)
        self.emergency_checkbox.toggled.connect(self._on_emergency_toggled)
        self.emergency_cost_spinbox.valueChanged.connect(self._update_final_amount)
        self.discount_amount.valueChanged.connect(self._update_final_amount)
        self.advance_payment.valueChanged.connect(self._update_final_amount)
        self.remarks_text.textChanged.connect(self._schedule_data_changed)

        # Note: Office info and customer info are now labels (no signals needed)

        # Initial calculations
        self._update_final_amount()

    def _schedule_data_changed(self):
        """Schedule data changed signal emission to avoid too frequent updates."""
        self._update_timer.start(100)  # 100ms delay

    def _emit_data_changed(self):
        """Emit the data changed signal."""
        self.data_changed.emit()

    def _on_language_changed(self):
        """Handle language selection changes."""
        self._update_translation_direction()
        self._schedule_data_changed()

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

    def _on_emergency_toggled(self, checked: bool):
        """Handle emergency checkbox toggle."""
        self.emergency_cost_spinbox.setEnabled(checked)
        self.emergency_label.setEnabled(checked)  # Enable/disable the label too

        if checked:
            # Calculate half of translation cost
            translation_cost = self._parse_cost_from_label(self.translation_cost_label.text())
            emergency_cost = int(translation_cost / 2)
            self.emergency_cost_spinbox.setValue(emergency_cost)
        else:
            self.emergency_cost_spinbox.setValue(0)

        self._update_final_amount()

    @staticmethod
    def _parse_cost_from_label(text: str) -> float:
        """Parse cost value from label text."""
        if text == "۰ تومان":
            return 0.0
        # Remove "تومان" and thousand separators, then convert to float
        clean_text = text.replace(" تومان", "").replace("٬", "").replace(",", "")
        try:
            return float(clean_text)
        except ValueError:
            return 0.0

    def _update_final_amount(self):
        """Update final amount based on all costs."""
        # Calculate subtotal from cost labels
        translation_cost = self._parse_cost_from_label(self.translation_cost_label.text())
        confirmation_cost = self._parse_cost_from_label(self.confirmation_cost_label.text())
        office_cost = self._parse_cost_from_label(self.office_affairs_cost_label.text())
        copy_cost = self._parse_cost_from_label(self.copy_cert_cost_label.text())
        emergency_cost = self.emergency_cost_spinbox.value()

        subtotal = translation_cost + confirmation_cost + office_cost + copy_cost + emergency_cost
        discount = self.discount_amount.value()
        advance = self.advance_payment.value()

        final = max(0, int(subtotal - discount - advance))
        final_english = self._format_currency(final)
        self.final_amount.setText(to_persian_number(final_english))

        # Emit data changed signal
        self._schedule_data_changed()

    def update_financial_display(self, translation_cost: float = 0, confirmation_cost: float = 0,
                                 office_affairs_cost: float = 0, copy_cert_cost: float = 0):
        """Update financial cost displays."""
        self.translation_cost_label.setText(self._format_currency(translation_cost))
        self.confirmation_cost_label.setText(self._format_currency(confirmation_cost))
        self.office_affairs_cost_label.setText(self._format_currency(office_affairs_cost))
        self.copy_cert_cost_label.setText(self._format_currency(copy_cert_cost))

        # Update emergency cost if emergency is checked
        if self.emergency_checkbox.isChecked():
            emergency_cost = int(translation_cost / 2)
            self.emergency_cost_spinbox.setValue(emergency_cost)

        self._update_final_amount()

    def update_emergency_cost(self, cost: float):
        """Update emergency cost display."""
        self.emergency_cost_spinbox.setValue(int(cost))

    def update_language_display(self):
        """Update language display (called by controller)."""
        self._update_translation_direction()

    def update_office_info_display(self):
        """Update office info display (called by controller)."""
        # This method can be used to refresh office info display if needed
        pass

    def _format_currency(self, amount: float) -> str:
        """Format currency amount."""
        if amount == 0:
            return "۰ تومان"
        return f"{amount:,.0f} تومان".replace(',', '٬')

    def get_data(self) -> Dict[str, Any]:
        """Get current form data."""
        return {
            'receipt_number': self.receipt_number_label.text(),
            'total_documents': self.total_documents.text(),
            'receive_date': self.receive_date_label.text(),
            'delivery_date': self.delivery_date.text(),
            'username': self.username_label.text(),
            'source_language': self.source_language.currentText(),
            'target_language': self.target_language.currentText(),
            'translation_cost': self._parse_cost_from_label(self.translation_cost_label.text()),
            'confirmation_cost': self._parse_cost_from_label(self.confirmation_cost_label.text()),
            'office_affairs_cost': self._parse_cost_from_label(self.office_affairs_cost_label.text()),
            'copy_cert_cost': self._parse_cost_from_label(self.copy_cert_cost_label.text()),
            'emergency_cost': self.emergency_cost_spinbox.value(),
            'is_emergency': self.emergency_checkbox.isChecked(),
            'discount_amount': self.discount_amount.value(),
            'advance_payment': self.advance_payment.value(),
            'final_amount': self._parse_cost_from_label(self.final_amount.text()),
            'remarks': self.remarks_text.toPlainText().strip(),
            'customer_info': {
                'name': self.customer_name.text(),
                'phone': self.customer_phone.text(),
                'national_id': self.customer_national_id.text(),
                'email': self.customer_email.text(),
                'address': self.customer_address.text(),
                'total_companions': self.companions_num.text()
            },
            'office_info': {
                'name': self.office_name.text(),
                'registration_number': self.office_license.text(),
                'translator': self.office_translator.text(),
                'address': self.office_address.text(),
                'phone': self.office_phone.text(),
                'email': self.office_email.text()
            }
        }

    def set_data(self, invoice_data: InvoiceData, translation_office_info: TranslationOfficeInfo):
        """Set form data from InvoiceData object."""
        # Block signals to prevent unnecessary updates
        self.blockSignals(True)

        try:
            # Set basic info
            self.receipt_number_label.setText(invoice_data.receipt_number)
            self.total_documents.setText(str(invoice_data.total_documents))
            self.username_label.setText(invoice_data.username)

            # Set receive date with current format
            if isinstance(invoice_data.receive_date, datetime):
                date_text = invoice_data.receive_date.strftime("%Y/%m/%d %H:%M")
            else:
                date_text = datetime.now().strftime("%Y/%m/%d %H:%M")
            self.receive_date_label.setText(to_persian_number(date_text))

            # Set languages
            self.source_language.setCurrentText(invoice_data.source_language.value)
            self.target_language.setCurrentText(invoice_data.target_language.value)

            # Set financial data
            financial = invoice_data.financial
            self.update_financial_display(
                financial.translation_cost,
                financial.confirmation_cost,
                financial.office_affairs_cost,
                financial.copy_certification_cost
            )

            self.emergency_checkbox.setChecked(financial.is_emergency)
            self.emergency_cost_spinbox.setValue(int(financial.emergency_cost))
            self.emergency_cost_spinbox.setEnabled(financial.is_emergency)
            self.discount_amount.setValue(financial.discount_amount)
            self.advance_payment.setValue(financial.advance_payment)
            # final_amount will be calculated automatically

            # Set office info
            office = translation_office_info
            self.office_name.setText(office.name)
            self.office_license.setText(to_persian_number(office.registration_number))
            self.office_translator.setText(office.representative)
            self.office_address.setText(office.address)
            self.office_phone.setText(office.phone)
            self.office_email.setText(office.email)

            # Set customer info (if available in invoice_data)
            if hasattr(invoice_data, 'customer_info'):
                customer = invoice_data.customer_info
                self.customer_name.setText(getattr(customer, 'name', 'نامشخص'))
                self.customer_phone.setText(getattr(customer, 'phone', 'نامشخص'))
                self.customer_national_id.setText(getattr(customer, 'national_id', 'نامشخص'))
                self.customer_email.setText(getattr(customer, 'email', 'نامشخص'))
                self.customer_address.setText(getattr(customer, 'address', 'نامشخص'))
                self.companions_num.setText(getattr(customer, 'total_companions', '۰'))

            # Set remarks
            self.remarks_text.setPlainText(invoice_data.remarks)

        finally:
            self.blockSignals(False)

        # Update displays
        self._update_translation_direction()
        self._update_final_amount()

    def clear_data(self):
        """Clear all form data."""
        self.receipt_number_label.setText("نامشخص")
        self.receive_date_label.setText(to_persian_number(datetime.now().strftime("%Y/%m/%d %H:%M")))
        self.username_label.setText("نامشخص")

        self.source_language.setCurrentText(Language.FARSI.value)
        self.target_language.setCurrentText(Language.ENGLISH.value)

        # Clear financial data
        self.translation_cost_label.setText("۰ تومان")
        self.confirmation_cost_label.setText("۰ تومان")
        self.office_affairs_cost_label.setText("۰ تومان")
        self.copy_cert_cost_label.setText("۰ تومان")

        self.emergency_checkbox.setChecked(False)
        self.emergency_cost_spinbox.setValue(0)
        self.emergency_cost_spinbox.setEnabled(False)
        self.discount_amount.setValue(0)
        self.advance_payment.setValue(0)
        # final_amount will be calculated automatically

        # Clear office info
        self.office_name.setText("نامشخص")
        self.office_license.setText("نامشخص")
        self.office_translator.setText("نامشخص")
        self.office_address.setText("نامشخص")
        self.office_phone.setText("نامشخص")
        self.office_email.setText("نامشخص")

        # Clear customer info
        self.customer_name.setText("نامشخص")
        self.customer_phone.setText("نامشخص")
        self.customer_national_id.setText("نامشخص")
        self.customer_email.setText("نامشخص")
        self.customer_address.setText("نامشخص")
        self.companions_num.setText("۰")

        # Clear remarks
        self.remarks_text.clear()

        self._update_translation_direction()
        self._update_final_amount()

    def is_valid(self) -> bool:
        """Check if current data is valid."""
        return (self.receipt_number_label.text() != "نامشخص" and
                self.receipt_number_label.text().strip() != "")

    def get_validation_errors(self) -> list:
        """Get list of validation errors."""
        errors = []

        if self.receipt_number_label.text() == "نامشخص" or not self.receipt_number_label.text().strip():
            errors.append("شماره رسید الزامی است")

        # Check if any costs are set
        total_cost = (self._parse_cost_from_label(self.translation_cost_label.text()) +
                      self._parse_cost_from_label(self.confirmation_cost_label.text()) +
                      self._parse_cost_from_label(self.office_affairs_cost_label.text()) +
                      self._parse_cost_from_label(self.copy_cert_cost_label.text()) +
                      self.emergency_cost_spinbox.value())

        if total_cost <= 0:
            errors.append("مجموع هزینه باید بیشتر از صفر باشد")

        if self.discount_amount.value() > total_cost:
            errors.append("تخفیف نمی‌تواند بیشتر از مجموع هزینه باشد")

        if self.advance_payment.value() > (total_cost - self.discount_amount.value()):
            errors.append("پیش‌پرداخت نمی‌تواند بیشتر از مبلغ قابل پرداخت باشد")

        receive_date = get_persian_date()  # Using current date as receive date
        delivery_date = self.delivery_date.text()
        if delivery_date < receive_date:
            errors.append("تاریخ تحویل نمی‌تواند قبل از تاریخ دریافت باشد")

        return errors

    def set_customer_info(self, name: str = None, phone: str = None, national_id: str = None,
                          email: str = None, address: str = None, companion_num: int = None):
        """Set customer information (called by controller)."""
        if name is not None:
            self.customer_name.setText(name or "نامشخص")
        if phone is not None:
            self.customer_phone.setText(phone or "نامشخص")
        if national_id is not None:
            self.customer_national_id.setText(national_id or "نامشخص")
        if email is not None:
            self.customer_email.setText(email or "نامشخص")
        if address is not None:
            self.customer_address.setText(address or "نامشخص")
        if companion_num is not None:
            self.companions_num.setText(companion_num or "۰")

    def set_office_info(self, name: str = None, registration_number: int = None, translator: str = None,
                        address: str = None, phone: str = None, email: str = None):
        """Set office information (called by controller)."""
        if name is not None:
            self.office_name.setText(name or "نامشخص")
        if registration_number is not None:
            self.office_license.setText(registration_number or "نامشخص")
        if translator is not None:
            self.office_translator.setText(translator or "نامشخص")
        if address is not None:
            self.office_address.setText(address or "نامشخص")
        if phone is not None:
            self.office_phone.setText(phone or "نامشخص")
        if email is not None:
            self.office_email.setText(email or "نامشخص")

    def set_receipt_number(self, receipt_number: str):
        """Set receipt number (called by controller)."""
        self.receipt_number_label.setText(receipt_number)

    def set_username(self, username: str):
        """Set username (called by controller)."""
        self.username_label.setText(username)

    def get_final_amount(self) -> float:
        """Get calculated final amount."""
        return self._parse_cost_from_label(self.final_amount.text())

    @staticmethod
    def _get_font(size=10, bold=False):
        """Get standard font for the application."""
        font = QFont("IRANSans")
        font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = InvoiceDetailsView()
    window.show()
    sys.exit(app.exec())
