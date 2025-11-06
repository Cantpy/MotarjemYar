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
        self._setup_styles()

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

    def _setup_styles(self):
        self.setStyleSheet(CUSTOMER_INFO_STYLES)

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
