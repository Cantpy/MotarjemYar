# features/Admin_Panel/translation_office_info/translation_office_info_repo.py

from sqlalchemy.orm import Session

from shared.orm_models.users_models import TranslationOfficeDataModel


class TranslationOfficeInfoRepository:
    """
    Stateless repository for accessing translation office information from the database.
    """
    def get_office_info(self, session: Session) -> TranslationOfficeDataModel | None:
        """
        Retrieves the first record of translation office information.
        In a real application, you might have a more specific way to identify the office.
        """
        return session.query(TranslationOfficeDataModel).first()
