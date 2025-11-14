from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap

from features.Admin_Panel.user_info.user_info_view import UserInfoView


class UserInfoController(QObject):
    """
    Controller for the User Info view. Handles user interactions like
    uploading an avatar and saving changes.
    """
    def __init__(self, view: UserInfoView):
        super().__init__()
        self._view = view
        self._connect_signals()

    def _connect_signals(self):
        """ Connects view signals to controller slots. """
        self._view.avatar_label.mousePressEvent = self._on_avatar_clicked
        self._view.save_button.clicked.connect(self._on_save_clicked)

    def _on_avatar_clicked(self, event):
        """ Opens a file dialog to select a new avatar image. """
        file_path, _ = QFileDialog.getOpenFileName(
            self._view,
            "انتخاب تصویر آواتار",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            self._view.set_avatar(pixmap)

    def _on_save_clicked(self):
        """
        Placeholder for saving user data. In a real app, this would
        interact with a model or database service.
        """
        display_name = self._view.display_name_input.text()
        role = self._view.role_combo.currentText()
        is_active = self._view.active_status_checkbox.isChecked()

        # You can now use these values to update your database
        print(f"Saving user data: Name='{display_name}', Role='{role}', Active={is_active}")

        QMessageBox.information(self._view, "موفق", "اطلاعات کاربر با موفقیت ذخیره شد.")

    def get_view(self) -> UserInfoView:
        """ Returns the view managed by this controller. """
        return self._view
