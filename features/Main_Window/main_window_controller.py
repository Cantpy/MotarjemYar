# features/Main_Window/main_window_controller.py

"""
Controller for the Main Window feature.
Handles navigation, page management, and application lifecycle logic.
"""

from PySide6.QtCore import QObject, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication
from sqlalchemy.engine import Engine

from core.navigation import PageManager, PageLifetime
from config.config_manager import ConfigManager

# Page Factories
from features.Home_Page.home_page_factory import HomePageFactory
from features.Invoice_Page.wizard_host.invoice_wizard_factory import InvoiceWizardFactory
from features.Admin_Panel.admin_panel.admin_panel_factory import AdminPanelFactory
from features.Invoice_Table.invoice_table_factory import InvoiceTableFactory
from features.Services.tab_manager.tab_manager_factory import ServicesManagementFactory
from features.Info_Page.info_page_factory import InfoPageFactory
from features.Workspace.workspace_factory import WorkspaceFactory

# Shared
from shared.orm_models.invoices_models import InvoiceData, InvoiceItemData
from shared import show_error_message_box, get_resource_path
from features.Main_Window.main_window_view import ExitDialog


class MainWindowController(QObject):
    logout_requested = Signal()

    def __init__(self, view, logic, username: str, engines: dict[str, Engine]):
        super().__init__()
        self._view = view
        self._logic = logic
        self._username = username
        self._engines = engines

        self.page_manager = PageManager(self._view.stackedWidget)
        self._register_pages()

        try:
            self.config = ConfigManager(get_resource_path('config', 'config.ini'))
            self.broker_host = self.config.get_broker_host()
        except FileNotFoundError:
            show_error_message_box(self._view, "Configuration Error", "Could not find config.ini.")
            self.broker_host = '127.0.0.1'

        self._connect_signals()
        self.initialize_with_user(username)

        # Optionally preload heavy pages silently
        self.page_manager.preload("admin_panel", delay_ms=2000)

    def get_view(self):
        return self._view

    def _register_pages(self):
        """Register all page controllers with caching policies."""
        # ... (Same as your original code) ...
        self.page_manager.register(
            "home",
            lambda: HomePageFactory.create(
                business_engine=self._engines.get('business'),
                parent=self._view),
            lifetime=PageLifetime.REFRESH_ON_SHOW
        )
        self.page_manager.register(
            "invoice_table",
            lambda: self._create_invoice_table_controller(),
            lifetime=PageLifetime.REFRESH_ON_SHOW
        )
        self.page_manager.register(
            "services",
            lambda: ServicesManagementFactory.create(
                business_engine=self._engines.get('business'),
                parent=self._view),
            lifetime=PageLifetime.REFRESH_ON_SHOW
        )
        self.page_manager.register(
            "invoice",
            lambda: InvoiceWizardFactory.create(
                business_engine=self._engines.get('business'),
                parent=self._view),
            lifetime=PageLifetime.KEEP_ALIVE
        )
        self.page_manager.register(
            "admin_panel",
            lambda: AdminPanelFactory.create(
                business_engine=self._engines.get('business'),
                payroll_engine=self._engines.get('payroll'),
                parent=self._view),
            lifetime=PageLifetime.TIMEOUT
        )
        self.page_manager.register(
            "info_page",
            lambda: InfoPageFactory.create(
                info_page_engine=self._engines.get('info_page'),
                parent=self._view),
            lifetime=PageLifetime.KEEP_ALIVE
        )
        self.page_manager.register(
            "workspace",
            lambda: WorkspaceFactory.create(
                self._engines.get('users'),
                self._engines.get('workspace'),
                self._logic.get_user_profile_for_view(self._username).id,
                self.broker_host,
                self._view),
            lifetime=PageLifetime.KEEP_ALIVE
        )

    def _create_invoice_table_controller(self):
        controller = InvoiceTableFactory.create(
            invoices_engine=self._engines.get('invoices'),
            users_engine=self._engines.get('users'),
            services_engine=self._engines.get('services'),
            payroll_engine=self._engines.get('payroll'),
            parent=self._view
        )
        controller.request_deep_edit_navigation.connect(self._on_request_deep_edit)
        return controller

    def _connect_signals(self):
        """Connect View signals to Controller methods."""
        v = self._view

        # Navigation
        v.home_button_clicked.connect(lambda: self.page_manager.show("home"))
        v.invoice_button_clicked.connect(lambda: self.page_manager.show("invoice"))
        v.user_profile_clicked.connect(lambda: self.page_manager.show("admin_panel"))
        v.issued_invoices_button_clicked.connect(lambda: self.page_manager.show('invoice_table'))
        v.documents_button_clicked.connect(lambda: self.page_manager.show('services'))
        v.help_button_clicked.connect(lambda: self.page_manager.show('info_page'))
        # v.workspace_button.clicked.connect(lambda: self.page_manager.show('workspace'))  # Note: View signal name check

        # Actions
        v.settings_button_clicked.connect(self._on_settings_button_clicked)
        v.logout_button_clicked.connect(self.logout_requested.emit)

        # Window State
        v.close_button_clicked.connect(self._handle_close_request)
        v.minimize_button_clicked.connect(self._handle_minimize_request)
        v.maximize_button_clicked.connect(self._toggle_maximize)

    def initialize_with_user(self, username: str):
        user_dto = self._logic.get_user_profile_for_view(username)
        if user_dto:
            self._view.update_user_profile(user_dto)
        self.page_manager.show("home")

    def _on_request_deep_edit(self, invoice_data: InvoiceData, items_data: list[InvoiceItemData]):
        self.page_manager.show("invoice")
        invoice_wizard_controller = self.page_manager.get_controller("invoice")
        if invoice_wizard_controller:
            invoice_wizard_controller.start_deep_edit_session(invoice_data, items_data)

    def _toggle_maximize(self):
        """Logic for toggling maximize state."""
        self._view.toggle_maximize_restore()

    def _handle_minimize_request(self):
        """Logic to fade out before minimizing (if desired) or just minimize."""
        # You can add the fade animation logic here if you want it controlled by logic,
        # or call a view method that runs the animation.
        self._view.smooth_minimize()

    def _on_settings_button_clicked(self):
        print("Controller: Settings button clicked.")

    def _handle_close_request(self):
        """
        Handles the application close sequence.
        1. Show confirmation dialog.
        2. If confirmed, fade out and quit.
        """
        dialog = ExitDialog(parent=self._view)
        if dialog.exec():
            # User clicked "Yes"
            self._fade_out_and_exit()

    def _fade_out_and_exit(self):
        """
        Animate window opacity to 0 then exit system.
        """
        self._anim = QPropertyAnimation(self._view, b"windowOpacity")
        self._anim.setDuration(350)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(self._perform_system_exit)
        self._anim.start()

    def _perform_system_exit(self):
        QApplication.quit()
