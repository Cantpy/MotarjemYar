# features/Main_Window/main_window_controller.py

"""
Controller for the Main Window feature.
Handles navigation and page management within the main application window.
"""

from PySide6.QtCore import QObject, Signal
from sqlalchemy.engine import Engine

from core.navigation import PageManager, PageLifetime
from config.config_manager import ConfigManager

from features.Home_Page.home_page_factory import HomePageFactory
from features.Invoice_Page.wizard_host.invoice_wizard_factory import InvoiceWizardFactory
from features.Admin_Panel.admin_panel.admin_panel_factory import AdminPanelFactory
from features.Invoice_Table.invoice_table_factory import InvoiceTableFactory
from features.Services.tab_manager.tab_manager_factory import ServicesManagementFactory
from features.Info_Page.info_page_factory import InfoPageFactory
from features.Workspace.workspace_factory import WorkspaceFactory

from shared.orm_models.invoices_models import InvoiceData, InvoiceItemData
from shared import show_error_message_box, get_resource_path


class MainWindowController(QObject):
    logout_requested = Signal()

    def __init__(self, view: "MainWindowView", logic: "MainWindowLogic",
                 username: str, engines: dict[str, Engine]):
        super().__init__()
        self._view = view
        self._logic = logic
        self._username = username
        self._engines = engines

        self.page_manager = PageManager(self._view.stackedWidget)
        self.page_controllers = {}
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

    # ---------------------------------------------------------------------
    # Register pages with their lifetime policies
    # ---------------------------------------------------------------------
    def _register_pages(self):
        """Register all page controllers with caching policies."""

        # --- Dynamic / frequently updated pages ---
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

        # --- Persistent pages (stateful or heavy) ---
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

        print("Page factories registered with lifetime policies.")

    # ---------------------------------------------------------------------
    # Helper to connect invoice table deep edit navigation
    # ---------------------------------------------------------------------
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

    # ---------------------------------------------------------------------
    # Signal Connections
    # ---------------------------------------------------------------------
    def _connect_signals(self):
        v = self._view
        v.home_button.clicked.connect(lambda: self.page_manager.show("home"))
        v.invoice_button.clicked.connect(lambda: self.page_manager.show("invoice"))
        v.large_user_pic.clicked.connect(lambda: self.page_manager.show("admin_panel"))
        v.issued_invoices_button.clicked.connect(lambda: self.page_manager.show('invoice_table'))
        v.documents_button.clicked.connect(lambda: self.page_manager.show('services'))
        v.help_button.clicked.connect(lambda: self.page_manager.show('info_page'))
        v.workspace_button.clicked.connect(lambda: self.page_manager.show('workspace'))
        v.settings_button_clicked.connect(self._on_settings_button_clicked)
        v.logout_button_clicked.connect(self.logout_requested.emit)

        v.close_button_clicked.connect(self._on_close_button_clicked)
        v.minimize_button_clicked.connect(v.showMinimized)
        v.maximize_button_clicked.connect(self._toggle_maximize)

    # ---------------------------------------------------------------------
    def initialize_with_user(self, username: str):
        user_dto = self._logic.get_user_profile_for_view(username)
        if user_dto:
            self._view.update_user_profile(user_dto)
        else:
            print(f"Warning: Could not load profile for user '{username}'.")
        self.page_manager.show("home")

    def _on_request_deep_edit(self, invoice_data: InvoiceData, items_data: list[InvoiceItemData]):
        print(f"MainWindow: Deep edit requested for {invoice_data.invoice_number}")
        self.page_manager.show("invoice")
        invoice_wizard_controller = self.page_manager.get_controller("invoice")
        if invoice_wizard_controller:
            invoice_wizard_controller.start_deep_edit_session(invoice_data, items_data)
        else:
            show_error_message_box(self._view, "Application Error", "Invoice wizard controller not found.")

    def _toggle_maximize(self):
        if self._view.isMaximized():
            self._view.showNormal()
        else:
            self._view.showMaximized()

    def _on_settings_button_clicked(self):
        print("Controller: Settings button clicked.")
        # Future: self.page_manager.show("settings")

    def _on_close_button_clicked(self):
        self._view.handle_close_request()
