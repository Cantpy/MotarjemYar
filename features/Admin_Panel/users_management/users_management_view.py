# features/Admin_Panel/users_management/users_management_view.py

import qtawesome as qta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QHBoxLayout, QPushButton, QLineEdit, QHeaderView)
from PySide6.QtCore import Signal, Qt
from features.Admin_Panel.users_management.users_management_models import UserData

ROLE_MAP = {"admin": "مدیر", "user": "کاربر"}


class UsersManagementView(QWidget):
    add_user_requested = Signal()
    edit_user_requested = Signal(object)  # Emits UserData
    delete_user_requested = Signal(int)  # Emits user_id
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #f9f9f9;")
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # title = QLabel("مدیریت کاربران")
        # font = QFont()
        # font.setPointSize(18)
        # font.setBold(True)
        # title.setFont(font)

        actions_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام کاربری یا نام کامل...")
        self.add_user_btn = QPushButton(" کاربر جدید")
        self.add_user_btn.setIcon(qta.icon('fa5s.user-plus'))
        actions_layout.addWidget(self.search_input)
        actions_layout.addStretch()
        actions_layout.addWidget(self.add_user_btn)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["نام کاربری", "نام کامل", "نقش", "وضعیت", "عملیات"])
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.verticalHeader().setVisible(False)

        # layout.addWidget(title)
        layout.addLayout(actions_layout)
        layout.addWidget(self.users_table)

    def _connect_signals(self):
        self.add_user_btn.clicked.connect(self.add_user_requested.emit)
        self.search_input.textChanged.connect(self.search_requested.emit)

    def populate_table(self, users: list[UserData]):
        self.users_table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user.username))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.display_name))
            self.users_table.setItem(row, 2, QTableWidgetItem(ROLE_MAP.get(user.role, user.role)))

            status_item = QTableWidgetItem("فعال" if user.is_active else "غیرفعال")
            status_item.setForeground(Qt.GlobalColor.darkGreen if user.is_active else Qt.GlobalColor.red)
            self.users_table.setItem(row, 3, status_item)

            self._add_action_buttons(row, user)

    def _add_action_buttons(self, row: int, user: UserData):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        edit_btn = QPushButton(icon=qta.icon('fa5s.pencil-alt', color='blue'))
        edit_btn.setToolTip("ویرایش کاربر")
        edit_btn.clicked.connect(lambda chk, u=user: self.edit_user_requested.emit(u))

        delete_btn = QPushButton(icon=qta.icon('fa5s.trash', color='red'))
        delete_btn.setToolTip("حذف کاربر")
        delete_btn.clicked.connect(lambda chk, u_id=user.user_id: self.delete_user_requested.emit(u_id))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        self.users_table.setCellWidget(row, 4, widget)
