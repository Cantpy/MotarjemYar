# document_selection/logic.py
from typing import List
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_repo import DocumentSelectionRepository
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import Service, FixedPrice


class DocumentSelectionLogic:
    def __init__(self):
        self._repo = DocumentSelectionRepository()

    def get_all_services(self) -> List[Service]:
        return self._repo.get_all_services()

    def get_calculation_fees(self) -> List[FixedPrice]:
        return self._repo.get_calculation_fees()
