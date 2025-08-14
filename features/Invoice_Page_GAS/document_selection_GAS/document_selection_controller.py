# document_selection/controller.py
from typing import List
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_logic import DocumentSelectionLogic
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import Service, FixedPrice


class DocumentSelectionController:
    def __init__(self):
        self._logic = DocumentSelectionLogic()

    def get_all_services(self) -> List[Service]:
        """Provides a list of all services for the view."""
        return self._logic.get_all_services()

    def get_calculation_fees(self) -> List[FixedPrice]:
        return self._logic.get_calculation_fees()
