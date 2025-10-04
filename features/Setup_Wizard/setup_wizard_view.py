# features/Setup_Wizard/setup_wizard_view.py

from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, QFormLayout, QMessageBox,
                               QGridLayout, QCheckBox, QComboBox)
from PySide6.QtCore import Signal, Qt
from features.Setup_Wizard.setup_wizard_models import (LicenseDTO, TranslationOfficeDTO, AdminUserDTO,
                                                       AdminProfileDTO, WizardStep)

from typing import Callable


SECURITY_QUESTIONS = [
    "نام اولین معلم شما چه بود؟",
    "نام خانوادگی مادر شما چیست؟",
    "در کدام شهر متولد شده اید؟",
    "غذای مورد علاقه شما چیست؟",
    "بهترین دوست دوران کودکی شما که بود؟",
    "الگوی شما در زندگی چه کسی است؟",
    "یک عدد سه رقمی انتخاب کنید",
]


class LicensePage(QWizardPage):
    submit_license = Signal(LicenseDTO)

    def __init__(self, validator: Callable[[LicenseDTO], bool], parent=None):
        super().__init__(parent)
        self._validator = validator

        self.setTitle("تایید لایسنس")
        self.setSubTitle("لطفا برای شروع، کلید لایسنس محصول را وارد کنید.")

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)

        self.label = QLabel("کلید مجوز:")
        self.license_input = QLineEdit()
        self.license_input.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.label)
        layout.addWidget(self.license_input)
        self.setLayout(layout)

    def validatePage(self):
        dto = LicenseDTO(license_key=self.license_input.text().strip())
        return self._validator(dto)


class OfficeDataPage(QWizardPage):
    submit_office_data = Signal(TranslationOfficeDTO)

    def __init__(self, validator: Callable[[TranslationOfficeDTO], bool], parent=None):
        super().__init__(parent)
        self._validator = validator

        self.setTitle("اطلاعات دفتر ترجمه")
        self.setSubTitle("اطلاعات مربوط به دفتر خود را در این بخش وارد نمایید.")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.name_edit = QLineEdit()
        self.reg_no_edit = QLineEdit()
        self.representative_edit = QLineEdit()
        self.manager_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()

        self.email_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout = QGridLayout(self)

        # Row 0
        layout.addWidget(QLabel("نام دفتر (*):"), 0, 0)
        layout.addWidget(self.name_edit, 0, 1)
        layout.addWidget(QLabel("شماره ثبت:"), 0, 2)
        layout.addWidget(self.reg_no_edit, 0, 3)

        # Row 1
        layout.addWidget(QLabel("مدیر مسئول:"), 1, 0)
        layout.addWidget(self.manager_edit, 1, 1)
        layout.addWidget(QLabel("نماینده:"), 1, 2)
        layout.addWidget(self.representative_edit, 1, 3)

        # Row 2
        layout.addWidget(QLabel("شماره تماس:"), 2, 0)
        layout.addWidget(self.phone_edit, 2, 1)
        layout.addWidget(QLabel("ایمیل:"), 2, 2)
        layout.addWidget(self.email_edit, 2, 3)

        # Row 3 (Address spans all columns)
        layout.addWidget(QLabel("آدرس:"), 3, 0)
        layout.addWidget(self.address_edit, 3, 1, 1, 3)  # widget, row, col, rowspan, colspan

        # Set column stretch to make inputs expand nicely
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

    def validatePage(self):
        """Gathers data from all fields and passes it to the validator."""
        # The 'or None' pattern ensures that empty strings are saved as NULL in the database
        dto = TranslationOfficeDTO(
            name=self.name_edit.text().strip(),
            reg_no=self.reg_no_edit.text().strip() or None,
            representative=self.representative_edit.text().strip() or None,
            manager=self.manager_edit.text().strip() or None,
            address=self.address_edit.text().strip() or None,
            phone=self.phone_edit.text().strip() or None,
            email=self.email_edit.text().strip() or None,
        )
        return self._validator(dto)


