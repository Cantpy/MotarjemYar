# features/Main_Window/main_window_controller.py

from PySide6.QtCore import QObject
from core.navigation import PageManager

from features.Main_Window.main_window_view import MainWindowView
from features.Main_Window.main_window_logic import MainWindowLogic

from features.Home_Page.home_page_factory import HomePageFactory
from features.Invoice_Page.wizard_host.invoice_wizard_factory import InvoiceWizardFactory
from features.Admin_Panel.host_tab.host_tab_factory import AdminPanelFactory
from features.Invoice_Table.invoice_table_factory import InvoiceTableFactory
from features.Services.tab_manager.tab_manager_factory import ServicesManagementFactory
from features.Info_Page.info_page_factory import InfoPageFactory


class MainWindowController(QObject):
    """
    Controller for the main application window.
    Connects user actions from the _view to the application's business _logic.
    """

    def __init__(self, view: "MainWindowView", logic: "MainWindowLogic"):
        super().__init__()

        self._view = view
        self._logic = logic

        self.page_manager = PageManager(self._view.stackedWidget)
        self._register_pages()

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
        session_provider = self._logic.session_provider

        # --- Home Page Registration ---
        self.page_manager.register(
            "home",
            lambda: HomePageFactory.create(
                session_provider,
                self._view
            )
        )

        # --- Invoice Page Registration ---
        self.page_manager.register(
            "invoice",
            lambda: InvoiceWizardFactory.create(
                session_provider,
                self._view
            )
        )

        # --- Users Page Registration ---
        self.page_manager.register(
            "users",
            lambda: AdminPanelFactory.create(
                session_provider,
                self._view
            )
        )

        # --- Invoice Table Page Registration ---
        self.page_manager.register(
            "invoice_table",
            lambda: InvoiceTableFactory.create(
                session_provider,
                self._view
            )
        )

        self.page_manager.register(
            "services",
            lambda: ServicesManagementFactory.create(
                session_provider,
                self._view
            )
        )

        self.page_manager.register(
            'info_page',
            lambda: InfoPageFactory.create(
                session_provider,
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
