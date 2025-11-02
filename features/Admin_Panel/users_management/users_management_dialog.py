# features/Admin_Panel/users_management/users_management_dialog.py

import qtawesome as qta
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout,
                               QCheckBox, QLabel)
from PySide6.QtCore import Signal, Qt
from features.Admin_Panel.employee_management.employee_management_dialog import ROLE_MAP


class UserAccountDialog(QDialog):
    """A lightweight dialog to create a new user account (users.db)."""
    save_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مرحله 1: ایجاد حساب کاربری سیستم")
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        # These fields are for the Employee profile later, but it's better UX to ask once.
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.national_id_edit = QLineEdit()
        self.national_id_edit.setMaxLength(10)

        # These are for the User account itself.
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("فقط حروف انگلیسی، اعداد و _")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("حداقل ۶ کاراکتر، شامل حرف و عدد")
        self.role_combo = QComboBox()
        for key, value in ROLE_MAP.items():
            self.role_combo.addItem(value, key)
        self.is_active_check = QCheckBox("اکانت فعال باشد")
        self.is_active_check.setChecked(True)

        form.addRow("* نام:", self.first_name_edit)
        form.addRow("* نام خانوادگی:", self.last_name_edit)
        form.addRow("* کد ملی:", self.national_id_edit)
        form.addRow("* نام کاربری:", self.username_edit)
        form.addRow("* رمز عبور:", self.password_edit)
        form.addRow("* نقش سیستمی:", self.role_combo)
        form.addRow("", self.is_active_check)
        layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #D32F2F;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("ایجاد کاربر و ادامه", icon=qta.icon('fa5s.arrow-right'))
        self.cancel_btn = QPushButton("انصراف", icon=qta.icon('fa5s.times'))
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_save(self):
        # The controller will handle validation via the logic layer
        self.error_label.hide()
        user_data = self.get_data()
        self.save_requested.emit(user_data)

    def get_data(self) -> dict:
        """Returns all collected data in a simple dictionary."""
        return {
            "first_name": self.first_name_edit.text().strip(),
            "last_name": self.last_name_edit.text().strip(),
            "national_id": self.national_id_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text(),
            "role": self.role_combo.currentData(),
            "is_active": self.is_active_check.isChecked(),
        }

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
