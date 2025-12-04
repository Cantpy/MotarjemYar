# features/Admin_Panel/translation_office_info/translation_office_info_factory.py

from sqlalchemy.engine import Engine

from features.Admin_Panel.translation_office_info.translation_office_info_controller import TranslationOfficeInfoController
from features.Admin_Panel.translation_office_info.translation_office_info_view import TranslationOfficeInfoView
from features.Admin_Panel.translation_office_info.translation_office_info_logic import TranslationOfficeInfoLogic
from features.Admin_Panel.translation_office_info.translation_office_info_repo import TranslationOfficeInfoRepository

from shared.session_provider import ManagedSessionProvider


class TranslationOfficeInfoFactory:
    """
    Factory for creating the Translation Office Info feature.
    """
    @staticmethod
    def create(business_engine: Engine, parent=None) -> TranslationOfficeInfoController:
        """
        Creates and returns a fully assembled Translation Office Info controller
        by wiring up the view, logic, and repository.
        """
        users_session = ManagedSessionProvider(business_engine)
        view = TranslationOfficeInfoView(parent=parent)
        repository = TranslationOfficeInfoRepository()
        logic = TranslationOfficeInfoLogic(business_engine=users_session, repository=repository)
        controller = TranslationOfficeInfoController(view=view, logic=logic)
        return controller
