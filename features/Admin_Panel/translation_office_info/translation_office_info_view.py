# features/Admin_Panel/translation_office_info/translation_office_info_view.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt
from shared.orm_models.users_models import TranslationOfficeData


class TranslationOfficeInfoView(QWidget):
    """
    A view to display read-only information about the translation office.
    It has no knowledge of the underlying logic or data source.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TranslationOfficeInfoView")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Fields ---
        self.office_name_input = QLineEdit()
        self.office_name_input.setReadOnly(True)

        self.registration_number_input = QLineEdit()
        self.registration_number_input.setReadOnly(True)

        form_layout.addRow(QLabel("نام دارالترجمه:"), self.office_name_input)
        form_layout.addRow(QLabel("شماره ثبت:"), self.registration_number_input)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

    def display_info(self, data: TranslationOfficeData):
        """
        Populates the view's fields with data from the provided DTO.
        This method is called by the controller.
        """
        self.office_name_input.setText(data.name)
        self.registration_number_input.setText(data.reg_no)