class AdminUserPage(QWizardPage):
    def __init__(self, validator: Callable[[AdminUserDTO, AdminProfileDTO], bool], parent=None):
        super().__init__(parent)
        self._validator = validator
        self.setTitle("ایجاد کاربر مدیر و تنظیمات امنیتی")
        self.setSubTitle("رمز عبور و سوالات امنیتی برای بازیابی رمز عبور را مشخص کنید.")

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # --- Create Widgets ---
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_confirm_edit = QLineEdit()
        self.show_password_checkbox = QCheckBox("نمایش رمز عبور")

        self.question1_combo = QComboBox()
        self.answer1_edit = QLineEdit()
        self.question2_combo = QComboBox()
        self.answer2_edit = QLineEdit()

        self.full_name_edit = QLineEdit()
        self.national_id_edit = QLineEdit()
        self.email_edit = QLineEdit()

        # --- Configure Widgets ---
        self.username_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.email_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.question1_combo.addItems(SECURITY_QUESTIONS)
        self.question2_combo.addItems(SECURITY_QUESTIONS)
        self.question2_combo.setCurrentIndex(1)  # Start with a different default question

        # --- Layout ---
        layout = QFormLayout(self)

        layout.addRow("نام کاربری (*):", self.username_edit)
        layout.addRow("رمز عبور (*):", self.password_edit)
        layout.addRow("تکرار رمز عبور (*):", self.password_confirm_edit)
        layout.addRow("", self.show_password_checkbox)

        # Add a separator or label for clarity
        layout.addRow(QLabel("--- سوالات امنیتی (برای بازیابی رمز عبور) ---"))
        layout.addRow("سوال امنیتی ۱ (*):", self.question1_combo)
        layout.addRow("پاسخ سوال ۱ (*):", self.answer1_edit)
        layout.addRow("سوال امنیتی ۲ (*):", self.question2_combo)
        layout.addRow("پاسخ سوال ۲ (*):", self.answer2_edit)

        layout.addRow(QLabel("--- اطلاعات پروفایل (اختیاری) ---"))
        layout.addRow("نام کامل:", self.full_name_edit)
        layout.addRow("کد ملی:", self.national_id_edit)
        layout.addRow("ایمیل:", self.email_edit)

        # --- Connect Signals ---
        self.show_password_checkbox.toggled.connect(self._on_toggle_password_visibility)

    def _on_toggle_password_visibility(self, is_checked: bool):
        """Toggles the echo mode of the password fields based on the checkbox state."""
        # --- FIX 3: The logic is now simpler and more robust ---
        mode = QLineEdit.EchoMode.Normal if is_checked else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.password_confirm_edit.setEchoMode(mode)

    def validatePage(self):
        """Gathers all data from the form and passes it to the validator."""
        user_dto = AdminUserDTO(
            username=self.username_edit.text().strip(),
            password=self.password_edit.text(),
            password_confirm=self.password_confirm_edit.text(),
            security_question_1=self.question1_combo.currentText(),
            security_answer_1=self.answer1_edit.text().strip(),
            security_question_2=self.question2_combo.currentText(),
            security_answer_2=self.answer2_edit.text().strip()
        )
        profile_dto = AdminProfileDTO(
            user_id=0,
            full_name=self.full_name_edit.text().strip() or None,
            national_id=self.national_id_edit.text().strip() or None,
            email=self.email_edit.text().strip() or None
        )
        return self._validator(user_dto, profile_dto)


# --- Main Wizard View with RTL Configuration ---

class SetupWizardView(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("راه اندازی اولیه نرم افزار")

        # --- RTL Change: Set layout for the entire wizard ---
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # --- RTL Change: Translate standard wizard buttons ---
        self.setButtonText(QWizard.WizardButton.BackButton, "قبلی")
        self.setButtonText(QWizard.WizardButton.NextButton, "بعدی")
        self.setButtonText(QWizard.WizardButton.CancelButton, "انصراف")
        self.setButtonText(QWizard.WizardButton.FinishButton, "پایان")

        self.license_page = None
        self.office_page = None
        self.admin_page = None
        self._page_id_map = {}

    def register_validators(self, license_validator, office_validator, admin_validator):
        """Creates the pages and injects the validation logic from the controller."""
        self.license_page = LicensePage(validator=license_validator)
        self.office_page = OfficeDataPage(validator=office_validator)
        self.admin_page = AdminUserPage(validator=admin_validator)

        self._page_id_map = {
            WizardStep.LICENSE: self.addPage(self.license_page),
            WizardStep.TRANSLATION_OFFICE: self.addPage(self.office_page),
            WizardStep.ADMIN_USER: self.addPage(self.admin_page)
        }

    def prepare_to_show_step(self, step: WizardStep):
        """Sets the wizard to the correct starting page before it is shown."""
        page_id = self._page_id_map.get(step)
        if page_id is not None:
            self.setCurrentId(page_id)

    @staticmethod
    def show_error_on_page(page_widget: QWizardPage, message: str):
        """Displays a translated and RTL-aware error message to the user."""
        # --- RTL Change: Configure the message box for RTL ---
        msg_box = QMessageBox(page_widget)
        msg_box.setWindowTitle("خطا")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg_box.exec()

    def advance_page(self):
        """Manually advances the wizard to the next page."""
        self.next()
