# core/navigation.py

from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtCore import QTimer, QObject
from typing import Callable, Dict, Optional


class PageManager:
    """
    Manages the lifecycle and navigation of page controllers.
    It creates and caches controllers, and asks them for their views to display.
    """

    def __init__(self, stacked_widget: QStackedWidget):
        self.stacked_widget = stacked_widget
        # These now store controllers (which are QObjects)
        self._factories: Dict[str, Callable[[], QObject]] = {}
        self._instances: Dict[str, QObject] = {}

    def register(self, name: str, factory: Callable[[], QObject]):
        """Register a factory function that creates the CONTROLLER for a page."""
        self._factories[name] = factory

    def get_controller(self, name: str) -> QObject:
        """Get an instance of the page's controller, creating it if necessary."""
        if name in self._instances:
            return self._instances[name]

        if name not in self._factories:
            raise ValueError(f"No factory registered for page controller: {name}")

        controller = self._factories[name]()
        self._instances[name] = controller
        return controller

    def show(self, name: str):
        """Shows a page by getting its controller and asking for its _view."""
        # 1. Get the controller for the page
        controller = self.get_controller(name)

        # 2. CRITICAL: Ask the controller for its _view
        #    We assume all our page controllers have a get_view() method.
        page_view = controller.get_view()

        # 3. Add the _view to the stacked widget if it's not already there
        #    (This check prevents adding the same widget multiple times)
        if self.stacked_widget.indexOf(page_view) == -1:
            self.stacked_widget.addWidget(page_view)

        # 4. Show the _view
        self.stacked_widget.setCurrentWidget(page_view)

    def preload(self, name: str, delay_ms: int = 100):
        """Preloads a page's controller after a short delay."""
        QTimer.singleShot(delay_ms, lambda: self.get_controller(name))

    def clear_cache(self):
        """Removes and deletes all cached pages and their controllers."""
        for name, controller in list(self._instances.items()):
            # Get the _view from the controller
            view = controller.get_view()
            if view:
                self.stacked_widget.removeWidget(view)
                view.deleteLater()  # Schedule the _view for deletion

            # The controller is a QObject, it can also be scheduled for deletion
            # if it has no parent or its parent is being deleted.
            if hasattr(controller, 'deleteLater'):
                controller.deleteLater()

            del self._instances[name]
