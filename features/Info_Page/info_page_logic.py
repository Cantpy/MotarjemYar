# features/Info_Page/info_page_logic.py

from features.Info_Page.info_page_repo import InfoPageRepository
from features.Info_Page.info_page_models import InfoPageDataDTO
from shared.session_provider import ManagedSessionProvider


class InfoPageLogic:
    """Business _logic for the info page."""

    def __init__(self, repo: InfoPageRepository,
                 info_pge_engine: ManagedSessionProvider):
        """
        Initializes the _logic with a _repository and session provider.

        Args:
            repo (InfoPageRepository): The data _repository.
            info_pge_engine: The session provider for database access.
        """
        self._repo = repo
        self._info_page_session = info_pge_engine

    def get_info_page_data(self) -> InfoPageDataDTO:
        """
        Retrieves all necessary data for the info page.

        Returns:
            InfoPageDataDTO: A DTO containing all display data.
        """
        with self._info_page_session() as session:
            version_info = self._repo.get_latest_version(session)
            changelog = self._repo.get_changelog_for_latest_version(session)
            faq_items = self._repo.get_all_faqs(session)

            return InfoPageDataDTO(
                version_info=version_info,
                changelog=changelog,
                faq_items=faq_items
            )