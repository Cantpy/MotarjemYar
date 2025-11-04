# core/navigation.py

from PySide6.QtWidgets import QStackedWidget
from PySide6.QtCore import QTimer, QObject
from enum import Enum
from typing import Callable, Dict


class PageLifetime(Enum):
    KEEP_ALIVE = 1       # Keep the controller/view alive once created
    REFRESH_ON_SHOW = 2  # Destroy and recreate each time it's shown
    TIMEOUT = 3          # (Optional future use)


class PageManager:
    """
    Manages the lifecycle and navigation of page controllers.
    Supports selective caching via lifetime policies.
    """

    def __init__(self, stacked_widget: QStackedWidget):
        self.stacked_widget = stacked_widget
        self._factories: Dict[str, Callable[[], QObject]] = {}
        self._instances: Dict[str, QObject] = {}
        self._lifetimes: Dict[str, PageLifetime] = {}

    def register(self, name: str, factory: Callable[[], QObject],
                 lifetime: PageLifetime = PageLifetime.KEEP_ALIVE):
        """Register a page factory and its caching policy."""
        self._factories[name] = factory
        self._lifetimes[name] = lifetime

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
        """Show a page, respecting its lifetime policy."""
        if name not in self._factories:
            raise ValueError(f"No factory registered for page '{name}'")

        lifetime = self._lifetimes.get(name, PageLifetime.KEEP_ALIVE)

        # Recreate page if refresh policy
        if lifetime == PageLifetime.REFRESH_ON_SHOW and name in self._instances:
            self._destroy_page(name)

        controller = self.get_controller(name)
        page_view = controller.get_view()

        if self.stacked_widget.indexOf(page_view) == -1:
            self.stacked_widget.addWidget(page_view)

        self.stacked_widget.setCurrentWidget(page_view)

    def _destroy_page(self, name: str):
        """Safely remove a page and its controller."""
        controller = self._instances.pop(name, None)
        if not controller:
            return
        view = getattr(controller, "get_view", lambda: None)()
        if view:
            self.stacked_widget.removeWidget(view)
            view.deleteLater()
        if hasattr(controller, "deleteLater"):
            controller.deleteLater()

    def preload(self, name: str, delay_ms: int = 100):
        """Preloads a page after a short delay (useful for heavy pages)."""
        if name not in self._factories:
            return
        QTimer.singleShot(delay_ms, lambda: self.get_controller(name))

    def clear_cache(self):
        """Deletes all cached controllers and their views."""
        for name in list(self._instances.keys()):
            self._destroy_page(name)
