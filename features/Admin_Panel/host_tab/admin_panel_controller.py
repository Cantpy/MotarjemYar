# Admin_Panel/host_tab/admin_panel_controller.py

from PySide6.QtCore import QObject
from features.Admin_Panel.host_tab.admin_panel_view import AdminMainWindowView
from features.Admin_Panel.host_tab.admin_panel_logic import AdminMainWindowService


class AdminMainWindowController(QObject):
    """
    Controller for the Admin Panel main window.
    """
    def __init__(self, view: AdminMainWindowView, logic: AdminMainWindowService):
        super().__init__()
        self._view = view
        self._service = logic

        self._setup_tabs()

    def _setup_tabs(self):
        for view, icon, title in self._service.create_tabs():
            self._view.tab_widget.addTab(view, icon, title)

    def get_view(self):
        return self._view
