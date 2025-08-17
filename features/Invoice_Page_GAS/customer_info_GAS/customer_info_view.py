# view.py
from PySide6.QtWidgets import (
    QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QCompleter,
    QScrollArea, QGroupBox, QSpacerItem
)
from PySide6.QtGui import QIntValidator, QFont
from PySide6.QtCore import QStringListModel, Qt, QTimer, Signal

from features.Invoice_Page_GAS.customer_info_GAS.customer_info_models import Customer
from features.Invoice_Page_GAS.customer_info_GAS.customer_info_qss_styles import (CUSTOMER_INFO_STYLES,
                                                                                  BASE_LINEEDIT_STYLE,
                                                                                  VALID_LINEEDIT_STYLE,
                                                                                  INVALID_LINEEDIT_STYLE)
from shared.utils.validation_utils import (validate_national_id, validate_email, validate_phone_number)
from shared import to_persian_number, show_error_message_box, show_information_message_box, show_question_message_box


class CustomerInfoWidget(QWidget):
    save_requested = Signal(dict)
    fetch_customer_details_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("CustomerInfoWidget")
        self.setWindowTitle("فرم اطلاعات مشتریان")
        self.setGeometry(100, 100, 1200, 800)

        # Set stylesheets
        self.setStyleSheet(CUSTOMER_INFO_STYLES)
        self.setFont(QFont("IranSANS", 11))

        # To map customer names from the completer back to their national IDs
        self.completer_map = {}

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # --- Customer Info Section ---
        self._setup_customer_fields()

        # --- Companions Section ---
        self._setup_companions_section()
        self.main_layout.addStretch(1)

        # --- Action Buttons ---
        self._setup_action_buttons()

        # --- Initial Setup ---
        self.clear_form()

    def _setup_customer_fields(self):
        customer_group = QGroupBox("اطلاعات مشتری اصلی")
        grid_layout = QGridLayout(customer_group)
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(15, 15, 15, 15)

        # --- Create Widgets ---
        self.name_edit = QLineEdit()
        self.national_id_edit = QLineEdit()
        self.national_id_edit.setValidator(QIntValidator())
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()

        # --- Create validated field containers using the new helper method ---
        name_container, self.name_error_label = self._create_validated_field_widget(self.name_edit)
        nid_container, self.nid_error_label = self._create_validated_field_widget(self.national_id_edit)
        phone_container, self.phone_error_label = self._create_validated_field_widget(self.phone_edit)
        email_container, self.email_error_label = self._create_validated_field_widget(self.email_edit)

        # --- Connect signals for real-time validation ---
        self.name_edit.textChanged.connect(self._validate_name)
        self.national_id_edit.textChanged.connect(self._validate_nid)
        self.phone_edit.textChanged.connect(self._validate_phone)
        self.email_edit.textChanged.connect(self._validate_email)

        # --- Add Widgets to Grid ---
        # Row 0
        grid_layout.addWidget(QLabel("نام و نام خانوادگی:"), 0, 0, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(name_container, 0, 1)
        grid_layout.addWidget(QLabel("کد ملی:"), 0, 2, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(nid_container, 0, 3)

        # Row 1
        grid_layout.addWidget(QLabel("شماره تماس:"), 1, 0, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(phone_container, 1, 1)
        grid_layout.addWidget(QLabel("ایمیل (اختیاری):"), 1, 2, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(email_container, 1, 3)

        # Row 2: Address spans all columns
        grid_layout.addWidget(QLabel("آدرس:"), 2, 0, Qt.AlignmentFlag.AlignTop)
        grid_layout.addWidget(self.address_edit, 2, 1, 1, 3)

        # --- Make layout responsive ---
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        grid_layout.setColumnMinimumWidth(0, 120)
        grid_layout.setColumnMinimumWidth(2, 120)

        self.main_layout.addWidget(customer_group)

    def _create_validated_field_widget(self, line_edit: QLineEdit) -> (QWidget, QLabel):
        container = QWidget()

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(line_edit)

        error_label = QLabel()
        error_label.setStyleSheet("color: #dc3545; font-family: IranSANS; font-size: 9pt;")
        error_label.setVisible(False)
        layout.addWidget(error_label)

        return container, error_label

    def add_companion_fields(self, name="", national_id=""):
        """Adds a new, compact set of fields for one companion."""
        companion_number = self.companions_layout.count() + 1
        companion_group = QGroupBox(f"اطلاعات همراه {to_persian_number(companion_number)}")
        companion_group.setObjectName("CompanionGroup")

        layout = QGridLayout(companion_group)
        name_edit = QLineEdit(name)
        nid_edit = QLineEdit(str(national_id) if national_id else "")
        nid_edit.setValidator(QIntValidator())
        remove_button = QPushButton("×")
        remove_button.setObjectName("RemoveButton")

        name_container, name_error_label = self._create_validated_field_widget(name_edit)
        nid_container, nid_error_label = self._create_validated_field_widget(nid_edit)

        # Add all widgets to row 0
        layout.addWidget(QLabel("نام کامل:"), 0, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(name_container, 0, 1)
        layout.addWidget(QLabel("کد ملی:"), 0, 2, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(nid_container, 0, 3)
        layout.addWidget(remove_button, 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)

        # Set horizontal stretch for the input fields
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        # --- NEW: Add vertical stretch INSIDE the group box ---
        # This forces the content in row 0 to the top, preventing vertical stretching.
        layout.setRowStretch(1, 1)

        # Connect signals for validation
        name_edit.textChanged.connect(
            lambda text, le=name_edit, el=name_error_label: self._set_field_state(
                le, el, "valid") if text else self._clear_field_state(le, el))
        nid_edit.textChanged.connect(
            lambda text, le=nid_edit, el=nid_error_label: self._validate_companion_nid(le, el, text))

        # Connect the remove button
        remove_button.clicked.connect(lambda: self._remove_companion(companion_group))

        self.companions_layout.addWidget(companion_group)

    # --- VISUAL VALIDATION SYSTEM (REVISED) ---
    def _set_field_state(self, line_edit: QLineEdit, error_label: QLabel, state: str, message: str = None):
        """A generic function to set the visual state of a field."""
        if state == "valid":
            line_edit.setStyleSheet(VALID_LINEEDIT_STYLE)
            error_label.setVisible(False)
        elif state == "invalid" and message:
            line_edit.setStyleSheet(INVALID_LINEEDIT_STYLE)
            error_label.setText(message)
            error_label.setVisible(True)
        else:  # "neutral" or default state
            line_edit.setStyleSheet(BASE_LINEEDIT_STYLE)
            error_label.setVisible(False)

    def _clear_field_state(self, line_edit: QLineEdit, error_label: QLabel):
        self._set_field_state(line_edit, error_label, "neutral")

    def _validate_name(self, text):
        if len(text) >= 3:
            self._set_field_state(self.name_edit, self.name_error_label, "valid")
            return True
        elif not text:
            self._clear_field_state(self.name_edit, self.name_error_label)
            return False
        else:
            self._set_field_state(self.name_edit, self.name_error_label, "invalid", "نام باید حداقل ۳ حرف باشد")
            return False

    def _validate_nid(self, text):
        if validate_national_id(text):
            self._set_field_state(self.national_id_edit, self.nid_error_label, "valid")
            return True
        elif not text:
            self._clear_field_state(self.national_id_edit, self.nid_error_label)
            return False
        else:
            self._set_field_state(self.national_id_edit, self.nid_error_label, "invalid", "کد ملی معتبر نیست")
            return False

    def _validate_phone(self, text):
        if validate_phone_number(text):
            self._set_field_state(self.phone_edit, self.phone_error_label, "valid")
            return True
        elif not text:
            self._clear_field_state(self.phone_edit, self.phone_error_label)
            return False
        else:
            self._set_field_state(self.phone_edit, self.phone_error_label, "invalid", "شماره تماس معتبر نیست")
            return False

    def _validate_email(self, text):
        if not text:
            self._clear_field_state(self.email_edit, self.email_error_label)
            return True
        if validate_email(text):
            self._set_field_state(self.email_edit, self.email_error_label, "valid")
            return True
        else:
            self._set_field_state(self.email_edit, self.email_error_label, "invalid", "فرمت ایمیل صحیح نیست")
            return False

    def _validate_companion_nid(self, line_edit, error_label, text):
        if validate_national_id(text):
            self._set_field_state(line_edit, error_label, "valid")
        elif not text:
            self._clear_field_state(line_edit, error_label)
        else:
            self._set_field_state(line_edit, error_label, "invalid", "کد ملی معتبر نیست")

    def _validate_form(self):
        # Trigger validation for all fields to show errors if fields were not touched
        is_name_valid = self._validate_name(self.name_edit.text())
        is_nid_valid = self._validate_nid(self.national_id_edit.text())
        is_phone_valid = self._validate_phone(self.phone_edit.text())
        is_email_valid = self._validate_email(self.email_edit.text())

        return is_name_valid and is_nid_valid and is_phone_valid and is_email_valid

    def clear_form(self):
        """Clears all input fields and their validation states."""
        for editor in [self.name_edit, self.national_id_edit, self.phone_edit, self.email_edit, self.address_edit]:
            editor.clear()

        # Clear main fields' visual state
        self._clear_field_state(self.name_edit, self.name_error_label)
        self._clear_field_state(self.national_id_edit, self.nid_error_label)
        self._clear_field_state(self.phone_edit, self.phone_error_label)
        self._clear_field_state(self.email_edit, self.email_error_label)

        self._clear_companion_widgets()
        self.companions_checkbox.setChecked(False)

    def _style_line_edit(self, line_edit):
        """Helper to re-apply stylesheet to update property-based styles."""
        line_edit.style().unpolish(line_edit)
        line_edit.style().polish(line_edit)

    def _setup_companions_section(self):
        self.companions_checkbox = QCheckBox("آیا مشتری همراه دارد؟")
        self.companions_checkbox.stateChanged.connect(self.toggle_companions_ui)
        self.main_layout.addWidget(self.companions_checkbox)

        self.companions_area = QScrollArea()
        self.companions_widget = QWidget()
        self.companions_layout = QVBoxLayout(self.companions_widget)
        self.companions_area.setWidget(self.companions_widget)
        self.companions_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.companions_area)
        self.companions_area.setVisible(False)

        self.add_companion_button = QPushButton("افزودن همراه")
        self.add_companion_button.clicked.connect(lambda: self.add_companion_fields())
        self.main_layout.addWidget(self.add_companion_button)
        self.add_companion_button.setVisible(False)

    def populate_completer(self, customer_info: list[dict]):
        """Public slot to receive completer data and set up the completer."""
        self.completer_map = {info['name']: info['national_id'] for info in customer_info}
        model = QStringListModel(list(self.completer_map.keys()))
        completer = QCompleter(model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_edit.setCompleter(completer)
        # When a name is activated, find its ID and emit a signal asking for details
        completer.activated.connect(self._on_completer_activated)

    def _on_completer_activated(self, selected_name: str):
        """Internal handler to emit the fetch request signal."""
        national_id = self.completer_map.get(selected_name)
        if national_id:
            self.fetch_customer_details_requested.emit(national_id)

    # This method will be called by the controller after it fetches the data
    def display_customer_details(self, customer: Customer):
        """Public slot to pre-fill the form with a Customer object's data."""
        # This flag prevents validation signals from firing while we programmatically set text
        self._is_autofilling = True

        self.clear_form()  # Start with a clean slate
        self.name_edit.setText(customer.name)
        self.national_id_edit.setText(customer.national_id)
        self.phone_edit.setText(customer.phone)
        self.email_edit.setText(customer.email or "")
        self.address_edit.setText(customer.address or "")

        if customer.companions:
            for comp in customer.companions:
                self.add_companion_fields(comp.name, comp.national_id)
            self.companions_checkbox.setChecked(True)

        self._is_autofilling = False

    # def load_completer_data(self):
    #     """Fetches customer names and IDs to populate the autofill completer."""
    #     self.completer_map = {info['name']: info['national_id'] for info in customer_info}
    #
    #     model = QStringListModel(list(self.completer_map.keys()))
    #
    #     completer = QCompleter(model, self)
    #     completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    #     self.name_edit.setCompleter(completer)
    #
    #     # Connect the completer's 'activated' signal to the autofill slot
    #     completer.activated.connect(self.autofill_customer_data)
    #
    # def display_customer_details(self, customer: Customer):
    #     """Public slot to pre-fill the form with data."""
    #     self.name_edit.setText(customer.name)
    #     self.national_id_edit.setText(customer.national_id)
    #     # ... (fill all other fields)
    #
    # def autofill_customer_data(self, selected_name: str):
    #     """Fills the form with data of the customer selected from the completer."""
    #     national_id = self.completer_map.get(selected_name)
    #     if not national_id:
    #         return
    #
    #     customer = self.controller.get_customer_details(national_id)
    #     if customer:
    #         # Clear all fields first to ensure a clean slate
    #         self.clear_form()
    #
    #         # Fill the main customer fields
    #         self.national_id_edit.setText(str(customer.national_id))
    #         self.name_edit.setText(customer.name)
    #         self.phone_edit.setText(customer.phone)
    #         self.email_edit.setText(customer.email or "")
    #         self.address_edit.setText(customer.address or "")
    #
    #         # --- REVISED LOGIC FOR ROBUSTNESS ---
    #         if customer.companions:
    #             # 1. Add all the companion data fields FIRST.
    #             for comp in customer.companions:
    #                 self.add_companion_fields(comp.name, comp.national_id)
    #
    #             # 2. THEN, check the box. This will trigger toggle_companions_ui,
    #             # but the check to add a default field will fail because the
    #             # layout is no longer empty, which is the correct behavior.
    #             self.companions_checkbox.setChecked(True)
    #         else:
    #             # Ensure the box is unchecked if there are no companions.
    #             self.companions_checkbox.setChecked(False)

    def toggle_companions_ui(self, state):
        """
        Shows or hides the companion section, manages the layout stretch,
        and adds a default companion field when checked.
        """
        is_visible = bool(state)
        self.companions_area.setVisible(is_visible)
        self.add_companion_button.setVisible(is_visible)

        if is_visible:
            self._remove_stretch()
            # This runs only when the user checks the box, not during autofill,
            # because autofill adds fields *before* checking the box.
            if self.companions_layout.count() == 0:
                self.add_companion_fields()
        else:
            self._add_stretch_before_buttons()

        if not is_visible:
            self._clear_companion_widgets()

    def _add_stretch_before_buttons(self):
        """Adds a stretch item specifically before the action buttons layout."""
        # Defensively remove any existing stretch to avoid duplicates
        self._remove_stretch()

        # Find the index of our button layout
        index = self.main_layout.indexOf(self.buttons_layout)

        # Insert a stretch item at that specific index
        if index != -1:
            self.main_layout.insertStretch(index, 1)

    def _remove_stretch(self):
        """Finds and removes any stretch item from the main layout."""
        for i in range(self.main_layout.count() - 1, -1, -1):
            item = self.main_layout.itemAt(i)
            if isinstance(item, QSpacerItem):
                self.main_layout.removeItem(item)
                return

    def _remove_companion(self, group_box_to_remove: QGroupBox):
        group_box_to_remove.deleteLater()
        QTimer.singleShot(0, self._refresh_companion_numbers)

    def _refresh_companion_numbers(self):
        for i in range(self.companions_layout.count()):
            widget = self.companions_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                widget.setTitle(f"اطلاعات همراه {i + 1}")

    def _setup_action_buttons(self):
        # This layout is now stored as a class attribute to find its position later
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(10)

        self.save_button = QPushButton("ذخیره مشتری")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self._on_save_clicked)

        self.clear_button = QPushButton("پاک کردن فرم")
        self.clear_button.clicked.connect(self.clear_form)

        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.clear_button)
        self.buttons_layout.addWidget(self.save_button)

        # Add the button layout to the main layout
        self.main_layout.addLayout(self.buttons_layout)

    def _on_save_clicked(self):
        """Gathers raw text from all fields and emits the save_requested signal."""
        companions = []
        # Find all companion groups and get their raw text
        for group_box in self.companions_widget.findChildren(QGroupBox, "CompanionGroup"):
            line_edits = group_box.findChildren(QLineEdit)
            if len(line_edits) == 2:
                companions.append({
                    "name": line_edits[0].text(),
                    "national_id": line_edits[1].text()
                })

        # Package all raw data into a single dictionary
        raw_data = {
            "name": self.name_edit.text(),
            "national_id": self.national_id_edit.text(),
            "phone": self.phone_edit.text(),
            "email": self.email_edit.text(),
            "address": self.address_edit.text(),
            "companions": companions
        }

        # Emit the signal with the raw data for the logic layer to process
        self.save_requested.emit(raw_data)

    def _clear_companion_widgets(self):
        while self.companions_layout.count():
            child = self.companions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_save_success(self, message):
        """Public slot to show a success message."""
        show_information_message_box(self, "موفقیت", message)

    def show_error(self, message: str):
        """Public slot to show an error message."""
        show_error_message_box(self, "خطا", message)

    def show_edit_question(self, message, func):
        """Public slot to show question message box."""
        show_question_message_box(parent=self,
                                  title="ویراش مشتری",
                                  message=message,
                                  button_1="بله",
                                  yes_func=func,
                                  button_2="خیر"
                                  )
