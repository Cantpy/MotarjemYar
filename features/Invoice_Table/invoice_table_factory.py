# features/Invoice_Table/invoice_table_factory.py

from sqlalchemy import Engine

from features.Invoice_Table.invoice_table_repo import RepositoryManager
from features.Invoice_Table.invoice_table_view import InvoiceTableView
from features.Invoice_Table.invoice_table_logic import (InvoiceLogic, InvoiceService, SearchService, SettingsService,
                                                        InvoiceExportService, FileService,
                                                        ValidationService, NumberFormatService)
from features.Invoice_Table.invoice_table_controller import InvoiceTableController

from shared.session_provider import ManagedSessionProvider


class InvoiceTableFactory:
    """
    Factory class for creating and wiring up the Invoice Table feature components.
    """
    @staticmethod
    def create(invoices_engine: Engine, users_engine: Engine,
               services_engine: Engine, payroll_engine: Engine, parent=None) -> InvoiceTableController:
        """
        Creates and wires up all components for the Invoice Table feature.
        Args:
            invoices_engine: SQLAlchemy engine for the invoices database.
            users_engine: SQLAlchemy engine for the users database.
            services_engine: SQLAlchemy engine for the services database.
            payroll_engine: SQLAlchemy engine for the payroll database.
            parent: Optional parent widget.
        Returns:
            An initialized InvoiceTableController.
        """
        invoices_session = ManagedSessionProvider(engine=invoices_engine)
        users_session = ManagedSessionProvider(engine=users_engine)
        services_session = ManagedSessionProvider(engine=services_engine)
        payroll_session = ManagedSessionProvider(engine=payroll_engine)  # Create payroll session

        invoice_table_view = InvoiceTableView(parent=parent)

        repo_manager = RepositoryManager()

        settings_service = SettingsService()
        file_service = FileService()
        validation_service = ValidationService()
        search_service = SearchService()
        invoice_service = InvoiceService(repo_manager=repo_manager,
                                        invoices_engine=invoices_session,
                                        users_engine=users_session,
                                        services_engine=services_session,
                                        payroll_engine=payroll_session)
        export_service = InvoiceExportService(invoice_service=invoice_service)
        format_service = NumberFormatService()

        logic = InvoiceLogic(
            invoice_service=invoice_service,
            settings_service=settings_service,
            file_service=file_service,
            validation_service=validation_service,
            search_service=search_service,
            export_service=export_service,
            format_service=format_service
        )

        invoice_table_controller = InvoiceTableController(view=invoice_table_view, logic=logic)

        invoice_table_controller.load_initial_data()

        return invoice_table_controller


if __name__ == "__main__":
    from shared.testing.launch_feature import launch_feature_for_ui_test
    # Update the test launcher to include the required payroll engine
    launch_feature_for_ui_test(
        factory_class=InvoiceTableFactory,
        required_engines={
            'invoices': 'invoices_engine',
            'users': 'users_engine',
            'services': 'services_engine',
            'payroll': 'payroll_engine'
        },
        use_memory_db=True
    )
