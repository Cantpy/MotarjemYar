# features/Services/tab_manager/tab_manager_controller.py

from PySide6.QtCore import QObject


class ServicesManagementController(QObject):
    """
    Manages the ServicesManagementView and coordinates the sub-controllers for each tab.
    """

    def __init__(self,
                 view: "ServicesManagementView",
                 documents_controller,
                 fixed_prices_controller,
                 other_services_controller):
        super().__init__()
        self._view = view

        # Store the sub-controllers as dependencies
        self._documents_controller = documents_controller
        self._fixed_prices_controller = fixed_prices_controller
        self._other_services_controller = other_services_controller

        self._connect_signals()

    def get_view(self) -> "ServicesManagementView":
        """Provides the assembled view, adhering to the application pattern."""
        return self._view

    def _connect_signals(self):
        """Connects the container view's signals to this controller's slots."""
        self._view.refresh_all_requested.connect(self.handle_refresh_all)

    def handle_refresh_all(self):
        """Orchestrates a refresh action across all sub-modules."""
        # This controller tells each sub-controller to reload its data.
        self._documents_controller.load_initial_data()
        self._fixed_prices_controller.load_initial_data()
        self._other_services_controller.load_initial_data()

