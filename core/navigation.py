from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtCore import QTimer
from typing import Callable, Dict, Optional


class PageManager:
    def __init__(self, stacked_widget: QStackedWidget, parent: Optional[object] = None):
        self.stacked_widget = stacked_widget
        self.parent = parent
        self._factories: Dict[str, Callable[[], QWidget]] = {}
        self._instances: Dict[str, QWidget] = {}

    def register(self, name: str, factory: Callable[[], QWidget]):
        """Register a factory function that creates the widget for a page"""
        self._factories[name] = factory

    def get(self, name: str) -> QWidget:
        """Get an instance of the page, creating it if necessary"""
        if name in self._instances:
            return self._instances[name]

        if name not in self._factories:
            raise ValueError(f"No factory registered for page: {name}")

        widget = self._factories[name]()
        self.stacked_widget.addWidget(widget)
        self._instances[name] = widget
        return widget

    def show(self, name: str):
        """Show a page by name, creating it lazily if needed"""
        if name in self._instances:
            page = self._instances[name]
        else:
            if name not in self._factories:
                raise ValueError(f"Unknown page name: {name}")
            page = self._factories[name]()
            self._instances[name] = page
            self.stacked_widget.addWidget(page)

            # Apply permissions on first load if available
            if hasattr(page, 'set_permissions') and self.parent and hasattr(self.parent, 'permissions'):
                page.set_permissions(self.parent.permissions)

        self.stacked_widget.setCurrentWidget(page)

    def preload(self, name: str, delay_ms: int = 0):
        """Preload a page after a delay (default = immediately)"""
        QTimer.singleShot(delay_ms, lambda: self.get(name))

    def clear_cache(self):
        """Clear cached pages except home page"""
        for page_name, page in list(self._instances.items()):
            if page_name != 'home' and page is not None:
                # Remove from stacked widget first
                self.stacked_widget.removeWidget(page)
                # Then delete the widget
                if hasattr(page, 'deleteLater'):
                    page.deleteLater()
                # Remove from instances dict
                del self._instances[page_name]
