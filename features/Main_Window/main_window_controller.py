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
        self._register_pages()

        try:
            self.config = ConfigManager(get_resource_path('config', 'config.ini'))
            # Store the broker host as an instance attribute for easy access
            self.broker_host = self.config.get_broker_host()
        except FileNotFoundError:
            show_error_message_box(self._view, "Configuration Error", "Could not find config.ini.")
            # Set a safe fallback or exit the application
            self.broker_host = '127.0.0.1'

        self._connect_signals()

        self.page_manager.show("home")

    def get_view(self):
        """Returns the main window widget to be shown."""
        return self._view

    def _register_pages(self):
        """
        Register all page controllers with the PageManager.
        This is where the main controller passes the application's core
        dependencies (like session makers) down to the feature factories.
        """
        # --- Home Page: Needs 'customers' and 'invoices' engines ---
        self.page_manager.register(
            "home",
            lambda: HomePageFactory.create(
                customers_engine=self._engines.get('customers'),
                invoices_engine=self._engines.get('invoices'),
                parent=self._view
            )
        )

        # --- Invoice Wizard: Needs 'customers', 'invoices', 'services', 'users' ---
        self.page_manager.register(
            "invoice",
            lambda: InvoiceWizardFactory.create(
                customer_engine=self._engines.get('customers'),
                invoices_engine=self._engines.get('invoices'),
                services_engine=self._engines.get('services'),
                users_engine=self._engines.get('users'),
                parent=self._view
            )
        )

        # --- Admin Panel: Needs multiple engines ---
        self.page_manager.register(
            "users",
            lambda: AdminPanelFactory.create(
                users_engine=self._engines.get('users'),
                payroll_engine=self._engines.get('payroll'),
                expenses_engine=self._engines.get('expenses'),
                customers_engine=self._engines.get('customers'),
                invoices_engine=self._engines.get('invoices'),
                services_engine=self._engines.get('services'),
                parent=self._view
            )
        )

        # --- Invoice Table: Only needs the 'invoices' engine ---
        self.page_manager.register(
            "invoice_table",
            lambda: InvoiceTableFactory.create(
                invoices_engine=self._engines.get('invoices'),
                parent=self._view
            )
        )

        self.page_manager.register(
            "services",
            lambda: ServicesManagementFactory.create(
                services_engine=self._engines.get('services'),
                parent=self._view
            )
        )

        self.page_manager.register(
            'info_page',
            lambda: InfoPageFactory.create(
                info_page_engine=self._engines.get('info_page'),
                parent=self._view
            )
        )

        self.page_manager.register(
            'workspace',
            lambda: WorkspaceFactory.create(
                self._engines.get('users'),
                self._engines.get('workspace'),
                self._logic.get_user_profile_for_view(self._username).id,
                self.broker_host,
                self._view
            )
        )
        print("Pages registered with PageManager.")

    def _connect_signals(self):
        """Connect signals from the _view to slots in this controller."""
        # --- Sidebar Navigation to use the PageManager ---
        self._view.home_button.clicked.connect(lambda: self.page_manager.show("home"))
        self._view.invoice_button.clicked.connect(lambda: self.page_manager.show("invoice"))
        self._view.large_user_pic.clicked.connect(lambda: self.page_manager.show("users"))
        self._view.issued_invoices_button.clicked.connect(lambda: self.page_manager.show('invoice_table'))
        self._view.documents_button.clicked.connect(lambda: self.page_manager.show('services'))
        self._view.help_button.clicked.connect(lambda: self.page_manager.show('info_page'))
        self._view.workspace_button.clicked.connect(lambda: self.page_manager.show('workspace'))
        self._view.settings_button_clicked.connect(self._on_settings_button_clicked)

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

        # --- 3. Show the default page on startup ---
        self.page_manager.show("home")

    # --- Slots for View Signals ---

    def _toggle_maximize(self):
        """Toggles the window between maximized and normal states."""
        if self._view.isMaximized():
            self._view.showNormal()
        else:
            self._view.showMaximized()

    def _on_home_button_clicked(self):
        """Handle the user clicking the 'Home' button."""
        print("Controller: Home button clicked.")
        self.page_manager.show("home")

    def _on_invoice_button_clicked(self):
        """Handle the user clicking the 'Invoice' button."""
        print("Controller: Invoice button clicked.")
        self.page_manager.show("invoice")

    def _on_settings_button_clicked(self):
        """Handle the user clicking the 'Settings' button."""
        print("Controller: Settings button clicked.")
        self.page_manager.show("settings")

    def _on_user_profile_clicked(self):
        """Handle the user clicking their profile picture or name."""
        print("Controller: User profile clicked. Switching to user page.")
        self.page_manager.show("user")

    def _on_close_button_clicked(self):
        """
        Handles the user clicking the 'X' button in the title bar.
        Instructs the _view to begin its close confirmation process.
        """
        print("Controller: Close button clicked. Telling _view to handle close request.")
        self._view.handle_close_request()
