# features/Info_Page/info_page_repo.py

from typing import List
from sqlalchemy.orm import Session
from shared.orm_models.info_page_models import Version, Changelog, FAQ
from features.Info_Page.info_page_models import VersionInfoDTO, ChangelogEntryDTO, FAQItemDTO


class InfoPageRepository:
    """Stateless repository for fetching info page data."""

    def get_latest_version(self, session: Session) -> VersionInfoDTO:
        """Fetches the most recent version information."""
        latest_version_orm = session.query(Version).order_by(Version.id.desc()).first()
        if latest_version_orm:
            return VersionInfoDTO(
                version_number=latest_version_orm.version_number,
                release_date=latest_version_orm.release_date
            )
        return VersionInfoDTO(version_number="N/A", release_date="N/A")

    def get_changelog_for_latest_version(self, session: Session) -> List[ChangelogEntryDTO]:
        """Fetches the changelog for the most recent version."""
        latest_version_orm = session.query(Version).order_by(Version.id.desc()).first()
        if not latest_version_orm:
            return []

        changelog_orms = session.query(Changelog).filter(Changelog.version_id == latest_version_orm.id).all()
        return [ChangelogEntryDTO(description=entry.change_description) for entry in changelog_orms]

    def get_all_faqs(self, session: Session) -> List[FAQItemDTO]:
        """Fetches all FAQ items."""
        faq_orms = session.query(FAQ).all()
        return [FAQItemDTO(question=item.question, answer=item.answer) for item in faq_orms]
