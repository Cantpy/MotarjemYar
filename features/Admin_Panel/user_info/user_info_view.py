import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
                               QComboBox, QCheckBox, QPushButton, QHBoxLayout, QMessageBox,
                               QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import qtawesome as qta

from shared.orm_models.users_models import UsersData


class UserInfoView(QWidget):
    """
    A view for displaying and editing the current user's information.
    Emits signals when the user performs actions.
    """
    # Define signals that the controller can connect to
    save_clicked = Signal(UsersData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UserInfoView")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Internal state for new avatar path before saving
        self._current_avatar_path = None

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # --- Avatar ---
        self.avatar_label = QLabel("برای آپلود کلیک کنید")
        self.avatar_label.setFixedSize(128, 128)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel { border: 2px dashed #aaa; border-radius: 64px; background-color: #f0f0f0; }
            QLabel:hover { background-color: #e0e0e0; }
        """)
        self.avatar_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.avatar_label.mousePressEvent = self._on_avatar_label_clicked

        # --- Fields ---
        self.username_input = QLineEdit()
        self.username_input.setReadOnly(True)
        self.display_name_input = QLineEdit()
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "user"])
        self.active_status_checkbox = QCheckBox("کاربر فعال است")

        # --- Save Button ---
        self.save_button = QPushButton("ذخیره تغییرات")
        self.save_button.setIcon(qta.icon('fa5s.save'))
        self.save_button.clicked.connect(self._on_save_button_clicked)

        # --- Layout Assembly ---
        # ... (Layout code is identical to previous versions, so omitted for brevity) ...
        avatar_layout = QHBoxLayout()
        avatar_layout.addStretch()
        avatar_layout.addWidget(self.avatar_label)
        avatar_layout.addStretch()
        main_layout.addLayout(avatar_layout)
        main_layout.addSpacing(20)

        form_layout.addRow("نام کاربری:", self.username_input)
        form_layout.addRow("نام نمایشی:", self.display_name_input)
        form_layout.addRow("نقش:", self.role_combo)
        form_layout.addRow(self.active_status_checkbox)
        main_layout.addLayout(form_layout)

        main_layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        main_layout.addLayout(button_layout)

    def _on_save_button_clicked(self):
        """ Gathers data into a DTO and emits the save_clicked signal. """
        dto = UsersData(
            username=self.username_input.text(),
            display_name=self.display_name_input.text(),
            role=self.role_combo.currentText(),
            active=1 if self.active_status_checkbox.isChecked() else 0,
            avatar_path=self._current_avatar_path,

        )
        self.save_clicked.emit(dto)

    def _on_avatar_label_clicked(self, event):
        """ Opens a file dialog and updates the avatar preview. """
        file_path, _ = QFileDialog.getOpenFileName(self, "انتخاب تصویر آواتار", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self._current_avatar_path = file_path
            self.set_avatar(file_path)

    def set_avatar(self, path: str | None):
        """ Sets the user's avatar image from a file path. """
        if path and os.path.exists(path):
            self._current_avatar_path = path
            pixmap = QPixmap(path)
            self.avatar_label.setPixmap(pixmap.scaled(
                self.avatar_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.avatar_label.setText("برای آپلود کلیک کنید")
            self.avatar_label.setPixmap(QPixmap())  # Clear pixmap

    def display_user_data(self, data: UsersData):
        """ Populates the view's fields from a DTO. """
        self.username_input.setText(data.username)
        self.display_name_input.setText(data.display_name)
        role_index = self.role_combo.findText(data.role)
        if role_index != -1:
            self.role_combo.setCurrentIndex(role_index)
        self.active_status_checkbox.setChecked(data.active)
        self.set_avatar(data.avatar_path)

    def show_message(self, title: str, message: str, is_error: bool = False):
        """ Displays a message box to the user. """
        if is_error:
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
