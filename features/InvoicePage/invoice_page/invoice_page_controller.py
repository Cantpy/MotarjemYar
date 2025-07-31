from PySide6.QtCore import QObject, Signal
from typing import Optional, Any, Dict
from invoice_page_models import WizardData, WizardSteps


class InvoicePageController(QObject):
    """Controller for managing invoice wizard navigation and data."""

    # Signals
    step_changed = Signal(int)  # current_step_index
    step_completed = Signal(int, dict)  # step_index, step_data
    wizard_finished = Signal(dict)  # complete_invoice_data
    validation_error = Signal(str)  # error_message
    data_updated = Signal()  # data has been updated

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step = WizardSteps.CUSTOMER
        self.wizard_data = WizardData()
        self._step_views = {}  # Will hold references to step views

    def register_step_view(self, step_index: int, view_widget):
        """Register a step view widget with the controller."""
        self._step_views[step_index] = view_widget

    def get_current_step(self) -> int:
        """Get current step index."""
        return self.current_step

    def get_wizard_data(self) -> WizardData:
        """Get complete wizard data."""
        return self.wizard_data

    def set_wizard_data(self, data: WizardData):
        """Set wizard data."""
        self.wizard_data = data
        self._populate_all_views()
        self.data_updated.emit()

    def go_to_step(self, step_index: int, validate_current: bool = True) -> bool:
        """Navigate to specific step."""
        if validate_current and not self._validate_current_step():
            return False

        if 0 <= step_index < WizardSteps.TOTAL_STEPS:
            self._save_current_step_data()
            self.current_step = step_index
            self._populate_current_view()
            self.step_changed.emit(self.current_step)
            return True
        return False

    def go_next(self) -> bool:
        """Navigate to next step."""
        if not self._validate_current_step():
            return False

        if self.current_step < WizardSteps.TOTAL_STEPS - 1:
            self._save_current_step_data()
            self.current_step += 1
            self._populate_current_view()
            self.step_changed.emit(self.current_step)
            return True
        else:
            # Last step - finish wizard
            return self._finish_wizard()

    def go_back(self) -> bool:
        """Navigate to previous step."""
        if self.current_step > 0:
            self._save_current_step_data()
            self.current_step -= 1
            self._populate_current_view()
            self.step_changed.emit(self.current_step)
            return True
        return False

    def can_go_next(self) -> bool:
        """Check if can navigate to next step."""
        return self._validate_current_step()

    def can_go_back(self) -> bool:
        """Check if can navigate to previous step."""
        return self.current_step > 0

    def is_last_step(self) -> bool:
        """Check if current step is the last one."""
        return self.current_step == WizardSteps.TOTAL_STEPS - 1

    def reset_wizard(self):
        """Reset wizard to initial state."""
        self.wizard_data.reset()
        self.current_step = WizardSteps.CUSTOMER
        self._populate_all_views()
        self.step_changed.emit(self.current_step)
        self.data_updated.emit()

    def update_customer_data(self, customer_data: Dict[str, Any]):
        """Update customer data."""
        self.wizard_data.customer.name = customer_data.get('name', '')
        self.wizard_data.customer.national_id = customer_data.get('national_id', '')
        self.wizard_data.customer.phone = customer_data.get('phone', '')
        self.wizard_data.customer.email = customer_data.get('email', '')
        self.wizard_data.customer.address = customer_data.get('address', '')
        self.data_updated.emit()

    def update_documents_data(self, documents_data: list):
        """Update documents data."""
        self.wizard_data.documents.clear()
        for doc_data in documents_data:
            from invoice_page_models import DocumentData
            doc = DocumentData(
                name=doc_data.get('name', ''),
                doc_type=doc_data.get('doc_type', ''),
                pages=doc_data.get('pages', 0),
                source_language=doc_data.get('source_language', ''),
                target_language=doc_data.get('target_language', ''),
                cost=doc_data.get('cost', 0.0)
            )
            self.wizard_data.documents.append(doc)

        # Update total amount in invoice details
        total_cost = self.wizard_data.calculate_total_cost()
        self.wizard_data.invoice_details.total_amount = total_cost
        self.data_updated.emit()

    def update_invoice_details_data(self, details_data: Dict[str, Any]):
        """Update invoice details data."""
        self.wizard_data.invoice_details.receipt_number = details_data.get('receipt_number', '')
        self.wizard_data.invoice_details.receive_date = details_data.get('receive_date',
                                                                         self.wizard_data.invoice_details.receive_date)
        self.wizard_data.invoice_details.delivery_date = details_data.get('delivery_date',
                                                                          self.wizard_data.invoice_details.delivery_date)
        self.wizard_data.invoice_details.username = details_data.get('username', '')
        self.wizard_data.invoice_details.total_amount = details_data.get('total_amount', 0.0)
        self.wizard_data.invoice_details.discount_amount = details_data.get('discount_amount', 0.0)
        self.wizard_data.invoice_details.advance_payment = details_data.get('advance_payment', 0.0)
        self.wizard_data.invoice_details.remarks = details_data.get('remarks', '')
        self.data_updated.emit()

    def update_preview_settings_data(self, settings_data: Dict[str, Any]):
        """Update preview settings data."""
        self.wizard_data.preview_settings.paper_size = settings_data.get('paper_size', 'A4')
        self.wizard_data.preview_settings.show_logo = settings_data.get('show_logo', True)
        self.wizard_data.preview_settings.custom_header = settings_data.get('custom_header', '')
        self.wizard_data.preview_settings.custom_footer = settings_data.get('custom_footer', '')
        self.data_updated.emit()

    def update_sharing_options_data(self, sharing_data: Dict[str, Any]):
        """Update sharing options data."""
        self.wizard_data.sharing_options.email_enabled = sharing_data.get('email_enabled', True)
        self.wizard_data.sharing_options.additional_emails = sharing_data.get('additional_emails', '')
        self.wizard_data.sharing_options.email_subject = sharing_data.get('email_subject', '')
        self.wizard_data.sharing_options.email_message = sharing_data.get('email_message', '')
        self.wizard_data.sharing_options.whatsapp_enabled = sharing_data.get('whatsapp_enabled', False)
        self.wizard_data.sharing_options.telegram_enabled = sharing_data.get('telegram_enabled', False)
        self.wizard_data.sharing_options.sms_enabled = sharing_data.get('sms_enabled', False)
        self.wizard_data.sharing_options.selected_template = sharing_data.get('selected_template', '')
        self.data_updated.emit()

    def get_step_completion_status(self) -> Dict[int, bool]:
        """Get completion status for all steps."""
        return {i: self.wizard_data.is_step_valid(i) for i in range(WizardSteps.TOTAL_STEPS)}

    def _validate_current_step(self) -> bool:
        """Validate current step data."""
        is_valid = self.wizard_data.is_step_valid(self.current_step)

        if not is_valid:
            if self.current_step == WizardSteps.CUSTOMER:
                self.validation_error.emit("لطفاً نام مشتری را وارد کنید")
            elif self.current_step == WizardSteps.DOCUMENTS:
                self.validation_error.emit("لطفاً حداقل یک سند اضافه کنید")
            elif self.current_step == WizardSteps.INVOICE_DETAILS:
                self.validation_error.emit("لطفاً شماره رسید را وارد کنید")

        return is_valid

    def _save_current_step_data(self):
        """Save current step data from view to model."""
        if self.current_step in self._step_views:
            view = self._step_views[self.current_step]

            if hasattr(view, 'get_data'):
                data = view.get_data()

                if self.current_step == WizardSteps.CUSTOMER:
                    self.update_customer_data(data)
                elif self.current_step == WizardSteps.DOCUMENTS:
                    self.update_documents_data(data)
                elif self.current_step == WizardSteps.INVOICE_DETAILS:
                    self.update_invoice_details_data(data)
                elif self.current_step == WizardSteps.PREVIEW:
                    self.update_preview_settings_data(data)
                elif self.current_step == WizardSteps.SHARING:
                    self.update_sharing_options_data(data)

        # Emit step completed signal
        self.step_completed.emit(self.current_step, self.wizard_data.to_dict())

    def _populate_current_view(self):
        """Populate current view with data from model."""
        if self.current_step in self._step_views:
            view = self._step_views[self.current_step]

            if hasattr(view, 'set_data'):
                if self.current_step == WizardSteps.CUSTOMER:
                    view.set_data({
                        'name': self.wizard_data.customer.name,
                        'national_id': self.wizard_data.customer.national_id,
                        'phone': self.wizard_data.customer.phone,
                        'email': self.wizard_data.customer.email,
                        'address': self.wizard_data.customer.address
                    })
                elif self.current_step == WizardSteps.DOCUMENTS:
                    view.set_data([{
                        'name': doc.name,
                        'doc_type': doc.doc_type,
                        'pages': doc.pages,
                        'source_language': doc.source_language,
                        'target_language': doc.target_language,
                        'cost': doc.cost
                    } for doc in self.wizard_data.documents])
                elif self.current_step == WizardSteps.INVOICE_DETAILS:
                    view.set_data({
                        'receipt_number': self.wizard_data.invoice_details.receipt_number,
                        'receive_date': self.wizard_data.invoice_details.receive_date,
                        'delivery_date': self.wizard_data.invoice_details.delivery_date,
                        'username': self.wizard_data.invoice_details.username,
                        'total_amount': self.wizard_data.invoice_details.total_amount,
                        'discount_amount': self.wizard_data.invoice_details.discount_amount,
                        'advance_payment': self.wizard_data.invoice_details.advance_payment,
                        'remarks': self.wizard_data.invoice_details.remarks
                    })
                elif self.current_step == WizardSteps.PREVIEW:
                    view.set_data({
                        'paper_size': self.wizard_data.preview_settings.paper_size,
                        'show_logo': self.wizard_data.preview_settings.show_logo,
                        'custom_header': self.wizard_data.preview_settings.custom_header,
                        'custom_footer': self.wizard_data.preview_settings.custom_footer,
                        'wizard_data': self.wizard_data
                    })
                elif self.current_step == WizardSteps.SHARING:
                    view.set_data({
                        'email_enabled': self.wizard_data.sharing_options.email_enabled,
                        'additional_emails': self.wizard_data.sharing_options.additional_emails,
                        'email_subject': self.wizard_data.sharing_options.email_subject,
                        'email_message': self.wizard_data.sharing_options.email_message,
                        'whatsapp_enabled': self.wizard_data.sharing_options.whatsapp_enabled,
                        'telegram_enabled': self.wizard_data.sharing_options.telegram_enabled,
                        'sms_enabled': self.wizard_data.sharing_options.sms_enabled,
                        'selected_template': self.wizard_data.sharing_options.selected_template
                    })

    def _populate_all_views(self):
        """Populate all registered views with current data."""
        for step_index in self._step_views.keys():
            current_step = self.current_step
            self.current_step = step_index
            self._populate_current_view()
            self.current_step = current_step

    def _finish_wizard(self) -> bool:
        """Finish the wizard and emit completion signal."""
        if not self._validate_current_step():
            return False

        self._save_current_step_data()
        self.wizard_finished.emit(self.wizard_data.to_dict())
        return True
