# features/Admin_Panel/translation_office_info/translation_office_info_logic.py

from features.Admin_Panel.translation_office_info.translation_office_info_repo import TranslationOfficeInfoRepository
from shared.orm_models.users_models import TranslationOfficeData
from shared.session_provider import ManagedSessionProvider


class TranslationOfficeInfoLogic:
    """
    Handles the business logic for the Translation Office Info feature.
    It uses the repository to fetch data and maps it to a DTO for the view.
    """

    def __init__(self, business_engine: ManagedSessionProvider,
                 repository: TranslationOfficeInfoRepository):
        self._business_session = business_engine
        self._repository = repository

    def get_office_display_data(self) -> TranslationOfficeData:
        """
        Fetches office data and prepares it for display.

        Returns:
            A DTO containing the office name and registration number.
        """
        try:
            with self._business_session as session:
                office_orm = self._repository.get_office_info(session)
                if office_orm:
                    return TranslationOfficeData(
                        id=office_orm.id,
                        license_key=office_orm.license_key,
                        name=office_orm.name,
                        reg_no=office_orm.reg_no or "ثبت نشده",
                        representative=office_orm.representative,
                        manager=office_orm.manager,
                        address=office_orm.address,
                        phone=office_orm.phone,
                        email=office_orm.email,
                        website=office_orm.website,
                        whatsapp=office_orm.whatsapp,
                        instagram=office_orm.instagram,
                        telegram=office_orm.telegram,
                        other_media=office_orm.other_media,
                        open_hours=office_orm.open_hours,
                        logo=office_orm.logo,
                        map_url=office_orm.map_url,
                        created_at=office_orm.created_at,
                        updated_at=office_orm.updated_at
                    )
        except Exception as e:
            print(f"Error fetching office info: {e}")
