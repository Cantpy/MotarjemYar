from typing import Optional, List, Dict, Any
from datetime import date
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from models import (
    Customer, Service, Invoice, InvoiceItem, ValidationError, OperationResult,
    CustomerSearchCriteria, InvoiceSearchCriteria, PaymentStatus, DeliveryStatus
)
from logic import (
    CustomerService, ServiceService, InvoiceService, PricingService,
    ReportService, BusinessRulesService
)


class BaseController(QObject):
    """Base controller with common functionality."""

    # Signals for UI updates
    status_changed = Signal(str)  # Status message
    error_occurred = Signal(str)  # Error message
    success_occurred = Signal(str)  # Success message
    data_updated = Signal()  # General data update signal

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent

    def show_message(self, message: str, message_type: str = "information"):
        """Show message to user."""
        if self.parent_widget:
            msg_box = QMessageBox(self.parent_widget)
            msg_box.setText(message)

            if message_type == "information":
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("اطلاعات")
            elif message_type == "warning":
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("هشدار")
            elif message_type == "error":
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("خطا")

            msg_box.exec()

    def show_validation_errors(self, errors: List[ValidationError]):
        """Show validation errors to user."""
        error_messages = [f"{error.field}: {error.message}" for error in errors]
        full_message = "\n".join(error_messages)
        self.show_message(full_message, "error")

    def handle_operation_result(self, result: OperationResult, success_action=None, error_action=None):
        """Handle operation result and show appropriate message."""
        if result.success:
            self.success_occurred.emit(result.message)
            if success_action:
                success_action(result.data)
        else:
            if result.errors:
                self.show_validation_errors(result.errors)
            else:
                self.error_occurred.emit(result.message)
            if error_action:
                error_action()


