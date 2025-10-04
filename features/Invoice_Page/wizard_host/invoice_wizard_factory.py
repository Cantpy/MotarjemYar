# features/Invoice_Page/wizard_host/invoice_wizard_factory.py

from sqlalchemy.engine import Engine

from features.Invoice_Page.wizard_host.invoice_wizard_view import InvoiceWizardWidget
from features.Invoice_Page.wizard_host.invoice_wizard_controller import InvoiceWizardController
from features.Invoice_Page.wizard_host.invoice_page_wizard_logic import InvoiceWizardLogic

from features.Invoice_Page.customer_info.customer_info_factory import CustomerInfoFactory
from features.Invoice_Page.document_selection.document_selection_factory import DocumentSelectionFactory
from features.Invoice_Page.invoice_details.invoice_details_factory import InvoiceDetailsFactory
from features.Invoice_Page.invoice_preview.invoice_preview_factory import InvoicePreviewFactory
from features.Invoice_Page.document_assignment.document_assignment_view import AssignmentWidget
from features.Invoice_Page.invoice_page_state_manager import WorkflowStateManager


class InvoiceWizardFactory:
    """
    The master factory that assembles the entire invoice creation workflow.
    """

    @staticmethod
    def create(customer_engine: Engine,
               invoices_engine: Engine,
               services_engine: Engine,
               users_engine: Engine,
               parent=None) -> InvoiceWizardController:

        state_manager = WorkflowStateManager()
        sub_controllers = {
            'customer': CustomerInfoFactory.create(customer_engine=customer_engine,
                                                   state_manager=state_manager),
            'documents': DocumentSelectionFactory.create(services_engine=services_engine,
                                                         state_manager=state_manager),
            'assignment': AssignmentWidget(state_manager=state_manager),
            'details': InvoiceDetailsFactory.create(users_engine=users_engine, invoices_engine=invoices_engine,
                                                    state_manager=state_manager),
            'preview': InvoicePreviewFactory.create(invoices_engine=invoices_engine,
                                                    state_manager=state_manager)
        }

        wizard_view = InvoiceWizardWidget(parent=parent)
        wizard_logic = InvoiceWizardLogic()

        wizard_controller = InvoiceWizardController(
            view=wizard_view,
            logic=wizard_logic,
            state_manager=state_manager,
            sub_controllers=sub_controllers
        )

        return wizard_controller


if __name__ == '__main__':
    from shared.testing.launch_feature import launch_feature_for_ui_test
    launch_feature_for_ui_test(
        factory_class=InvoiceWizardFactory,
        required_engines={'customers': 'customer_engine',
                          'invoices': 'invoices_engine',
                          'services': 'services_engine',
                          'users': 'users_engine'},
        use_memory_db=True
    )
