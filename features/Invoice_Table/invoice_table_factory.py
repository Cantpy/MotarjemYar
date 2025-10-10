# features/Invoice_Table/invoice_table_factory.py

from sqlalchemy import Engine

from features.Invoice_Table.invoice_table_repo import RepositoryManager
from features.Invoice_Table.invoice_table_view import InvoiceTableView
from features.Invoice_Table.invoice_table_logic import (InvoiceLogic, InvoiceService, SearchService, SettingsService,
                                                        InvoiceExportService, FileService,
                                                        ValidationService, NumberFormatService)
from features.Invoice_Table.invoice_table_controller import MainController

from shared.session_provider import ManagedSessionProvider


class InvoiceTableFactory:
    """

    """
    @staticmethod
    def create(invoices_engine: Engine, users_engine: Engine,
               services_engine: Engine, parent=None) -> MainController:
        """

        """
        invoices_session = ManagedSessionProvider(engine=invoices_engine)
        users_session = ManagedSessionProvider(engine=users_engine)
        services_session = ManagedSessionProvider(engine=services_engine)

        invoice_table_view = InvoiceTableView(parent=parent)

        repo_manager = RepositoryManager()

        settings_service = SettingsService()
        file_service = FileService()
        validation_service = ValidationService()
        search_service = SearchService()
        invoice_servie = InvoiceService(repo_manager=repo_manager,
                                        invoices_engine=invoices_session,
                                        users_engine=users_session,
                                        services_engine=services_session)
        export_service = InvoiceExportService(invoice_service=invoice_servie)
        format_service = NumberFormatService()

        logic = InvoiceLogic(
            invoice_service=invoice_servie,
            settings_service=settings_service,
            file_service=file_service,
            validation_service=validation_service,
            search_service=search_service,
            export_service=export_service,
            format_service=format_service
        )

        invoice_table_controller = MainController(view=invoice_table_view, logic=logic)

        invoice_table_controller.load_initial_data()

        return invoice_table_controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoiceTableFactory,
        required_engines={'invoices': 'invoices_engine'},
        use_memory_db=True
    )
