# features/Admin_Panel/translation_office_info/translation_office_info_controller.py

from PySide6.QtCore import QObject
from features.Admin_Panel.translation_office_info.translation_office_info_view import TranslationOfficeInfoView
from features.Admin_Panel.translation_office_info.translation_office_info_logic import TranslationOfficeInfoLogic


class TranslationOfficeInfoController(QObject):
    """
    Orchestrates the Translation Office Info feature. It initializes the
    view with data from the logic layer.
    """
    def __init__(self, view: TranslationOfficeInfoView, logic: TranslationOfficeInfoLogic):
        super().__init__()
        self._view = view
        self._logic = logic

        self._load_initial_data()

    def _load_initial_data(self):
        """
        Asks the logic layer for the office data and tells the view to display it.
        """
        office_data_dto = self._logic.get_office_display_data()
        self._view.display_info(office_data_dto)

    def get_view(self) -> TranslationOfficeInfoView:
        """ Returns the view managed by this controller. """
        return self._view
