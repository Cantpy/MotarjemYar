# features/Invoice_Page/customer_info/customer_info_view.py

from PySide6.QtWidgets import (QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QCheckBox, QCompleter, QScrollArea, QGroupBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Signal, QModelIndex

from features.Invoice_Page.customer_info.customer_info_models import Customer
from features.Invoice_Page.customer_info.customer_info_qss_styles import (CUSTOMER_INFO_STYLES,
                                                                          BASE_LINEEDIT_STYLE,
                                                                          VALID_LINEEDIT_STYLE,
                                                                          INVALID_LINEEDIT_STYLE)
from shared import to_persian_number, show_error_message_box, show_information_message_box, show_question_message_box
from shared.widgets.validators import PersianNIDEdit
from shared.widgets.persian_tools import PhoneLineEdit, EmailLineEdit


class CustomerInfoWidget(QWidget):
    """
    The View in MVC. It is responsible for the UI only.
    - It emits signals on user actions.
    - It has public methods (slots) to be updated by the Controller.
    - It contains no business logic or direct data access.
    """
    # --- Signals ---
    save_requested = Signal(dict)
    fetch_customer_details_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("فرم اطلاعات مشتریان")

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self._setup_customer_fields()
        self._setup_companions_section()
        self.main_layout.addStretch(1)
        self._setup_action_buttons()

    # --- UI Setup Methods ---

    def _setup_customer_fields(self):
        customer_group = QGroupBox("اطلاعات مشتری اصلی")
        grid_layout = QGridLayout(customer_group)

        self.name_edit = QLineEdit()
        self.national_id_edit = PersianNIDEdit()
        self.phone_edit = PhoneLineEdit()
        self.email_edit = EmailLineEdit()
        self.address_edit = QLineEdit()

        name_container, self.name_error_label = self._create_validated_field(self.name_edit)
        nid_container, self.nid_error_label = self._create_validated_field(self.national_id_edit)
        phone_container, self.phone_error_label = self._create_validated_field(self.phone_edit)
        email_container, self.email_error_label = self._create_validated_field(self.email_edit)

        grid_layout.addWidget(QLabel("نام و نام خانوادگی:"), 0, 0)
        grid_layout.addWidget(name_container, 0, 1)
        grid_layout.addWidget(QLabel("کد ملی:"), 0, 2)
        grid_layout.addWidget(nid_container, 0, 3)
        grid_layout.addWidget(QLabel("شماره تماس:"), 1, 0)
        grid_layout.addWidget(phone_container, 1, 1)
        grid_layout.addWidget(QLabel("ایمیل:"), 1, 2)
        grid_layout.addWidget(email_container, 1, 3)
        grid_layout.addWidget(QLabel("آدرس:"), 2, 0)
        grid_layout.addWidget(self.address_edit, 2, 1, 1, 3)

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        self.main_layout.addWidget(customer_group)

    def _setup_companions_section(self):
        self.companions_checkbox = QCheckBox("مشتری همراه دارد")
        self.companions_checkbox.stateChanged.connect(self._toggle_companions_ui)
        self.main_layout.addWidget(self.companions_checkbox)

        self.companions_area = QScrollArea()
        self.companions_widget = QWidget()
        self.companions_layout = QVBoxLayout(self.companions_widget)
        self.companions_area.setWidget(self.companions_widget)
        self.companions_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.companions_area)

        self.add_companion_button = QPushButton("افزودن همراه")
        self.add_companion_button.clicked.connect(lambda: self.add_companion_fields())
        self.main_layout.addWidget(self.add_companion_button)

        self.companions_area.hide()
        self.add_companion_button.hide()

    def _setup_action_buttons(self):
        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("ذخیره مشتری")
        self.save_button.setObjectName("PrimaryButton")
        self.clear_button = QPushButton("پاک کردن فرم")

        self.buttons_layout.addStretch()
        self.buttons_layout.addWidget(self.clear_button)
        self.buttons_layout.addWidget(self.save_button)
        self.main_layout.addLayout(self.buttons_layout)

        # Connect internal signals to internal slots
        self.save_button.clicked.connect(self._on_save_clicked)
        self.clear_button.clicked.connect(self.clear_form)

    # --- Public Methods (Slots for Controller) ---

    def populate_all_completers(self, completer_data: dict):
        """
        REVISED: Populates completers for name, NID, and phone fields.
        'completer_data' is a dict like {'names': [...], 'nids': [...], 'phones': [...]}
        """
        self._create_completer(self.name_edit, completer_data.get('names', []))
        self._create_completer(self.national_id_edit, completer_data.get('nids', []))
        self._create_completer(self.phone_edit, completer_data.get('phones', []))

    def display_customer_details(self, customer: Customer):
        """Populates the form with data from a Customer DTO."""
        print(f"customer selected to be autofilled by view: {customer}")
        self.clear_form()
        self.name_edit.setText(customer.name)
        self.national_id_edit.setText(str(customer.national_id))
        self.phone_edit.setText(customer.phone)
        self.email_edit.setText(customer.email or "")
        self.address_edit.setText(customer.address or "")

        if customer.companions:
            for comp in customer.companions:
                self.add_companion_fields(comp.name, comp.national_id)
            self.companions_checkbox.setChecked(True)

    def display_validation_results(self, errors: dict[str, str]):
        """Applies visual feedback based on a dictionary of validation errors."""
        # Reset all fields to neutral
        self._set_field_state(self.name_edit, self.name_error_label, "neutral")
        self._set_field_state(self.national_id_edit, self.nid_error_label, "neutral")
        self._set_field_state(self.phone_edit, self.phone_error_label, "neutral")
        self._set_field_state(self.email_edit, self.email_error_label, "neutral")

        # Apply invalid states
        if 'name' in errors:
            self._set_field_state(self.name_edit, self.name_error_label, "invalid", errors['name'])
        if 'national_id' in errors:
            self._set_field_state(self.national_id_edit, self.nid_error_label, "invalid", errors['national_id'])
        if 'phone' in errors:
            self._set_field_state(self.phone_edit, self.phone_error_label, "invalid", errors['phone'])
        if 'email' in errors:
            self._set_field_state(self.email_edit, self.email_error_label, "invalid", errors['email'])
        if 'companions' in errors:
            self.show_error(errors['companions'])

    def get_current_data(self) -> dict:
        """Gathers all data from the form fields into a dictionary."""
        companions = []
        for group_box in self.companions_widget.findChildren(QGroupBox):
            line_edits = group_box.findChildren(QLineEdit)
            if len(line_edits) == 2:
                companions.append({
                    "name": line_edits[0].text(),
                    "national_id": line_edits[1].text()
                })
        return {
            "name": self.name_edit.text(),
            "national_id": self.national_id_edit.text(),
            "phone": self.phone_edit.text(),
            "email": self.email_edit.text(),
            "address": self.address_edit.text(),
            "companions": companions
        }

    def clear_form(self):
        """Clears all input fields and validation states."""
        for editor in [self.name_edit, self.national_id_edit, self.phone_edit, self.email_edit, self.address_edit]:
            editor.clear()

        self.display_validation_results({})  # Clear all error styles
        self._clear_companion_widgets()
        self.companions_checkbox.setChecked(False)

    def show_save_success(self, message: str):
        show_information_message_box(self, "موفقیت", message)

    def show_error(self, message: str):
        show_error_message_box(self, "خطا", message)

    def show_edit_question(self, message: str, yes_callback):
        show_question_message_box(
            parent=self,
            title="ویرایش مشتری",
            message=message,
            yes_func=yes_callback,
            button_1="بله",
            button_2="خیر"
        )

    def add_companion_fields(self, name="", national_id=""):
        """Adds a new set of fields for one companion."""
        companion_number = self.companions_layout.count() + 1
        group_box = QGroupBox(f"اطلاعات همراه {to_persian_number(companion_number)}")

        layout = QGridLayout(group_box)
        name_edit = QLineEdit(name)
        nid_edit = PersianNIDEdit(national_id)
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)

        layout.addWidget(QLabel("نام:"), 0, 0)
        layout.addWidget(name_edit, 0, 1)
        layout.addWidget(QLabel("کد ملی:"), 0, 2)
        layout.addWidget(nid_edit, 0, 3)
        layout.addWidget(remove_btn, 0, 4)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        remove_btn.clicked.connect(lambda: group_box.deleteLater())
        self.companions_layout.addWidget(group_box)

    # --- Internal Helper Methods & Slots ---

    def _create_completer(self, line_edit: QLineEdit, data: list[dict]):
        """
        Creates, configures, and attaches a QCompleter to a line edit.
        """
        model = QStandardItemModel(self)
        for item_data in data:
            item = QStandardItem(str(item_data["display"]))
            item.setData(item_data["lookup_id"], Qt.ItemDataRole.UserRole)
            model.appendRow(item)

        completer = QCompleter(model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        line_edit.setCompleter(completer)

        completer.activated[QModelIndex].connect(self._on_completer_activated)

    def _on_save_clicked(self):
        """Internal slot that emits the public save_requested signal."""
        raw_data = self.get_current_data()
        self.save_requested.emit(raw_data)

    def _on_completer_activated(self, index: QModelIndex):
        """
        This single slot handles activation from ANY completer.
        It emits the public signal for the Controller to handle.
        """
        national_id = index.data(Qt.ItemDataRole.UserRole)
        print(f"national id taken from view to pass to the controller: {national_id}")

        if national_id:
            self.fetch_customer_details_requested.emit(str(national_id))

    def _toggle_companions_ui(self, state):
        is_visible = bool(state)
        self.companions_area.setVisible(is_visible)
        self.add_companion_button.setVisible(is_visible)
        if is_visible and self.companions_layout.count() == 0:
            self.add_companion_fields()
        elif not is_visible:
            self._clear_companion_widgets()

    def _create_validated_field(self, line_edit: QLineEdit) -> tuple[QWidget, QLabel]:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        error_label = QLabel()
        error_label.setStyleSheet("color: #dc3545; font-size: 9pt;")
        error_label.hide()
        layout.addWidget(line_edit)
        layout.addWidget(error_label)
        return container, error_label

    def _set_field_state(self, line_edit: QLineEdit, error_label: QLabel, state: str, message: str = ""):
        if state == "invalid":
            line_edit.setStyleSheet(INVALID_LINEEDIT_STYLE)
            error_label.setText(message)
            error_label.show()
        else:  # "neutral"
            line_edit.setStyleSheet(BASE_LINEEDIT_STYLE)
            error_label.hide()

    def _clear_companion_widgets(self):
        while (item := self.companions_layout.takeAt(0)) is not None:
            if item.widget():
                item.widget().deleteLater()


# # features/Invoice_Page/customer_info/customer_info_view.py
#
# from PySide6.QtWidgets import (
#     QLabel, QWidget, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox, QCompleter,
#     QScrollArea, QGroupBox, QSpacerItem
# )
# from PySide6.QtGui import QValidator, QStandardItemModel, QStandardItem
# from PySide6.QtCore import Qt, QTimer, Signal
#
# from features.Invoice_Page.customer_info.customer_info_models import Customer
# from features.Invoice_Page.customer_info.customer_info_qss_styles import (CUSTOMER_INFO_STYLES,
#                                                                           BASE_LINEEDIT_STYLE,
#                                                                           VALID_LINEEDIT_STYLE,
#                                                                           INVALID_LINEEDIT_STYLE)
# from shared.utils.validation_utils import (validate_national_id, validate_email, validate_phone_number)
# from shared import to_persian_number, show_error_message_box, show_information_message_box, show_question_message_box
# from shared.widgets.validators import PersianNIDEdit
# from shared.widgets.persian_tools import PhoneLineEdit, EmailLineEdit
#
#
# class CustomerInfoWidget(QWidget):
#     save_requested = Signal(dict)
#     fetch_customer_details_requested = Signal(str)
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setObjectName("CustomerInfoWidget")
#         self.setWindowTitle("فرم اطلاعات مشتریان")
#
#         # Set stylesheets
#         # self.setStyleSheet(CUSTOMER_INFO_STYLES)
#
#         # To map customer names from the completer back to their national IDs
#         self.completer_map = {}
#
#         self.customers = self.db_session.query(CustomersModel).all()
#
#         self.by_name = {c.name: c for c in self.customers}
#         self.by_national_id = {c.national_id: c for c in self.customers}
#         self.by_phone = {c.phone: c for c in self.customers}
#
#         self._add_completer(self.name_edit, list(self.by_name.keys()), self.on_name_selected)
#         self._add_completer(self.national_id_edit, list(self.by_national_id.keys()), self.on_nid_selected)
#         self._add_completer(self.phone_edit, list(self.by_phone.keys()), self.on_phone_selected)
#
#         # --- Main Layout ---
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(15, 15, 15, 15)
#         self.main_layout.setSpacing(15)
#
#         # --- Customer Info Section ---
#         self._setup_customer_fields()
#
#         # --- Companions Section ---
#         self._setup_companions_section()
#         self.main_layout.addStretch(1)
#
#         # --- Action Buttons ---
#         self._setup_action_buttons()
#
#         # --- Initial Setup ---
#         self._is_autofilling = False
#
#     def _setup_customer_fields(self):
#         customer_group = QGroupBox("اطلاعات مشتری اصلی")
#         grid_layout = QGridLayout(customer_group)
#         grid_layout.setSpacing(15)
#         grid_layout.setContentsMargins(15, 15, 15, 15)
#
#         # --- Create Widgets ---
#         self.name_edit = QLineEdit()
#         self.national_id_edit = PersianNIDEdit()
#         self.phone_edit = PhoneLineEdit()
#         self.email_edit = EmailLineEdit()
#         self.address_edit = QLineEdit()
#
#         # --- Create validated field containers using the new helper method ---
#         name_container, self.name_error_label = self._create_validated_field_widget(self.name_edit)
#         nid_container, self.nid_error_label, self.nid_feedback_label = self._create_validated_field_widget(
#             self.national_id_edit, include_feedback=True)
#         phone_container, self.phone_error_label = self._create_validated_field_widget(self.phone_edit)
#         email_container, self.email_error_label = self._create_validated_field_widget(self.email_edit)
#
#         # --- Connect signals for real-time validation ---
#         self.national_id_edit.validation_changed.connect(self._on_nid_validation_changed)
#
#         # --- Add Widgets to Grid ---
#         # Row 0
#         grid_layout.addWidget(QLabel("نام و نام خانوادگی:"), 0, 0, Qt.AlignmentFlag.AlignTop)
#         grid_layout.addWidget(name_container, 0, 1)
#         grid_layout.addWidget(QLabel("کد ملی:"), 0, 2, Qt.AlignmentFlag.AlignTop)
#         grid_layout.addWidget(nid_container, 0, 3)
#
#         # Row 1
#         grid_layout.addWidget(QLabel("شماره تماس:"), 1, 0, Qt.AlignmentFlag.AlignTop)
#         grid_layout.addWidget(phone_container, 1, 1)
#         grid_layout.addWidget(QLabel("ایمیل (اختیاری):"), 1, 2, Qt.AlignmentFlag.AlignTop)
#         grid_layout.addWidget(email_container, 1, 3)
#
#         # Row 2: Address spans all columns
#         grid_layout.addWidget(QLabel("آدرس:"), 2, 0, Qt.AlignmentFlag.AlignTop)
#         grid_layout.addWidget(self.address_edit, 2, 1, 1, 3)
#
#         # --- Make layout responsive ---
#         grid_layout.setColumnStretch(1, 1)
#         grid_layout.setColumnStretch(3, 1)
#         grid_layout.setColumnMinimumWidth(0, 120)
#         grid_layout.setColumnMinimumWidth(2, 120)
#
#         self.main_layout.addWidget(customer_group)
#
#     def _create_validated_field_widget(self, line_edit: QLineEdit, include_feedback=False) -> tuple:
#         """Updated to optionally include a green feedback label."""
#         container = QWidget()
#         container.setObjectName('container_fields')
#         layout = QVBoxLayout(container)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(4)
#         layout.addWidget(line_edit)
#
#         error_label = QLabel()
#         error_label.setObjectName('error_label')
#         error_label.setVisible(False)
#         error_label.setStyleSheet("color: #dc3545; font-size: 9pt;")
#         layout.addWidget(error_label)
#
#         if include_feedback:
#             feedback_label = QLabel()
#             feedback_label.setVisible(False)
#             feedback_label.setStyleSheet("color: #28a745; font-size: 9pt; font-weight: bold;")
#             layout.addWidget(feedback_label)
#             return container, error_label, feedback_label
#
#         return container, error_label
#
#     def add_companion_fields(self, name="", national_id=""):
#         """Adds a new, compact set of fields for one companion."""
#         companion_number = self.companions_layout.count() + 1
#         companion_group = QGroupBox(f"اطلاعات همراه {to_persian_number(companion_number)}")
#         companion_group.setObjectName("CompanionGroup")
#
#         layout = QGridLayout(companion_group)
#         name_edit = QLineEdit(name)
#         nid_edit = PersianNIDEdit()
#         if national_id:
#             nid_edit.setText(str(national_id))
#         remove_button = QPushButton("×")
#         remove_button.setObjectName("RemoveButton")
#
#         name_container, name_error_label = self._create_validated_field_widget(name_edit)
#         nid_container, nid_error_label = self._create_validated_field_widget(nid_edit)
#
#         # Add all widgets to row 0
#         layout.addWidget(QLabel("نام کامل:"), 0, 0, Qt.AlignmentFlag.AlignTop)
#         layout.addWidget(name_container, 0, 1)
#         layout.addWidget(QLabel("کد ملی:"), 0, 2, Qt.AlignmentFlag.AlignTop)
#         layout.addWidget(nid_container, 0, 3)
#         layout.addWidget(remove_button, 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)
#
#         # Set horizontal stretch for the input fields
#         layout.setColumnStretch(1, 1)
#         layout.setColumnStretch(3, 1)
#
#         # This forces the content in row 0 to the top, preventing vertical stretching.
#         layout.setRowStretch(1, 1)
#
#         # Connect signals for validation
#         nid_edit.validation_changed.connect(
#             lambda state, entity_type, le=nid_edit, el=nid_error_label:
#             self._on_companion_nid_validation_changed(state, le, el)
#         )
#
#         # Connect the remove button
#         remove_button.clicked.connect(lambda: self._remove_companion(companion_group))
#
#         self.companions_layout.addWidget(companion_group)
#
#     # --- VISUAL VALIDATION SYSTEM (REVISED) ---
#     def _on_companion_nid_validation_changed(self, state, line_edit, error_label):
#         """Handles visual feedback for a companion's NID field."""
#         if state == QValidator.State.Acceptable:
#             self._set_field_state(line_edit, error_label, "valid")
#         elif state == QValidator.State.Invalid:
#             self._set_field_state(line_edit, error_label, "invalid", "کد ملی معتبر نیست")
#         else:  # Intermediate
#             self._clear_field_state(line_edit, error_label)
#
#     def _clear_field_state(self, line_edit: QLineEdit, error_label: QLabel):
#         self._set_field_state(line_edit, error_label, "neutral")
#
#     def _on_nid_validation_changed(self, state: QValidator.State, entity_type: str):
#         """
#         Slot that handles feedback from the PersianNIDEdit widget.
#         This replaces the old _validate_nid method.
#         """
#         self.nid_feedback_label.hide()  # Hide feedback by default
#
#         if state == QValidator.State.Acceptable:
#             self._set_field_state(self.national_id_edit, self.nid_error_label, "valid")
#             if entity_type == 'real':
#                 self.nid_feedback_label.setText("✔ شخص حقیقی")
#                 self.nid_feedback_label.show()
#             elif entity_type == 'legal':
#                 self.nid_feedback_label.setText("✔ شخص حقوقی")
#                 self.nid_feedback_label.show()
#         elif state == QValidator.State.Invalid:
#             self._set_field_state(self.national_id_edit, self.nid_error_label, "invalid", "کد/شناسه ملی معتبر نیست")
#         else:  # Intermediate state
#             self._clear_field_state(self.national_id_edit, self.nid_error_label)
#
#     def _validate_companion_nid(self, line_edit, error_label, text):
#         if validate_national_id(text):
#             self._set_field_state(line_edit, error_label, "valid")
#         elif not text:
#             self._clear_field_state(line_edit, error_label)
#         else:
#             self._set_field_state(line_edit, error_label, "invalid", "کد ملی معتبر نیست")
#
#     def clear_form(self):
#         """Clears all input fields and their validation states."""
#         for editor in [self.name_edit, self.national_id_edit, self.phone_edit, self.email_edit, self.address_edit]:
#             editor.clear()
#
#         # Clear main fields' visual state
#         self._clear_field_state(self.name_edit, self.name_error_label)
#         self._clear_field_state(self.national_id_edit, self.nid_error_label)
#         self.nid_feedback_label.hide()
#         self._clear_field_state(self.phone_edit, self.phone_error_label)
#         self._clear_field_state(self.email_edit, self.email_error_label)
#
#         self._clear_companion_widgets()
#         self.companions_checkbox.setChecked(False)
#
#     def _style_line_edit(self, line_edit):
#         """Helper to re-apply stylesheet to update property-based styles."""
#         line_edit.style().unpolish(line_edit)
#         line_edit.style().polish(line_edit)
#
#     def _setup_companions_section(self):
#         self.companions_checkbox = QCheckBox("آیا مشتری همراه دارد؟")
#         self.companions_checkbox.stateChanged.connect(self.toggle_companions_ui)
#         self.main_layout.addWidget(self.companions_checkbox)
#
#         self.companions_area = QScrollArea()
#         self.companions_widget = QWidget()
#         self.companions_layout = QVBoxLayout(self.companions_widget)
#         self.companions_area.setWidget(self.companions_widget)
#         self.companions_area.setWidgetResizable(True)
#         self.main_layout.addWidget(self.companions_area)
#         self.companions_area.setVisible(False)
#
#         self.add_companion_button = QPushButton("افزودن همراه")
#         self.add_companion_button.clicked.connect(lambda: self.add_companion_fields())
#         self.main_layout.addWidget(self.add_companion_button)
#         self.add_companion_button.setVisible(False)
#
#     def populate_completer(self, all_people_info: list[dict]):
#         """
#         all_people_info: list of {"name": ..., "national_id": ..., "type": ...}
#         We'll create a QStandardItemModel, store national_id in Qt.UserRole,
#         and build a QCompleter from that model.
#         """
#         model = QStandardItemModel(self)
#
#         for person in all_people_info:
#             item = QStandardItem(person["name"])
#             # store the nid in UserRole so the model carries it
#             item.setData(person["national_id"], Qt.ItemDataRole.UserRole)
#             model.appendRow(item)
#
#         completer = QCompleter(model, self)
#         # Display role is default; keep case-insensitive and contains filtering
#         completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
#         completer.setFilterMode(Qt.MatchFlag.MatchContains)
#
#         # Save for lookup/usage later
#         self._completer_model = model
#         self._completer = completer
#         self.name_edit.setCompleter(completer)
#
#         # when activated, we receive the plain text — find the model item(s) with that display text
#         completer.activated.connect(self._on_completer_activated)
#
#     # This method will be called by the controller after it fetches the data
#     def display_customer_details(self, customer_dto: Customer):
#         """Public slot to pre-fill the form with a Customer object's data."""
#         # This flag prevents validation signals from firing while we programmatically set text
#         # self._is_autofilling = True
#
#         self.clear_form()
#         self.name_edit.setText(customer_dto.name)
#         self.national_id_edit.setText(customer_dto.national_id)
#         self.phone_edit.setText(customer_dto.phone)
#         self.email_edit.setText(customer_dto.email or "")
#         self.address_edit.setText(customer_dto.address or "")
#
#         if customer_dto.companions:
#             for comp in customer_dto.companions:
#                 self.add_companion_fields(comp.name, comp.national_id)
#             self.companions_checkbox.setChecked(True)
#
#         # self._is_autofilling = False
#
#     def toggle_companions_ui(self, state):
#         """
#         Shows or hides the companion section, manages the layout stretch,
#         and adds a default companion field when checked.
#         """
#         is_visible = bool(state)
#         self.companions_area.setVisible(is_visible)
#         self.add_companion_button.setVisible(is_visible)
#
#         if is_visible:
#             self._remove_stretch()
#             # This runs only when the user checks the box, not during autofill,
#             # because autofill adds fields *before* checking the box.
#             if self.companions_layout.count() == 0:
#                 self.add_companion_fields()
#         else:
#             self._add_stretch_before_buttons()
#
#         if not is_visible:
#             self._clear_companion_widgets()
#
#     def _add_stretch_before_buttons(self):
#         """Adds a stretch item specifically before the action buttons layout."""
#         # Defensively remove any existing stretch to avoid duplicates
#         self._remove_stretch()
#
#         # Find the index of our button layout
#         index = self.main_layout.indexOf(self.buttons_layout)
#
#         # Insert a stretch item at that specific index
#         if index != -1:
#             self.main_layout.insertStretch(index, 1)
#
#     def _remove_stretch(self):
#         """Finds and removes any stretch item from the main layout."""
#         for i in range(self.main_layout.count() - 1, -1, -1):
#             item = self.main_layout.itemAt(i)
#             if isinstance(item, QSpacerItem):
#                 self.main_layout.removeItem(item)
#                 return
#
#     def _remove_companion(self, group_box_to_remove: QGroupBox):
#         group_box_to_remove.deleteLater()
#         QTimer.singleShot(0, self._refresh_companion_numbers)
#
#     def _refresh_companion_numbers(self):
#         for i in range(self.companions_layout.count()):
#             widget = self.companions_layout.itemAt(i).widget()
#             if isinstance(widget, QGroupBox):
#                 widget.setTitle(f"اطلاعات همراه {i + 1}")
#
#     def _setup_action_buttons(self):
#         # This layout is now stored as a class attribute to find its position later
#         self.buttons_layout = QHBoxLayout()
#         self.buttons_layout.setSpacing(10)
#
#         self.save_button = QPushButton("ذخیره مشتری")
#         self.save_button.setObjectName("PrimaryButton")
#         self.save_button.clicked.connect(self._on_save_clicked)
#
#         self.clear_button = QPushButton("پاک کردن فرم")
#         self.clear_button.clicked.connect(self.clear_form)
#
#         self.buttons_layout.addStretch()
#         self.buttons_layout.addWidget(self.clear_button)
#         self.buttons_layout.addWidget(self.save_button)
#
#         # Add the button layout to the main layout
#         self.main_layout.addLayout(self.buttons_layout)
#
#     def get_current_data(self) -> dict:
#         """A new public method to get the raw data from the form fields."""
#         # This is the same _logic that was in your old _on_save_clicked method
#         companions = []
#         # Find all companion groups and get their raw text
#         for group_box in self.companions_widget.findChildren(QGroupBox, "CompanionGroup"):
#             line_edits = group_box.findChildren(QLineEdit)
#             if len(line_edits) == 2:
#                 companions.append({
#                     "name": line_edits[0].text(),
#                     "national_id": line_edits[1].text()
#                 })
#
#         # Package all raw data into a single dictionary
#         raw_data = {
#             "name": self.name_edit.text(),
#             "national_id": self.national_id_edit.text(),
#             "phone": self.phone_edit.text(),
#             "email": self.email_edit.text(),
#             "address": self.address_edit.text(),
#             "companions": companions
#         }
#
#         return raw_data
#
#     def _on_save_clicked(self):
#         """
#         Internal slot. Gathers raw data and emits the save_requested signal.
#         This method is now extremely simple.
#         """
#         raw_data = self.get_current_data()
#         self.save_requested.emit(raw_data)
#
#     def _on_completer_activated(self, selected_text: str):
#         """Internal handler for the completer."""
#         if not hasattr(self, "_completer_model"):
#             return
#
#         matches = self._completer_model.findItems(selected_text)
#         if not matches:
#             # fallback: maybe the completer gave partial text — try scanning all rows
#             for row in range(self._completer_model.rowCount()):
#                 item = self._completer_model.item(row)
#                 if item.text() == selected_text:
#                     matches = [item]
#                     break
#
#         if not matches:
#             return
#
#         # If there are multiple matches (same display name), decide policy:
#         # here we take the first match. Alternatively, open a small selector dialog.
#         item = matches[0]
#         nid_to_fetch = item.data(Qt.ItemDataRole.UserRole)
#         if nid_to_fetch:
#             self.fetch_customer_details_requested.emit(str(nid_to_fetch))
#
#     def _set_field_state(self, line_edit: QLineEdit, error_label: QLabel, state: str, message: str = None):
#         """A generic helper to set the visual state of a field."""
#         if state == "valid":
#             line_edit.setStyleSheet(VALID_LINEEDIT_STYLE)
#             error_label.setVisible(False)
#         elif state == "invalid" and message:
#             line_edit.setStyleSheet(INVALID_LINEEDIT_STYLE)
#             error_label.setText(message)
#             error_label.setVisible(True)
#         else:  # "neutral" or default state
#             line_edit.setStyleSheet(BASE_LINEEDIT_STYLE)
#             error_label.setVisible(False)
#
#     def _clear_companion_widgets(self):
#         while self.companions_layout.count():
#             child = self.companions_layout.takeAt(0)
#             if child.widget():
#                 child.widget().deleteLater()
#
#     def show_save_success(self, message):
#         """Public slot to show a success message."""
#         show_information_message_box(self, "موفقیت", message)
#
#     def show_error(self, message: str):
#         """Public slot to show an error message."""
#         show_error_message_box(self, "خطا", message)
#
#     def show_edit_question(self, message, func):
#         """Public slot to show question message box."""
#         show_question_message_box(parent=self,
#                                   title="ویراش مشتری",
#                                   message=message,
#                                   button_1="بله",
#                                   yes_func=func,
#                                   button_2="خیر"
#                                   )
#
#     def display_validation_results(self, errors: dict):
#         """
#         NEW: Public method to display validation feedback.
#         The _view doesn't know what the errors mean, it just displays them.
#         """
#         # Reset all fields to neutral/valid state first
#         self._set_field_state(self.name_edit, self.name_error_label, "valid")
#         self._set_field_state(self.national_id_edit, self.nid_error_label, "valid")
#         self._set_field_state(self.phone_edit, self.phone_error_label, "valid")
#         self._set_field_state(self.email_edit, self.email_error_label, "valid")
#
#         # Apply invalid states based on the errors dictionary
#         if 'name' in errors:
#             self._set_field_state(self.name_edit, self.name_error_label, "invalid", errors['name'])
#         if 'national_id' in errors:
#             self._set_field_state(self.national_id_edit, self.nid_error_label, "invalid", errors['national_id'])
#         if 'phone' in errors:
#             self._set_field_state(self.phone_edit, self.phone_error_label, "invalid", errors['phone'])
#         if 'email' in errors:
#             self._set_field_state(self.email_edit, self.email_error_label, "invalid", errors['email'])
#         if 'companions' in errors:
#             # Show general companion error, e.g., in a message box or a dedicated label
#             self.show_error(errors['companions'])
#
#     # ---- slots for completer ----
#     def _add_completer(self, line_edit, items, slot):
#         completer = QCompleter(items)
#         completer.setCaseSensitivity(Qt.CaseInsensitive)
#         line_edit.setCompleter(completer)
#
#     def on_name_selected(self, text):
#         customer = self.by_name.get(text)
#         if customer:
#             self._fill_fields(customer)
#
#     def on_nid_selected(self, text):
#         customer = self.by_national_id.get(text)
#         if customer:
#             self._fill_fields(customer)
#
#     def on_phone_selected(self, text):
#         customer = self.by_phone.get(text)
#         if customer:
#             self._fill_fields(customer)
#
#     def _fill_fields(self, customer):
#         self.name_edit.setText(customer.name)
#         self.national_id_edit.setText(customer.national_id or "")
#         self.phone_edit.setText(customer.phone or "")
#         self.address_edit.setText(customer.address or "")