class CustomerController(BaseController):
    """Controller for customer operations."""

    # Customer-specific signals
    customer_saved = Signal(Customer)
    customer_deleted = Signal(str)  # national_id
    customer_found = Signal(Customer)
    customers_loaded = Signal(list)

    def __init__(self, customer_service: CustomerService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.customer_service = customer_service

    def load_all_customers(self):
        """Load all customers."""
        result = self.customer_service.get_all_customers()

        def on_success(customers):
            self.customers_loaded.emit(customers)

        self.handle_operation_result(result, on_success)

    def save_customer(self, national_id: str, name: str, phone: str, address: str,
                      telegram_id: str = "", email: str = "", passport_image: str = ""):
        """Save a new customer."""
        # Convert empty strings to None
        telegram_id = telegram_id if telegram_id.strip() else None
        email = email if email.strip() else None
        passport_image = passport_image if passport_image.strip() else None

        result = self.customer_service.save_customer(
            national_id, name, phone, address, telegram_id, email, passport_image
        )

        def on_success(customer):
            self.customer_saved.emit(customer)
            self.data_updated.emit()

        self.handle_operation_result(result, on_success)

    def delete_customer(self, national_id: str):
        """Delete a customer."""
        result = self.customer_service.delete_customer(national_id)

        def on_success(data):
            self.customer_deleted.emit(national_id)
            self.data_updated.emit()

        self.handle_operation_result(result, on_success)

    def find_customer_by_national_id(self, national_id: str):
        """Find customer by national ID."""
        result = self.customer_service.get_customer_by_national_id(national_id)

        def on_success(customer):
            self.customer_found.emit(customer)

        self.handle_operation_result(result, on_success)

    def find_customer_by_phone(self, phone: str):
        """Find customer by phone."""
        result = self.customer_service.get_customer_by_phone(phone)

        def on_success(customer):
            self.customer_found.emit(customer)

        self.handle_operation_result(result, on_success)

    def find_customer_by_name(self, name: str):
        """Find customer by name."""
        result = self.customer_service.get_customer_by_name(name)

        def on_success(customer):
            self.customer_found.emit(customer)

        self.handle_operation_result(result, on_success)

    def get_customer_suggestions(self, field: str) -> List[str]:
        """Get autocomplete suggestions."""
        return self.customer_service.get_customer_suggestions(field)

    def search_customers(self, name: str = "", phone: str = "", national_id: str = ""):
        """Search customers with criteria."""
        criteria = CustomerSearchCriteria(
            name=name if name.strip() else None,
            phone=phone if phone.strip() else None,
            national_id=national_id if national_id.strip() else None
        )

        result = self.customer_service.search_customers(criteria)

        def on_success(customers):
            self.customers_loaded.emit(customers)

        self.handle_operation_result(result, on_success)


class ServiceController(BaseController):
    """Controller for service operations."""

    # Service-specific signals
    services_loaded = Signal(list)
    service_found = Signal(Service)
    service_names_loaded = Signal(list)

    def __init__(self, service_service: ServiceService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.service_service = service_service

    def load_all_services(self):
        """Load all services."""
        result = self.service_service.get_all_services()

        def on_success(services):
            self.services_loaded.emit(services)

        self.handle_operation_result(result, on_success)

    def find_service_by_name(self, name: str):
        """Find service by name."""
        result = self.service_service.get_service_by_name(name)

        def on_success(service):
            self.service_found.emit(service)

        self.handle_operation_result(result, on_success)

    def load_service_names(self):
        """Load service names for autocomplete."""
        names = self.service_service.get_service_names()
        self.service_names_loaded.emit(names)


class InvoiceController(BaseController):
    """Controller for invoice operations."""

    # Invoice-specific signals
    invoice_created = Signal(Invoice)
    invoice_updated = Signal(Invoice)
    invoice_found = Signal(Invoice)
    invoices_loaded = Signal(list)
    invoice_number_generated = Signal(int)
    item_added = Signal(Invoice)
    item_deleted = Signal(Invoice)

    def __init__(self, invoice_service: InvoiceService, pricing_service: PricingService,
                 business_rules_service: BusinessRulesService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.invoice_service = invoice_service
        self.pricing_service = pricing_service
        self.business_rules_service = business_rules_service

    def generate_invoice_number(self):
        """Generate next invoice number."""
        invoice_number = self.invoice_service.get_current_invoice_number()
        self.invoice_number_generated.emit(invoice_number)

    def create_invoice(self, invoice_data: Dict[str, Any]):
        """Create a new invoice."""
        result = self.invoice_service.create_invoice(
            invoice_number=invoice_data['invoice_number'],
            name=invoice_data['name'],
            national_id=invoice_data['national_id'],
            phone=invoice_data['phone'],
            issue_date=invoice_data['issue_date'],
            delivery_date=invoice_data['delivery_date'],
            translator=invoice_data['translator'],
            total_amount=invoice_data.get('total_amount', 0),
            total_translation_price=invoice_data.get('total_translation_price', 0),
            advance_payment=invoice_data.get('advance_payment', 0),
            discount_amount=invoice_data.get('discount_amount', 0),
            force_majeure=invoice_data.get('force_majeure', 0),
            source_language=invoice_data.get('source_language'),
            target_language=invoice_data.get('target_language'),
            remarks=invoice_data.get('remarks'),
            username=invoice_data.get('username')
        )

        def on_success(invoice):
            self.invoice_created.emit(invoice)
            self.data_updated.emit()

        self.handle_operation_result(result, on_success)

    def add_invoice_item(self, invoice_number: int, item_data: Dict[str, Any]):
        """Add item to invoice."""
        result = self.invoice_service.add_invoice_item(
            invoice_number=invoice_number,
            item_name=item_data['item_name'],
            item_qty=item_data['item_qty'],
            item_price=item_data['item_price'],
            officiality=item_data.get('officiality', 0),
            judiciary_seal=item_data.get('judiciary_seal', 0),
            foreign_affairs_seal=item_data.get('foreign_affairs_seal', 0),
            remarks=item_data.get('remarks')
        )

        def on_success(invoice):
            self.item_added.emit(invoice)

        self.handle_operation_result(result, on_success)

    def delete_invoice_item(self, invoice_number: int, item_id: int):
        """Delete item from invoice."""
        result = self.invoice_service.delete_invoice_item(invoice_number, item_id)

        def on_success(invoice):
            self.item_deleted.emit(invoice)

        self.handle_operation_result(result, on_success)

    def find_invoice_by_number(self, invoice_number: int):
        """Find invoice by number."""
        result = self.invoice_service.get_invoice_by_number(invoice_number)

        def on_success(invoice):
            self.invoice_found.emit(invoice)

        self.handle_operation_result(result, on_success)

    def update_payment_status(self, invoice_number: int, is_paid: bool):
        """Update invoice payment status."""
        status = PaymentStatus.PAID if is_paid else PaymentStatus.UNPAID
        result = self.invoice_service.update_invoice_payment_status(invoice_number, status)

        def on_success(invoice):
            self.invoice_updated.emit(invoice)

        self.handle_operation_result(result, on_success)

    def update_delivery_status(self, invoice_number: int, delivery_status: DeliveryStatus):
        """Update invoice delivery status."""
        result = self.invoice_service.update_invoice_delivery_status(invoice_number, delivery_status)

        def on_success(invoice):
            self.invoice_updated.emit(invoice)

        self.handle_operation_result(result, on_success)

    def load_unpaid_invoices(self):
        """Load unpaid invoices."""
        result = self.invoice_service.get_unpaid_invoices()

        def on_success(invoices):
            self.invoices_loaded.emit(invoices)

        self.handle_operation_result(result, on_success)

    def load_pending_delivery_invoices(self):
        """Load invoices with pending delivery."""
        result = self.invoice_service.get_pending_delivery_invoices()

        def on_success(invoices):
            self.invoices_loaded.emit(invoices)

        self.handle_operation_result(result, on_success)

    def search_invoices(self, search_criteria: Dict[str, Any]):
        """Search invoices."""
        criteria = InvoiceSearchCriteria(
            invoice_number=search_criteria.get('invoice_number'),
            customer_name=search_criteria.get('customer_name'),
            national_id=search_criteria.get('national_id'),
            payment_status=search_criteria.get('payment_status'),
            delivery_status=search_criteria.get('delivery_status'),
            date_from=search_criteria.get('date_from'),
            date_to=search_criteria.get('date_to')
        )

        result = self.invoice_service.search_invoices(criteria)

        def on_success(invoices):
            self.invoices_loaded.emit(invoices)

        self.handle_operation_result(result, on_success)

    def update_invoice_totals(self, invoice_number: int):
        """Update invoice totals from items."""
        result = self.invoice_service.update_invoice_totals_from_items(invoice_number)

        def on_success(invoice):
            self.invoice_updated.emit(invoice)

        self.handle_operation_result(result, on_success)

    def can_modify_invoice(self, invoice: Invoice) -> bool:
        """Check if invoice can be modified."""
        result = self.business_rules_service.can_modify_invoice(invoice)
        if not result.success:
            self.show_message(result.message, "warning")
            return False
        return True


class PricingController(BaseController):
    """Controller for pricing operations."""

    # Pricing-specific signals
    price_calculated = Signal(dict)
    discount_applied = Signal(dict)

    def __init__(self, pricing_service: PricingService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pricing_service = pricing_service

    def calculate_service_price(self, service_name: str, quantity: int,
                                use_dynamic_price_1: bool = False,
                                use_dynamic_price_2: bool = False):
        """Calculate price for a service."""
        result = self.pricing_service.calculate_service_price(
            service_name, quantity, use_dynamic_price_1, use_dynamic_price_2
        )

        def on_success(price_info):
            self.price_calculated.emit(price_info)

        self.handle_operation_result(result, on_success)

    def apply_discount(self, total_amount: int, discount_percentage: float = 0,
                       discount_amount: int = 0):
        """Apply discount to amount."""
        result = self.pricing_service.apply_discount(
            total_amount, discount_percentage, discount_amount
        )

        def on_success(discount_info):
            self.discount_applied.emit(discount_info)

        self.handle_operation_result(result, on_success)


class ReportController(BaseController):
    """Controller for report operations."""

    # Report-specific signals
    customer_report_generated = Signal(dict)
    financial_summary_generated = Signal(dict)

    def __init__(self, report_service: ReportService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.report_service = report_service

    def generate_customer_report(self, customer_national_id: str):
        """Generate customer report."""
        result = self.report_service.generate_customer_report(customer_national_id)

        def on_success(report):
            self.customer_report_generated.emit(report)

        self.handle_operation_result(result, on_success)

    def generate_financial_summary(self, date_from: Optional[date] = None,
                                   date_to: Optional[date] = None):
        """Generate financial summary report."""
        result = self.report_service.generate_financial_summary(date_from, date_to)

        def on_success(summary):
            self.financial_summary_generated.emit(summary)

        self.handle_operation_result(result, on_success)


class MainInvoiceController(BaseController):
    """Main controller that coordinates all invoice-related operations."""

    # Main controller signals
    form_cleared = Signal()
    totals_updated = Signal(dict)

    def __init__(self, customer_controller: CustomerController,
                 service_controller: ServiceController,
                 invoice_controller: InvoiceController,
                 pricing_controller: PricingController,
                 report_controller: ReportController,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Sub-controllers
        self.customer_controller = customer_controller
        self.service_controller = service_controller
        self.invoice_controller = invoice_controller
        self.pricing_controller = pricing_controller
        self.report_controller = report_controller

        # Current state
        self.current_invoice: Optional[Invoice] = None
        self.current_customer: Optional[Customer] = None
        self.invoice_items: List[Dict[str, Any]] = []
        self.current_invoice_number: Optional[int] = None

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals between controllers."""
        # Customer signals
        self.customer_controller.customer_found.connect(self._on_customer_found)

        # Invoice signals
        self.invoice_controller.invoice_created.connect(self._on_invoice_created)
        self.invoice_controller.invoice_number_generated.connect(self._on_invoice_number_generated)
        self.invoice_controller.item_added.connect(self._on_item_added)
        self.invoice_controller.item_deleted.connect(self._on_item_deleted)

        # Pricing signals
        self.pricing_controller.price_calculated.connect(self._on_price_calculated)

    def _on_customer_found(self, customer: Customer):
        """Handle customer found event."""
        self.current_customer = customer

    def _on_invoice_created(self, invoice: Invoice):
        """Handle invoice created event."""
        self.current_invoice = invoice

    def _on_invoice_number_generated(self, invoice_number: int):
        """Handle invoice number generated event."""
        self.current_invoice_number = invoice_number

    def _on_item_added(self, invoice: Invoice):
        """Handle item added event."""
        self.current_invoice = invoice
        self._update_totals()

    def _on_item_deleted(self, invoice: Invoice):
        """Handle item deleted event."""
        self.current_invoice = invoice
        self._update_totals()

    def _on_price_calculated(self, price_info: Dict[str, Any]):
        """Handle price calculated event."""
        # This can be used to auto-fill price fields in UI
        pass

    def _update_totals(self):
        """Update invoice totals."""
        if self.current_invoice:
            totals = {
                'total_amount': self.current_invoice.total_amount,
                'final_amount': self.current_invoice.final_amount,
                'advance_payment': self.current_invoice.advance_payment,
                'discount_amount': self.current_invoice.discount_amount,
                'items_count': len(self.current_invoice.items)
            }
            self.totals_updated.emit(totals)

    def initialize_new_invoice(self):
        """Initialize a new invoice."""
        self.invoice_controller.generate_invoice_number()
        self.current_invoice = None
        self.current_customer = None
        self.invoice_items = []
        self.form_cleared.emit()

    def autofill_customer_data(self, field_type: str, value: str):
        """Auto-fill customer data based on field type."""
        if field_type == "national_id":
            self.customer_controller.find_customer_by_national_id(value)
        elif field_type == "phone":
            self.customer_controller.find_customer_by_phone(value)
        elif field_type == "name":
            self.customer_controller.find_customer_by_name(value)

    def add_service_to_invoice(self, service_name: str, quantity: int,
                               custom_price: Optional[int] = None,
                               use_dynamic_price_1: bool = False,
                               use_dynamic_price_2: bool = False):
        """Add a service to the current invoice."""
        if not self.current_invoice_number:
            self.show_message("لطفاً ابتدا فاکتور را ایجاد کنید.", "warning")
            return

        # Calculate price if not provided
        if custom_price is None:
            self.pricing_controller.calculate_service_price(
                service_name, quantity, use_dynamic_price_1, use_dynamic_price_2
            )
        else:
            # Use custom price directly
            item_data = {
                'item_name': service_name,
                'item_qty': quantity,
                'item_price': custom_price
            }
            self.invoice_controller.add_invoice_item(self.current_invoice_number, item_data)

    def create_invoice_with_customer(self, customer_data: Dict[str, Any],
                                     invoice_data: Dict[str, Any]):
        """Create invoice with customer data."""
        # Merge customer and invoice data
        full_invoice_data = {
            'invoice_number': self.current_invoice_number or self.invoice_controller.invoice_service.get_current_invoice_number(),
            'name': customer_data['name'],
            'national_id': customer_data['national_id'],
            'phone': customer_data['phone'],
            'issue_date': invoice_data.get('issue_date', date.today()),
            'delivery_date': invoice_data.get('delivery_date', date.today()),
            'translator': invoice_data.get('translator', ''),
            **invoice_data
        }

        self.invoice_controller.create_invoice(full_invoice_data)

    def save_new_customer_and_create_invoice(self, customer_data: Dict[str, Any],
                                             invoice_data: Dict[str, Any]):
        """Save new customer and create invoice."""
        # First save the customer
        self.customer_controller.save_customer(
            customer_data['national_id'],
            customer_data['name'],
            customer_data['phone'],
            customer_data['address'],
            customer_data.get('telegram_id', ''),
            customer_data.get('email', ''),
            customer_data.get('passport_image', '')
        )

        # Then create the invoice (will be handled by signal connection)
        self.create_invoice_with_customer(customer_data, invoice_data)

    def validate_invoice_form(self, form_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate complete invoice form."""
        errors = []

        # Validate customer data
        customer_errors = ValidationService.validate_customer_data(
            form_data.get('name', ''),
            form_data.get('phone', ''),
            form_data.get('national_id', ''),
            form_data.get('address', '')
        )
        errors.extend(customer_errors)

        # Validate invoice data
        invoice_errors = ValidationService.validate_invoice_data(
            form_data.get('name', ''),
            form_data.get('national_id', ''),
            form_data.get('phone', ''),
            form_data.get('translator', '')
        )
        errors.extend(invoice_errors)

        # Check if items exist
        if not self.current_invoice or not self.current_invoice.items:
            errors.append(ValidationError("items", "لطفاً حداقل یک آیتم به فاکتور اضافه کنید."))

        return errors

    def finalize_invoice(self, form_data: Dict[str, Any]) -> bool:
        """Finalize and save the complete invoice."""
        # Validate form
        errors = self.validate_invoice_form(form_data)
        if errors:
            self.show_validation_errors(errors)
            return False

        # Check if customer exists or needs to be created
        existing_customer_result = self.customer_controller.customer_service.get_customer_by_national_id(
            form_data['national_id']
        )

        if existing_customer_result.success:
            # Customer exists, create invoice
            self.create_invoice_with_customer(form_data, form_data)
        else:
            # Customer doesn't exist, create both
            self.save_new_customer_and_create_invoice(form_data, form_data)

        return True

    def clear_current_form(self):
        """Clear current form and reset state."""
        self.current_invoice = None
        self.current_customer = None
        self.invoice_items = []
        self.current_invoice_number = None
        self.form_cleared.emit()

    def get_current_state(self) -> Dict[str, Any]:
        """Get current controller state."""
        return {
            'current_invoice': self.current_invoice,
            'current_customer': self.current_customer,
            'invoice_items': self.invoice_items,
            'current_invoice_number': self.current_invoice_number
        }


class ControllerFactory:
    """Factory for creating controllers with proper dependencies."""

    def __init__(self, customer_service: CustomerService,
                 service_service: ServiceService,
                 invoice_service: InvoiceService,
                 pricing_service: PricingService,
                 report_service: ReportService,
                 business_rules_service: BusinessRulesService):
        self.customer_service = customer_service
        self.service_service = service_service
        self.invoice_service = invoice_service
        self.pricing_service = pricing_service
        self.report_service = report_service
        self.business_rules_service = business_rules_service

    def create_customer_controller(self, parent: Optional[QWidget] = None) -> CustomerController:
        """Create customer controller."""
        return CustomerController(self.customer_service, parent)

    def create_service_controller(self, parent: Optional[QWidget] = None) -> ServiceController:
        """Create service controller."""
        return ServiceController(self.service_service, parent)

    def create_invoice_controller(self, parent: Optional[QWidget] = None) -> InvoiceController:
        """Create invoice controller."""
        return InvoiceController(
            self.invoice_service,
            self.pricing_service,
            self.business_rules_service,
            parent
        )

    def create_pricing_controller(self, parent: Optional[QWidget] = None) -> PricingController:
        """Create pricing controller."""
        return PricingController(self.pricing_service, parent)

    def create_report_controller(self, parent: Optional[QWidget] = None) -> ReportController:
        """Create report controller."""
        return ReportController(self.report_service, parent)

    def create_main_controller(self, parent: Optional[QWidget] = None) -> MainInvoiceController:
        """Create main invoice controller with all dependencies."""
        customer_controller = self.create_customer_controller(parent)
        service_controller = self.create_service_controller(parent)
        invoice_controller = self.create_invoice_controller(parent)
        pricing_controller = self.create_pricing_controller(parent)
        report_controller = self.create_report_controller(parent)

        return MainInvoiceController(
            customer_controller,
            service_controller,
            invoice_controller,
            pricing_controller,
            report_controller,
            parent
        )
