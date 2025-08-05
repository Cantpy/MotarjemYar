from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QLabel,
    QPushButton, QGroupBox, QGridLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QScrollArea,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QSize, QDate
from PySide6.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor


class InvoiceWizardUI(QWidget):
    """Main invoice wizard widget managing the five-step process."""

    # Signals for navigation and completion
    step_completed = Signal(int, dict)  # step_index, step_data
    wizard_finished = Signal(dict)  # complete_invoice_data
    step_changed = Signal(int)  # current_step_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InvoiceWizard")
        self.current_step = 0
        self.wizard_data = {
            'customer': {},
            'documents': {},
            'invoice_details': {},
            'preview_settings': {},
            'sharing_options': {}
        }
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the main wizard UI structure."""
        self.resize(1000, 800)
        self.setFont(self._get_font())
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # Progress indicator
        self._create_progress_indicator()
        main_layout.addWidget(self.progress_frame)

        # Stacked widget for wizard steps
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("wizard_stack")

        # Create all wizard steps
        self._create_step_1_customer()
        self._create_step_2_documents()
        self._create_step_3_invoice_details()
        self._create_step_4_preview()
        self._create_step_5_sharing()

        main_layout.addWidget(self.stacked_widget)

        # Navigation buttons
        self._create_navigation_buttons()
        main_layout.addWidget(self.navigation_frame)

    def _create_progress_indicator(self):
        """Create progress indicator showing all five steps."""
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("progress_frame")
        self.progress_frame.setMaximumHeight(100)
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 12px;
                margin: 2px;
            }
        """)

        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(30, 20, 30, 20)
        progress_layout.setSpacing(15)

        # Step indicators
        self.step_labels = []
        step_names = [
            "1. اطلاعات مشتری",
            "2. اطلاعات اسناد",
            "3. جزئیات فاکتور",
            "4. پیش‌نمایش فاکتور",
            "5. اشتراک‌گذاری"
        ]

        for i, step_name in enumerate(step_names):
            # Step circle and label
            step_container = QVBoxLayout()

            # Circle indicator
            step_circle = QLabel(str(i + 1))
            step_circle.setObjectName(f"step_circle_{i}")
            step_circle.setFixedSize(40, 40)
            step_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_circle.setStyleSheet(self._get_step_circle_style(i == 0))

            # Step label
            step_label = QLabel(step_name)
            step_label.setObjectName(f"step_label_{i}")
            step_label.setFont(self._get_font(9, bold=True))
            step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_label.setWordWrap(True)

            step_container.addWidget(step_circle)
            step_container.addWidget(step_label)

            progress_layout.addLayout(step_container)
            self.step_labels.append((step_circle, step_label))

            # Add arrow between steps (except after last step)
            if i < len(step_names) - 1:
                arrow = QLabel("←")
                arrow.setFont(self._get_font(16, bold=True))
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                arrow.setStyleSheet("color: #6c757d;")
                progress_layout.addWidget(arrow)

        progress_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

    def _get_step_circle_style(self, is_active=False, is_completed=False):
        """Get CSS style for step circle indicators."""
        if is_completed:
            return """
                QLabel {
                    background-color: #28a745;
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """
        elif is_active:
            return """
                QLabel {
                    background-color: #007bff;
                    color: white;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """
        else:
            return """
                QLabel {
                    background-color: #e9ecef;
                    color: #6c757d;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """

    def _create_step_1_customer(self):
        """Create Step 1: CustomerModel Information."""
        step1_widget = QWidget()
        step1_layout = QVBoxLayout(step1_widget)
        step1_layout.setSpacing(20)

        # Title
        title = QLabel("مرحله 1: اطلاعات مشتری")
        title.setFont(self._get_font(16, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        step1_layout.addWidget(title)

        # CustomerModel info form
        customer_group = QGroupBox("اطلاعات شخصی مشتری")
        customer_layout = QFormLayout(customer_group)
        customer_layout.setSpacing(15)

        # Form fields
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("نام و نام خانوادگی")
        self.customer_national_id = QLineEdit()
        self.customer_national_id.setPlaceholderText("کد ملی")
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("شماره تماس")
        self.customer_email = QLineEdit()
        self.customer_email.setPlaceholderText("آدرس ایمیل")
        self.customer_address = QTextEdit()
        self.customer_address.setPlaceholderText("آدرس کامل")
        self.customer_address.setMaximumHeight(80)

        # Add fields to form
        customer_layout.addRow("نام و نام خانوادگی:", self.customer_name)
        customer_layout.addRow("کد ملی:", self.customer_national_id)
        customer_layout.addRow("شماره تماس:", self.customer_phone)
        customer_layout.addRow("ایمیل:", self.customer_email)
        customer_layout.addRow("آدرس:", self.customer_address)

        step1_layout.addWidget(customer_group)
        step1_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_widget.addWidget(step1_widget)

    def _create_step_2_documents(self):
        """Create Step 2: Documents Information."""
        step2_widget = QWidget()
        step2_layout = QVBoxLayout(step2_widget)
        step2_layout.setSpacing(20)

        # Title
        title = QLabel("مرحله 2: اطلاعات اسناد")
        title.setFont(self._get_font(16, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        step2_layout.addWidget(title)

        # Documents table
        docs_group = QGroupBox("لیست اسناد برای ترجمه")
        docs_layout = QVBoxLayout(docs_group)

        # Add document button
        add_doc_button = QPushButton("+ افزودن سند جدید")
        add_doc_button.setObjectName("add_document_btn")
        add_doc_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        docs_layout.addWidget(add_doc_button)

        # Documents table
        self.documents_table = QTableWidget(0, 5)
        self.documents_table.setHorizontalHeaderLabels([
            "نام سند", "نوع سند", "تعداد صفحات", "زبان مبدا", "زبان مقصد"
        ])
        self.documents_table.horizontalHeader().setStretchLastSection(True)
        self.documents_table.setAlternatingRowColors(True)
        self.documents_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        docs_layout.addWidget(self.documents_table)
        step2_layout.addWidget(docs_group)

        self.stacked_widget.addWidget(step2_widget)

    def _create_step_3_invoice_details(self):
        """Create Step 3: Invoice Details."""
        step3_widget = QWidget()
        step3_layout = QVBoxLayout(step3_widget)
        step3_layout.setSpacing(20)

        # Title
        title = QLabel("مرحله 3: جزئیات فاکتور")
        title.setFont(self._get_font(16, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        step3_layout.addWidget(title)

        # Create two columns
        details_layout = QHBoxLayout()

        # Left column - Invoice details
        invoice_group = QGroupBox("اطلاعات فاکتور")
        invoice_form = QFormLayout(invoice_group)
        invoice_form.setSpacing(15)

        self.receipt_number = QLineEdit()
        self.receipt_number.setPlaceholderText("شماره رسید")
        self.receive_date = QDateEdit()
        self.receive_date.setDate(QDate.currentDate())
        self.delivery_date = QDateEdit()
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.username = QLineEdit()
        self.username.setPlaceholderText("نام کاربر")

        invoice_form.addRow("شماره رسید:", self.receipt_number)
        invoice_form.addRow("تاریخ دریافت:", self.receive_date)
        invoice_form.addRow("تاریخ تحویل:", self.delivery_date)
        invoice_form.addRow("کاربر:", self.username)

        # Right column - Financial details
        financial_group = QGroupBox("اطلاعات مالی")
        financial_form = QFormLayout(financial_group)
        financial_form.setSpacing(15)

        self.total_amount = QDoubleSpinBox()
        self.total_amount.setRange(0, 999999999)
        self.total_amount.setSuffix(" تومان")
        self.discount_amount = QDoubleSpinBox()
        self.discount_amount.setRange(0, 999999999)
        self.discount_amount.setSuffix(" تومان")
        self.advance_payment = QDoubleSpinBox()
        self.advance_payment.setRange(0, 999999999)
        self.advance_payment.setSuffix(" تومان")

        financial_form.addRow("مجموع هزینه:", self.total_amount)
        financial_form.addRow("تخفیف:", self.discount_amount)
        financial_form.addRow("پیش‌پرداخت:", self.advance_payment)

        details_layout.addWidget(invoice_group)
        details_layout.addWidget(financial_group)
        step3_layout.addLayout(details_layout)

        # Remarks section
        remarks_group = QGroupBox("توضیحات اضافی")
        remarks_layout = QVBoxLayout(remarks_group)

        self.remarks_text = QTextEdit()
        self.remarks_text.setPlaceholderText("توضیحات و یادداشت‌های اضافی...")
        self.remarks_text.setMaximumHeight(100)
        remarks_layout.addWidget(self.remarks_text)

        step3_layout.addWidget(remarks_group)
        step3_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_widget.addWidget(step3_widget)

    def _create_step_4_preview(self):
        """Create Step 4: Invoice Preview."""
        step4_widget = QWidget()
        step4_layout = QVBoxLayout(step4_widget)
        step4_layout.setSpacing(20)

        # Title
        title = QLabel("مرحله 4: پیش‌نمایش فاکتور")
        title.setFont(self._get_font(16, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        step4_layout.addWidget(title)

        # Preview controls
        controls_layout = QHBoxLayout()

        # Paper size selection
        size_group = QGroupBox("اندازه کاغذ")
        size_layout = QHBoxLayout(size_group)

        self.paper_size = QComboBox()
        self.paper_size.addItems(["A4", "A5", "Letter"])
        self.paper_size.setCurrentText("A4")
        size_layout.addWidget(self.paper_size)

        controls_layout.addWidget(size_group)

        # Preview actions
        actions_group = QGroupBox("عملیات")
        actions_layout = QHBoxLayout(actions_group)

        self.refresh_preview_btn = QPushButton("🔄 بروزرسانی پیش‌نمایش")
        self.save_pdf_btn = QPushButton("💾 ذخیره PDF")
        self.print_preview_btn = QPushButton("🖨️ چاپ")

        for btn in [self.refresh_preview_btn, self.save_pdf_btn, self.print_preview_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            actions_layout.addWidget(btn)

        controls_layout.addWidget(actions_group)
        controls_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        step4_layout.addLayout(controls_layout)

        # Preview area
        preview_group = QGroupBox("پیش‌نمایش فاکتور")
        preview_layout = QVBoxLayout(preview_group)

        # Scroll area for preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Preview widget (this will contain the actual invoice preview)
        self.preview_widget = self._create_invoice_preview_widget()
        scroll_area.setWidget(self.preview_widget)

        preview_layout.addWidget(scroll_area)
        step4_layout.addWidget(preview_group)

        self.stacked_widget.addWidget(step4_widget)

    def _create_invoice_preview_widget(self):
        """Create the actual invoice preview widget."""
        preview_widget = QWidget()
        preview_widget.setFixedSize(595, 842)  # A4 size in pixels (72 DPI)
        preview_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
            }
        """)

        layout = QVBoxLayout(preview_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header section
        header_layout = QHBoxLayout()

        # Translation office info (left)
        office_info = QVBoxLayout()
        office_title = QLabel("دارالترجمه رسمی")
        office_title.setFont(self._get_font(14, bold=True))
        office_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        office_details = QLabel(
            "شماره ثبت: 12345\nآدرس: تهران، خیابان ولیعصر\nتلفن: 021-12345678\nایمیل: info@translation.com")
        office_details.setFont(self._get_font(9))
        office_details.setAlignment(Qt.AlignmentFlag.AlignRight)

        office_info.addWidget(office_title)
        office_info.addWidget(office_details)

        # Logo (center)
        logo_label = QLabel("LOGO")
        logo_label.setFixedSize(80, 80)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #6c757d;
                font-weight: bold;
            }
        """)

        # Invoice info (right)
        invoice_info = QVBoxLayout()
        invoice_title = QLabel("فاکتور ترجمه")
        invoice_title.setFont(self._get_font(14, bold=True))
        invoice_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        invoice_details = QLabel("شماره فاکتور: 001\nتاریخ صدور: 1403/01/01\nتاریخ تحویل: 1403/01/08")
        invoice_details.setFont(self._get_font(9))
        invoice_details.setAlignment(Qt.AlignmentFlag.AlignRight)

        invoice_info.addWidget(invoice_title)
        invoice_info.addWidget(invoice_details)

        header_layout.addLayout(office_info)
        header_layout.addWidget(logo_label)
        header_layout.addLayout(invoice_info)

        layout.addLayout(header_layout)

        # CustomerModel info section
        customer_group = QGroupBox("اطلاعات مشتری")
        customer_layout = QHBoxLayout(customer_group)

        customer_details = QLabel("نام: نام مشتری\nکد ملی: 1234567890\nتلفن: 09123456789\nایمیل: customer@email.com")
        customer_details.setFont(self._get_font(10))
        customer_details.setAlignment(Qt.AlignmentFlag.AlignRight)
        customer_layout.addWidget(customer_details)

        layout.addWidget(customer_group)

        # Documents table
        table_group = QGroupBox("اطلاعات اسناد")
        table_layout = QVBoxLayout(table_group)

        # Sample table (in real implementation, this would be populated with actual data)
        preview_table = QTableWidget(3, 4)
        preview_table.setHorizontalHeaderLabels(["نام سند", "نوع", "تعداد صفحات", "هزینه"])
        preview_table.setAlternatingRowColors(True)

        # Sample data
        sample_data = [
            ["گذرنامه", "شناسایی", "1", "50,000"],
            ["مدرک تحصیلی", "تحصیلی", "2", "100,000"],
            ["شهادت تولد", "شناسایی", "1", "50,000"]
        ]

        for i, row_data in enumerate(sample_data):
            for j, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                preview_table.setItem(i, j, item)

        preview_table.resizeColumnsToContents()
        preview_table.setMaximumHeight(150)
        table_layout.addWidget(preview_table)

        layout.addWidget(table_group)

        # Financial summary
        financial_group = QGroupBox("خلاصه مالی")
        financial_layout = QGridLayout(financial_group)

        financial_labels = [
            ("مجموع هزینه:", "200,000 تومان"),
            ("تخفیف:", "0 تومان"),
            ("پیش‌پرداخت:", "50,000 تومان"),
            ("قابل پرداخت:", "150,000 تومان")
        ]

        for i, (label, value) in enumerate(financial_labels):
            label_widget = QLabel(label)
            label_widget.setFont(self._get_font(10, bold=True))
            label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

            value_widget = QLabel(value)
            value_widget.setFont(self._get_font(10))
            value_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

            financial_layout.addWidget(label_widget, i, 0)
            financial_layout.addWidget(value_widget, i, 1)

        layout.addWidget(financial_group)

        # Footer
        footer_layout = QHBoxLayout()

        # Signature section
        signature_label = QLabel("امضاء مشتری:\n\n\n_________________")
        signature_label.setFont(self._get_font(10))
        signature_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Terms section
        terms_label = QLabel(
            "• لطفاً اصل مدارک را همراه داشته باشید\n• مهلت تحویل تا یک هفته پس از تاریخ مقرر\n• تایید مدارک با وزارت دادگستری")
        terms_label.setFont(self._get_font(8))
        terms_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        terms_label.setWordWrap(True)

        footer_layout.addWidget(signature_label)
        footer_layout.addWidget(terms_label)

        layout.addLayout(footer_layout)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        return preview_widget

    def _create_step_5_sharing(self):
        """Create Step 5: Sharing Options."""
        step5_widget = QWidget()
        step5_layout = QVBoxLayout(step5_widget)
        step5_layout.setSpacing(20)

        # Title
        title = QLabel("مرحله 5: اشتراک‌گذاری فاکتور")
        title.setFont(self._get_font(16, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        step5_layout.addWidget(title)

        # Sharing options
        sharing_layout = QHBoxLayout()

        # Email sharing
        email_group = QGroupBox("ارسال ایمیل")
        email_layout = QVBoxLayout(email_group)

        self.email_enabled = QCheckBox("ارسال فاکتور به ایمیل مشتری")
        self.email_enabled.setChecked(True)

        self.additional_emails = QLineEdit()
        self.additional_emails.setPlaceholderText("ایمیل‌های اضافی (جدا شده با کاما)")

        self.email_subject = QLineEdit()
        self.email_subject.setText("فاکتور ترجمه - دارالترجمه")

        self.email_message = QTextEdit()
        self.email_message.setPlaceholderText("متن پیام ایمیل...")
        self.email_message.setMaximumHeight(100)

        email_layout.addWidget(self.email_enabled)
        email_layout.addWidget(QLabel("ایمیل‌های اضافی:"))
        email_layout.addWidget(self.additional_emails)
        email_layout.addWidget(QLabel("موضوع:"))
        email_layout.addWidget(self.email_subject)
        email_layout.addWidget(QLabel("متن پیام:"))
        email_layout.addWidget(self.email_message)

        # Social media sharing
        social_group = QGroupBox("اشتراک‌گذاری در شبکه‌های اجتماعی")
        social_layout = QVBoxLayout(social_group)

        self.whatsapp_enabled = QCheckBox("ارسال به واتساپ")
        self.telegram_enabled = QCheckBox("ارسال به تلگرام")
        self.sms_enabled = QCheckBox("ارسال پیامک")

        social_layout.addWidget(self.whatsapp_enabled)
        social_layout.addWidget(self.telegram_enabled)
        social_layout.addWidget(self.sms_enabled)

        # Quick message templates
        templates_label = QLabel("قالب‌های پیام سریع:")
        templates_label.setFont(self._get_font(10, bold=True))
        social_layout.addWidget(templates_label)

        self.message_templates = QComboBox()
        self.message_templates.addItems([
            "فاکتور شما آماده شد",
            "مدارک شما در حال ترجمه است",
            "لطفاً برای دریافت مراجعه کنید"
        ])
        social_layout.addWidget(self.message_templates)

        sharing_layout.addWidget(email_group)
        sharing_layout.addWidget(social_group)
        step5_layout.addLayout(sharing_layout)

        # Final actions
        actions_group = QGroupBox("عملیات نهایی")
        actions_layout = QHBoxLayout(actions_group)

        self.send_now_btn = QPushButton("🚀 ارسال فوری")
        self.schedule_send_btn = QPushButton("⏰ زمان‌بندی ارسال")
        self.save_draft_btn = QPushButton("💾 ذخیره پیش‌نویس")

        for btn in [self.send_now_btn, self.schedule_send_btn, self.save_draft_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            actions_layout.addWidget(btn)

        step5_layout.addWidget(actions_group)
        step5_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_widget.addWidget(step5_widget)

    def _create_navigation_buttons(self):
        """Create navigation buttons for wizard."""
        self.navigation_frame = QFrame()
        self.navigation_frame.setObjectName("navigation_frame")
        self.navigation_frame.setMaximumHeight(80)
        self.navigation_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        nav_layout = QHBoxLayout(self.navigation_frame)
        nav_layout.setContentsMargins(30, 15, 30, 15)

        # Back button
        self.back_button = QPushButton("← قبلی")
        self.back_button.setObjectName("back_button")
        self.back_button.setMinimumSize(QSize(120, 40))
        self.back_button.setFont(self._get_font(11, bold=True))
        self.back_button.setEnabled(False)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:enabled {
                background-color: #007bff;
            }
            QPushButton:enabled:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)

        nav_layout.addWidget(self.back_button)

        # Step indicator
        self.step_indicator = QLabel("مرحله 1 از 5")
        self.step_indicator.setFont(self._get_font(12, bold=True))
        self.step_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_indicator.setStyleSheet("color: #495057;")

        nav_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        nav_layout.addWidget(self.step_indicator)
        nav_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Next/Finish button
        self.next_button = QPushButton("بعدی →")
        self.next_button.setObjectName("next_button")
        self.next_button.setMinimumSize(QSize(120, 40))
        self.next_button.setFont(self._get_font(11, bold=True))
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)

        nav_layout.addWidget(self.next_button)

    def _connect_signals(self):
        """Connect all signals and slots."""
        # Navigation buttons
        self.back_button.clicked.connect(self._go_back)
        self.next_button.clicked.connect(self._go_next)

        # Step 2 - Documents
        if hasattr(self, 'add_document_btn'):
            # This would be connected to add document functionality
            pass

        # Step 4 - Preview
        self.refresh_preview_btn.clicked.connect(self._refresh_preview)
        self.save_pdf_btn.clicked.connect(self._save_pdf)
        self.print_preview_btn.clicked.connect(self._print_preview)
        self.paper_size.currentTextChanged.connect(self._update_preview_size)

        # Step 5 - Sharing
        self.send_now_btn.clicked.connect(self._send_invoice)
        self.schedule_send_btn.clicked.connect(self._schedule_send)
        self.save_draft_btn.clicked.connect(self._save_draft)

    def _go_next(self):
        """Navigate to next step."""
        if self.current_step < 4:  # 0-4 (5 steps total)
            # Validate current step before proceeding
            if self._validate_current_step():
                self._save_current_step_data()
                self.current_step += 1
                self._switch_to_step(self.current_step)
                self.step_changed.emit(self.current_step)
        else:
            # Last step - finish wizard
            self._finish_wizard()

    def _go_back(self):
        """Navigate to previous step."""
        if self.current_step > 0:
            self._save_current_step_data()
            self.current_step -= 1
            self._switch_to_step(self.current_step)
            self.step_changed.emit(self.current_step)

    def _switch_to_step(self, step_index):
        """Switch to specified step and update UI."""
        self.stacked_widget.setCurrentIndex(step_index)
        self._update_progress_indicator(step_index)
        self._update_navigation_buttons(step_index)
        self._update_step_indicator(step_index)

    def _update_progress_indicator(self, current_step):
        """Update progress indicator based on current step."""
        for i, (circle, label) in enumerate(self.step_labels):
            if i < current_step:
                # Completed step
                circle.setStyleSheet(self._get_step_circle_style(False, True))
                label.setStyleSheet("color: #28a745; font-weight: bold;")
            elif i == current_step:
                # Current step
                circle.setStyleSheet(self._get_step_circle_style(True, False))
                label.setStyleSheet("color: #007bff; font-weight: bold;")
            else:
                # Future step
                circle.setStyleSheet(self._get_step_circle_style(False, False))
                label.setStyleSheet("color: #6c757d;")

    def _update_navigation_buttons(self, step_index):
        """Update navigation buttons based on current step."""
        # Back button
        self.back_button.setEnabled(step_index > 0)

        # Next/Finish button
        if step_index == 4:  # Last step
            self.next_button.setText("🎉 تکمیل ویزارد")
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
        else:
            self.next_button.setText("بعدی →")
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)

    def _update_step_indicator(self, step_index):
        """Update step indicator text."""
        self.step_indicator.setText(f"مرحله {step_index + 1} از 5")

    def _validate_current_step(self):
        """Validate current step data."""
        if self.current_step == 0:  # CustomerModel info
            return bool(self.customer_name.text().strip())
        elif self.current_step == 1:  # Documents
            return self.documents_table.rowCount() > 0
        elif self.current_step == 2:  # Invoice details
            return bool(self.receipt_number.text().strip())
        elif self.current_step == 3:  # Preview
            return True  # Preview step doesn't require validation
        elif self.current_step == 4:  # Sharing
            return True  # Sharing step doesn't require validation
        return True

    def _save_current_step_data(self):
        """Save current step data to wizard_data."""
        if self.current_step == 0:  # CustomerModel info
            self.wizard_data['customer'] = {
                'name': self.customer_name.text(),
                'national_id': self.customer_national_id.text(),
                'phone': self.customer_phone.text(),
                'email': self.customer_email.text(),
                'address': self.customer_address.toPlainText()
            }
        elif self.current_step == 1:  # Documents
            documents = []
            for row in range(self.documents_table.rowCount()):
                doc = {}
                for col in range(self.documents_table.columnCount()):
                    item = self.documents_table.item(row, col)
                    if item:
                        doc[f'col_{col}'] = item.text()
                documents.append(doc)
            self.wizard_data['documents'] = documents
        elif self.current_step == 2:  # Invoice details
            self.wizard_data['invoice_details'] = {
                'receipt_number': self.receipt_number.text(),
                'receive_date': self.receive_date.date().toString(),
                'delivery_date': self.delivery_date.date().toString(),
                'username': self.username.text(),
                'total_amount': self.total_amount.value(),
                'discount_amount': self.discount_amount.value(),
                'advance_payment': self.advance_payment.value(),
                'remarks': self.remarks_text.toPlainText()
            }
        elif self.current_step == 3:  # Preview
            self.wizard_data['preview_settings'] = {
                'paper_size': self.paper_size.currentText()
            }
        elif self.current_step == 4:  # Sharing
            self.wizard_data['sharing_options'] = {
                'email_enabled': self.email_enabled.isChecked(),
                'additional_emails': self.additional_emails.text(),
                'email_subject': self.email_subject.text(),
                'email_message': self.email_message.toPlainText(),
                'whatsapp_enabled': self.whatsapp_enabled.isChecked(),
                'telegram_enabled': self.telegram_enabled.isChecked(),
                'sms_enabled': self.sms_enabled.isChecked()
            }

        # Emit step completed signal
        self.step_completed.emit(self.current_step, self.wizard_data)

    def _finish_wizard(self):
        """Finish the wizard and emit completion signal."""
        self._save_current_step_data()
        self.wizard_finished.emit(self.wizard_data)

    def _refresh_preview(self):
        """Refresh the invoice preview."""
        # This would update the preview with current data
        self._update_preview_content()

    def _update_preview_content(self):
        """Update preview content with current wizard data."""
        # This would be implemented to update the preview widget
        # with actual data from the wizard steps
        pass

    def _update_preview_size(self, size):
        """Update preview widget size based on paper size selection."""
        if size == "A4":
            self.preview_widget.setFixedSize(595, 842)  # A4 at 72 DPI
        elif size == "A5":
            self.preview_widget.setFixedSize(420, 595)  # A5 at 72 DPI
        elif size == "Letter":
            self.preview_widget.setFixedSize(612, 792)  # Letter at 72 DPI

    def _save_pdf(self):
        """Save invoice as PDF."""
        # This would implement PDF saving functionality
        pass

    def _print_preview(self):
        """Print the invoice preview."""
        # This would implement printing functionality
        pass

    def _send_invoice(self):
        """Send invoice immediately."""
        # This would implement immediate sending functionality
        pass

    def _schedule_send(self):
        """Schedule invoice sending."""
        # This would implement scheduling functionality
        pass

    def _save_draft(self):
        """Save invoice as draft."""
        # This would implement draft saving functionality
        pass

    def reset_wizard(self):
        """Reset the entire wizard to initial state."""
        self.current_step = 0
        self.wizard_data = {
            'customer': {},
            'documents': {},
            'invoice_details': {},
            'preview_settings': {},
            'sharing_options': {}
        }

        # Reset all form fields
        self.customer_name.clear()
        self.customer_national_id.clear()
        self.customer_phone.clear()
        self.customer_email.clear()
        self.customer_address.clear()

        self.documents_table.setRowCount(0)

        self.receipt_number.clear()
        self.receive_date.setDate(QDate.currentDate())
        self.delivery_date.setDate(QDate.currentDate().addDays(7))
        self.username.clear()
        self.total_amount.setValue(0)
        self.discount_amount.setValue(0)
        self.advance_payment.setValue(0)
        self.remarks_text.clear()

        self.additional_emails.clear()
        self.email_subject.setText("فاکتور ترجمه - دارالترجمه")
        self.email_message.clear()

        # Reset checkboxes
        self.email_enabled.setChecked(True)
        self.whatsapp_enabled.setChecked(False)
        self.telegram_enabled.setChecked(False)
        self.sms_enabled.setChecked(False)

        # Switch to first step
        self._switch_to_step(0)

    def get_wizard_data(self):
        """Get complete wizard data."""
        self._save_current_step_data()
        return self.wizard_data

    def set_wizard_data(self, data):
        """Set wizard data (for loading existing invoice)."""
        self.wizard_data = data

        # Populate form fields with data
        if 'customer' in data:
            customer = data['customer']
            self.customer_name.setText(customer.get('name', ''))
            self.customer_national_id.setText(customer.get('national_id', ''))
            self.customer_phone.setText(customer.get('phone', ''))
            self.customer_email.setText(customer.get('email', ''))
            self.customer_address.setPlainText(customer.get('address', ''))

        # Similar population for other steps...
        # This would be expanded to populate all form fields

    @staticmethod
    def _get_font(size=10, bold=False):
        """Get standard font for the application."""
        font = QFont("IRANSans")
        font.setPointSize(size)
        if bold:
            font.setBold(True)
        return font


# Example usage and testing widget
class InvoiceWizardTestWindow(QWidget):
    """Test window to demonstrate the invoice wizard."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("تست ویزارد ساخت فاکتور")
        self.setGeometry(100, 100, 1200, 900)

        layout = QVBoxLayout(self)

        self.wizard = InvoiceWizardUI()
        layout.addWidget(self.wizard)

        # Connect wizard signals
        self.wizard.step_completed.connect(self.on_step_completed)
        self.wizard.wizard_finished.connect(self.on_wizard_finished)
        self.wizard.step_changed.connect(self.on_step_changed)

    def on_step_completed(self, step_index, step_data):
        """Handle step completion."""
        print(f"مرحله {step_index + 1} تکمیل شد")
        print(f"داده‌ها: {step_data}")

    def on_wizard_finished(self, complete_data):
        """Handle wizard completion."""
        print("ویزارد تکمیل شد!")
        print("داده‌های کامل:", complete_data)

    def on_step_changed(self, step_index):
        """Handle step change."""
        print(f"تغییر به مرحله {step_index + 1}")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Set RTL layout direction for Persian text
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    window = InvoiceWizardUI()
    window.show()

    sys.exit(app.exec())