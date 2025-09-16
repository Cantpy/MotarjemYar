# features/Info_Page/info_page_controller.py

from PySide6.QtCore import QObject
from features.Info_Page.info_page_view import InfoPageView
from features.Info_Page.info_page_logic import InfoPageLogic


class InfoPageController(QObject):
    """Controller for the info page."""

    def __init__(self, view: InfoPageView, logic: InfoPageLogic):
        """Initializes the controller with a view and logic."""
        super().__init__()
        self._view = view
        self._logic = logic
        self._connect_signals()

    def get_view(self) -> InfoPageView:
        """Returns the view instance, required for the page_manager."""
        return self._view

    def load_initial_data(self):
        """Fetches and loads all necessary data into the view."""
        info_data = self._logic.get_info_page_data()

        # Populate Version Info
        self._view.set_version_info(
            info_data.version_info.version_number,
            info_data.version_info.release_date
        )

        # Populate Changelog
        changelog_descriptions = [entry.description for entry in info_data.changelog]
        self._view.set_changelog(changelog_descriptions)

        # Populate FAQ
        self._view.set_faq(info_data.faq_items)

    def _connect_signals(self):
        """Connect signals from the view to handler methods."""
        self._view.feedback_button.clicked.connect(self._handle_feedback_button)

    def _handle_feedback_button(self):
        """Performer method to handle the feedback button click."""
        # In a real app, this might open a feedback dialog or a web link
        print("Feedback button clicked! This would open a feedback form.")
