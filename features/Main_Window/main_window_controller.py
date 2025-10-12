# features/Main_Window/main_window_controller.py

from PySide6.QtCore import QObject
from sqlalchemy.engine import Engine

from core.navigation import PageManager
from config.config_manager import ConfigManager

from features.Main_Window.main_window_view import MainWindowView
from features.Main_Window.main_window_logic import MainWindowLogic
from features.Home_Page.home_page_factory import HomePageFactory
from features.Invoice_Page.wizard_host.invoice_wizard_factory import InvoiceWizardFactory
from features.Admin_Panel.host_tab.host_tab_factory import AdminPanelFactory
from features.Invoice_Table.invoice_table_factory import InvoiceTableFactory
from features.Services.tab_manager.tab_manager_factory import ServicesManagementFactory
from features.Info_Page.info_page_factory import InfoPageFactory
from features.Workspace.workspace_factory import WorkspaceFactory

from shared.orm_models.invoices_models import InvoiceData, InvoiceItemData
from shared import show_error_message_box, get_resource_path


class MainWindowController(QObject):
    """
    Controller for the main application window.
    Connects user actions from the _view to the application's business _logic.
    """

    def __init__(self, view: "MainWindowView", logic: "MainWindowLogic", username: str, engines: dict[str, Engine]):
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

    def get_view(self):
        """Returns the main window widget to be shown."""
        return self._view

    def _register_pages(self):
        """
        Register all page controllers with the PageManager.
        The factory function is responsible for creating, caching, and connecting the controller.
        """

        def create_home_page():
            if "home" not in self.page_controllers:
                controller = HomePageFactory.create(
                    customers_engine=self._engines.get('customers'),
                    invoices_engine=self._engines.get('invoices'),
                    services_engine=self._engines.get('services'),
                    users_engine=self._engines.get('users'),
                    parent=self._view
                )
                self.page_controllers["home"] = controller
            return self.page_controllers["home"]

        self.page_manager.register("home", create_home_page)

        def create_invoice_wizard():
            if "invoice" not in self.page_controllers:
                controller = InvoiceWizardFactory.create(
                    customer_engine=self._engines.get('customers'),
                    invoices_engine=self._engines.get('invoices'),
                    services_engine=self._engines.get('services'),
                    users_engine=self._engines.get('users'),
                    parent=self._view
                )
                self.page_controllers["invoice"] = controller
            return self.page_controllers["invoice"]

        self.page_manager.register("invoice", create_invoice_wizard)

        def create_invoice_table():
            if "invoice_table" not in self.page_controllers:
                controller = InvoiceTableFactory.create(
                    invoices_engine=self._engines.get('invoices'),
                    users_engine=self._engines.get('users'),
                    services_engine=self._engines.get('services'),
                    parent=self._view
                )
                # --- FIX: Connect the signal here, at the moment of creation ---
                controller.request_deep_edit_navigation.connect(self._on_request_deep_edit)
                self.page_controllers["invoice_table"] = controller
            return self.page_controllers["invoice_table"]

        self.page_manager.register("invoice_table", create_invoice_table)

        def create_admin_panel():
            if "users" not in self.page_controllers:
                controller = AdminPanelFactory.create(
                    users_engine=self._engines.get('users'),
                    payroll_engine=self._engines.get('payroll'),
                    expenses_engine=self._engines.get('expenses'),
                    customers_engine=self._engines.get('customers'),
                    invoices_engine=self._engines.get('invoices'),
                    services_engine=self._engines.get('services'),
                    parent=self._view
                )
                self.page_controllers["users"] = controller
            return self.page_controllers["users"]

        self.page_manager.register("users", create_admin_panel)

        # --- Other pages converted to the robust factory pattern ---

        def create_services_management():
            if "services" not in self.page_controllers:
                controller = ServicesManagementFactory.create(
                    services_engine=self._engines.get('services'),
                    parent=self._view
                )
                self.page_controllers["services"] = controller
            return self.page_controllers["services"]

        self.page_manager.register("services", create_services_management)

        def create_info_page():
            if "info_page" not in self.page_controllers:
                controller = InfoPageFactory.create(
                    info_page_engine=self._engines.get('info_page'),
                    parent=self._view
                )
                self.page_controllers["info_page"] = controller
            return self.page_controllers["info_page"]

        self.page_manager.register('info_page', create_info_page)

        def create_workspace():
            if "workspace" not in self.page_controllers:
                controller = WorkspaceFactory.create(
                    self._engines.get('users'),
                    self._engines.get('workspace'),
                    self._logic.get_user_profile_for_view(self._username).id,
                    self.broker_host,
                    self._view
                )
                self.page_controllers["workspace"] = controller
            return self.page_controllers["workspace"]

        self.page_manager.register('workspace', create_workspace)
        print("Page factories registered with PageManager.")

    def _connect_signals(self):
        """Connect signals from the main window's view to slots in this controller."""
        # --- Sidebar Navigation to use the PageManager ---
        self._view.home_button.clicked.connect(lambda: self.page_manager.show("home"))
        self._view.invoice_button.clicked.connect(lambda: self.page_manager.show("invoice"))
        self._view.large_user_pic.clicked.connect(lambda: self.page_manager.show("users"))
        self._view.issued_invoices_button.clicked.connect(lambda: self.page_manager.show('invoice_table'))
        self._view.documents_button.clicked.connect(lambda: self.page_manager.show('services'))
        self._view.help_button.clicked.connect(lambda: self.page_manager.show('info_page'))
        self._view.workspace_button.clicked.connect(lambda: self.page_manager.show('workspace'))
        self._view.settings_button_clicked.connect(self._on_settings_button_clicked)

        # --- FIX: The connection logic is now inside the factory functions, so we remove it from here ---

        # --- Titlebar Click ---
        self._view.close_button_clicked.connect(self._on_close_button_clicked)
        self._view.minimize_button_clicked.connect(self._view.showMinimized)
        self._view.maximize_button_clicked.connect(self._toggle_maximize)

    def initialize_with_user(self, username: str):
        """
        Fetches user data and shows the initial page.
        """
        user_dto = self._logic.get_user_profile_for_view(username)
        if user_dto:
            self._view.update_user_profile(user_dto)
        else:
            print(f"Warning: Could not load profile for user '{username}'.")
        self.page_manager.show("home")

    def _on_request_deep_edit(self, invoice_data: InvoiceData, items_data: list[InvoiceItemData]):
        """
        Receives the signal from the invoice table and orchestrates the navigation
        and data passing to the invoice wizard.
        """
        print(f"MainWindow: Received request to deep edit {invoice_data.invoice_number}. Navigating...")

        self.page_manager.show("invoice")
        invoice_wizard_controller = self.page_controllers.get("invoice")

        if invoice_wizard_controller:
            invoice_wizard_controller.start_deep_edit_session(invoice_data, items_data)
        else:
            show_error_message_box(self._view, "خطای برنامه", "کنترلر صفحه صدور فاکتور یافت نشد.")

    def _toggle_maximize(self):
        if self._view.isMaximized():
            self._view.showNormal()
        else:
            self._view.showMaximized()

    def _on_settings_button_clicked(self):
        """Handle the user clicking the 'Settings' button."""
        print("Controller: Settings button clicked.")
        # Assuming you will create a 'settings' page
        # self.page_manager.show("settings")

    def _on_close_button_clicked(self):
        """
        Handles the user clicking the 'X' button in the title bar.
        Instructs the _view to begin its close confirmation process.
        """
        self._view.handle_close_request()
