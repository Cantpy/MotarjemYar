# features/Invoice_Table/invoice_table_factory.py

from sqlalchemy.engine import Engine

from features.Invoice_Table.invoice_table_repo import RepositoryManager
from features.Invoice_Table.invoice_table_view import InvoiceTableView
from features.Invoice_Table.invoice_table_logic import (SearchService, InvoiceTableService, InvoiceExportService,
                                                        SortService, FileService, ValidationService,
                                                        NumberFormatService, BulkOperationService)
from features.Invoice_Table.invoice_table_controller import MainController

from shared.session_provider import ManagedSessionProvider


class InvoiceTableFactory:
    """

    """
    @staticmethod
    def create(invoices_engine, parent=None) -> MainController:
        """

        """
        invoices_session = ManagedSessionProvider(engine=invoices_engine)
        invoice_table_view = InvoiceTableView(parent=parent)
        repo_manager = RepositoryManager()
        search_service = SearchService()
        invoice_service = InvoiceTableService(repo_manager, invoices_session)
        export_service = InvoiceExportService()
        sort_service = SortService()
        file_service = FileService()
        validation_service = ValidationService()
        formatting_srvice = NumberFormatService()
        operation_srvice = BulkOperationService()

        invoice_table_controller = MainController(view=invoice_table_view,
                                                  invoice_service=invoice_service,
                                                  search_service=search_service,
                                                  export_service=export_service,
                                                  sort_service=sort_service,
                                                  file_service=file_service,
                                                  validation_service=validation_service,
                                                  format_service=formatting_srvice,
                                                  operation_service=operation_srvice)

        return invoice_table_controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoiceTableFactory,
        required_engines={'invoices': 'invoices_engine'},
        use_memory_db=True
    )
