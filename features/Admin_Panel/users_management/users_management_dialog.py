# features/Admin_Panel/users_management/users_management_dialog.py

import qtawesome as qta
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout,
                               QCheckBox, QLabel)
from PySide6.QtCore import Signal, Qt
from features.Admin_Panel.employee_management.employee_management_dialog import ROLE_MAP
from features.Admin_Panel.users_management.users_management_models import UserData


class UserAccountDialog(QDialog):
    """A dialog to create or edit a user account, aligned with UsersModel."""
    save_requested = Signal(dict)

    def __init__(self, user_data: UserData | None = None, parent=None):
        super().__init__(parent)
        self._is_edit_mode = user_data is not None
        self._user_data = user_data
        self.setWindowTitle(
            "ویرایش کاربر" if self._is_edit_mode else "ایجاد حساب کاربری سیستم"
        )
        self.setMinimumWidth(450)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._setup_ui()
        self._connect_signals()

        if self._is_edit_mode:
            self._populate_data_for_edit()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.display_name_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("فقط حروف انگلیسی، اعداد و _")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_combo = QComboBox()
        for key, value in ROLE_MAP.items():
            self.role_combo.addItem(value, key)
        self.is_active_check = QCheckBox("اکانت فعال باشد")
        self.is_active_check.setChecked(True)

        form.addRow("* نام نمایشی:", self.display_name_edit)
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
        if self._is_edit_mode:
            self.save_btn = QPushButton("ذخیره تغییرات")
            self.save_btn.setIcon(qta.icon('fa5s.save'))
        else:
            self.save_btn = QPushButton("ایجاد کاربر")
            self.save_btn.setIcon(qta.icon('fa5s.user-plus'))
        self.cancel_btn = QPushButton("انصراف")
        self.cancel_btn.setIcon(qta.icon('fa5s.times'))
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        if self._is_edit_mode:
            self.username_edit.setReadOnly(True)
            self.password_edit.setPlaceholderText("برای تغییر، رمز جدید را وارد کنید")

    def _connect_signals(self):
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _populate_data_for_edit(self):
        """Fills the dialog's fields with data from an existing user."""
        self.display_name_edit.setText(self._user_data.display_name)
        self.username_edit.setText(self._user_data.username)
        self.is_active_check.setChecked(self._user_data.is_active)
        role_index = self.role_combo.findData(self._user_data.role)
        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)

    def _on_save(self):
        self.error_label.hide()
        user_data = self.get_data()
        self.save_requested.emit(user_data)

    def get_data(self) -> dict:
        """Returns all collected data in a simple dictionary."""
        data = {
            "display_name": self.display_name_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text(),
            "role": self.role_combo.currentData(),
            "is_active": self.is_active_check.isChecked(),
        }
        if self._is_edit_mode:
            data["user_id"] = self._user_data.user_id
        return data

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
