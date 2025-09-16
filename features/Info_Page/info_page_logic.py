# features/Info_Page/info_page_logic.py

from .info_page_repo import InfoPageRepository
from .info_page_models import InfoPageDataDTO
from shared.session_provider import SessionProvider


class InfoPageLogic:
    """Business logic for the info page."""

    def __init__(self, repo: InfoPageRepository, session_provider: "SessionProvider"):
        """
        Initializes the logic with a repository and session provider.

        Args:
            repo (InfoPageRepository): The data repository.
            session_provider: A class that provides database sessions.
        """
        self._repo = repo
        self._session_provider = session_provider

    def get_info_page_data(self) -> InfoPageDataDTO:
        """
        Retrieves all necessary data for the info page.

        Returns:
            InfoPageDataDTO: A DTO containing all display data.
        """
        with self._session_provider.info_page() as session:
            version_info = self._repo.get_latest_version(session)
            changelog = self._repo.get_changelog_for_latest_version(session)
            faq_items = self._repo.get_all_faqs(session)

            return InfoPageDataDTO(
                version_info=version_info,
                changelog=changelog,
                faq_items=faq_items
            )