from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import (
    Customer, Service, Invoice, InvoiceItem, ValidationError, OperationResult,
    CustomerSearchCriteria, InvoiceSearchCriteria, PaymentStatus, DeliveryStatus,
    InvoiceTotals
)
from repository import (
    InvoiceRepository, IServiceRepository, IInvoiceRepository,
    translate_sqlite_error
)


class ValidationService:
    """Service for validating business rules and data integrity."""

    @staticmethod
    def validate_customer_data(name: str, phone: str, national_id: str, address: str) -> List[ValidationError]:
        """Validate customer input data."""
        errors = []

        if not name or len(name.strip()) < 2:
            errors.append(ValidationError("name", "نام باید حداقل 2 کاراکتر باشد."))

        if not phone or len(phone.strip()) < 10:
            errors.append(ValidationError("phone", "شماره تلفن باید حداقل 10 رقم باشد."))

        if not national_id or len(national_id.strip()) != 10:
            errors.append(ValidationError("national_id", "کد ملی باید دقیقاً 10 رقم باشد."))

        if not address or len(address.strip()) < 5:
            errors.append(ValidationError("address", "آدرس باید حداقل 5 کاراکتر باشد."))

        # Additional business rules
        if national_id and not national_id.isdigit():
            errors.append(ValidationError("national_id", "کد ملی باید فقط شامل اعداد باشد."))

        if phone and not phone.isdigit():
            errors.append(ValidationError("phone", "شماره تلفن باید فقط شامل اعداد باشد."))

        return errors

    @staticmethod
    def validate_invoice_data(name: str, national_id: str, phone: str, translator: str) -> List[ValidationError]:
        """Validate invoice input data."""
        errors = []

        if not name or not name.strip():
            errors.append(ValidationError("name", "نام نباید خالی باشد."))

        if not national_id or len(national_id.strip()) != 10:
            errors.append(ValidationError("national_id", "کد ملی باید 10 رقم باشد."))

        if not phone or len(phone.strip()) < 10:
            errors.append(ValidationError("phone", "شماره تلفن باید حداقل 10 رقم باشد."))

        if not translator or not translator.strip():
            errors.append(ValidationError("translator", "نام مترجم نباید خالی باشد."))

        return errors

    @staticmethod
    def validate_invoice_item_data(item_name: str, item_qty: int, item_price: int) -> List[ValidationError]:
        """Validate invoice item input data."""
        errors = []

        if not item_name or not item_name.strip():
            errors.append(ValidationError("item_name", "نام آیتم نباید خالی باشد."))

        if item_qty <= 0:
            errors.append(ValidationError("item_qty", "تعداد باید بزرگتر از صفر باشد."))

        if item_price < 0:
            errors.append(ValidationError("item_price", "قیمت نمی‌تواند منفی باشد."))

        return errors

    @staticmethod
    def validate_numeric_input(value: str, field_name: str) -> Tuple[bool, str, int]:
        """Validate numeric input for integer fields."""
        try:
            parsed_value = int(value)
            if parsed_value < 0:
                return False, f"{field_name} نمی‌تواند منفی باشد.", 0
            return True, "", parsed_value
        except (ValueError, TypeError):
            return False, f"{field_name} باید یک عدد معتبر باشد.", 0

    @staticmethod
    def validate_payment_status(status: int) -> bool:
        """Validate payment status."""
        return status in [PaymentStatus.UNPAID.value, PaymentStatus.PAID.value]

    @staticmethod
    def validate_delivery_status(status: int) -> bool:
        """Validate delivery status."""
        return status in [s.value for s in DeliveryStatus]

    @staticmethod
    def validate_boolean_field(value: int) -> bool:
        """Validate boolean fields (0 or 1)."""
        return value in [0, 1]


class CustomerService:
    """Business logic service for customer operations."""

    def __init__(self, customer_repository: InvoiceRepository):
        self.customer_repository = customer_repository
        self.validator = ValidationService()

    def get_all_customers(self) -> OperationResult:
        """Retrieve all customers."""
        try:
            customers = self.customer_repository.get_all()
            return OperationResult.success_result("مشتریان با موفقیت بازیابی شدند.", customers)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_customer_by_national_id(self, national_id: str) -> OperationResult:
        """Find a customer by national ID."""
        try:
            customer = self.customer_repository.get_by_national_id(national_id)
            if customer:
                return OperationResult.success_result("مشتری یافت شد.", customer)
            else:
                return OperationResult.error_result("مشتری با این کد ملی یافت نشد.")
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_customer_by_phone(self, phone: str) -> OperationResult:
        """Find a customer by phone number."""
        try:
            customer = self.customer_repository.get_by_phone(phone)
            if customer:
                return OperationResult.success_result("مشتری یافت شد.", customer)
            else:
                return OperationResult.error_result("مشتری با این شماره تلفن یافت نشد.")
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_customer_by_name(self, name: str) -> OperationResult:
        """Find a customer by name."""
        try:
            customer = self.customer_repository.get_by_name(name)
            if customer:
                return OperationResult.success_result("مشتری یافت شد.", customer)
            else:
                return OperationResult.error_result("مشتری با این نام یافت نشد.")
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def save_customer(self, national_id: str, name: str, phone: str, address: str,
                      telegram_id: str = None, email: str = None, passport_image: str = None) -> OperationResult:
        """Save a new customer."""
        # Validate input
        validation_errors = self.validator.validate_customer_data(name, phone, national_id, address)
        if validation_errors:
            return OperationResult.validation_error_result(validation_errors)

        try:
            # Check for duplicates
            existing_customer = self.customer_repository.get_by_national_id(national_id)
            if existing_customer:
                return OperationResult.error_result("مشتری با این کد ملی قبلاً ثبت شده است.")

            existing_phone = self.customer_repository.get_by_phone(phone)
            if existing_phone:
                return OperationResult.error_result("مشتری با این شماره تلفن قبلاً ثبت شده است.")

            # Create customer
            customer = Customer(
                national_id=national_id,
                name=name,
                phone=phone,
                address=address,
                telegram_id=telegram_id,
                email=email,
                passport_image=passport_image
            )

            saved_customer = self.customer_repository.save(customer)
            return OperationResult.success_result("مشتری با موفقیت ذخیره شد!", saved_customer)

        except IntegrityError:
            return OperationResult.error_result("کد ملی یا شماره تلفن تکراری است.")
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def delete_customer(self, national_id: str) -> OperationResult:
        """Delete a customer by national ID."""
        try:
            customer = self.customer_repository.get_by_national_id(national_id)
            if not customer:
                return OperationResult.error_result("مشتری با این کد ملی پیدا نشد.")

            success = self.customer_repository.delete(customer.id)
            if success:
                return OperationResult.success_result(f"مشتری {customer.name} با موفقیت حذف شد!")
            else:
                return OperationResult.error_result("خطا در حذف مشتری.")

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_customer_suggestions(self, field: str) -> List[str]:
        """Get autocomplete suggestions for customer fields."""
        try:
            return self.customer_repository.get_suggestions(field)
        except SQLAlchemyError:
            return []

    def search_customers(self, criteria: CustomerSearchCriteria) -> OperationResult:
        """Search customers based on criteria."""
        try:
            customers = self.customer_repository.search(criteria)
            return OperationResult.success_result("جستجو با موفقیت انجام شد.", customers)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)


class ServiceService:
    """Business logic service for service operations."""

    def __init__(self, service_repository: IServiceRepository):
        self.service_repository = service_repository

    def get_all_services(self) -> OperationResult:
        """Retrieve all services."""
        try:
            services = self.service_repository.get_all()
            return OperationResult.success_result("سرویس‌ها با موفقیت بازیابی شدند.", services)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_service_by_name(self, name: str) -> OperationResult:
        """Find a service by name."""
        try:
            service = self.service_repository.get_by_name(name)
            if service:
                return OperationResult.success_result("سرویس یافت شد.", service)
            else:
                return OperationResult.error_result("سرویس با این نام یافت نشد.")
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_service_names(self) -> List[str]:
        """Get all service names for autocomplete."""
        try:
            return self.service_repository.get_names()
        except SQLAlchemyError:
            return []


class InvoiceService:
    """Business logic service for invoice operations."""

    def __init__(self, invoice_repository: IInvoiceRepository, customer_service: CustomerService):
        self.invoice_repository = invoice_repository
        self.customer_service = customer_service
        self.validator = ValidationService()

    def get_current_invoice_number(self) -> int:
        """Get the next available invoice number."""
        try:
            return self.invoice_repository.get_next_invoice_number()
        except SQLAlchemyError:
            return 1000

    def create_invoice(self, invoice_number: int, name: str, national_id: str, phone: str,
                       issue_date: date, delivery_date: date, translator: str,
                       total_amount: int = 0, total_translation_price: int = 0,
                       advance_payment: int = 0, discount_amount: int = 0,
                       force_majeure: int = 0, final_amount: int = 0,
                       source_language: str = None, target_language: str = None,
                       remarks: str = None, username: str = None) -> OperationResult:
        """Create a new invoice."""
        # Validate input
        validation_errors = self.validator.validate_invoice_data(name, national_id, phone, translator)
        if validation_errors:
            return OperationResult.validation_error_result(validation_errors)

        try:
            invoice = Invoice(
                invoice_number=invoice_number,
                name=name,
                national_id=national_id,
                phone=phone,
                issue_date=issue_date,
                delivery_date=delivery_date,
                translator=translator,
                total_amount=total_amount,
                total_translation_price=total_translation_price,
                advance_payment=advance_payment,
                discount_amount=discount_amount,
                force_majeure=force_majeure,
                final_amount=final_amount,
                source_language=source_language,
                target_language=target_language,
                remarks=remarks,
                username=username
            )

            saved_invoice = self.invoice_repository.save(invoice)
            return OperationResult.success_result("فاکتور با موفقیت ایجاد شد!", saved_invoice)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def add_invoice_item(self, invoice_number: int, item_name: str, item_qty: int,
                         item_price: int, officiality: int = 0,
                         judiciary_seal: int = 0, foreign_affairs_seal: int = 0,
                         remarks: str = None) -> OperationResult:
        """Add an item to an invoice."""
        # Validate input
        validation_errors = self.validator.validate_invoice_item_data(item_name, item_qty, item_price)
        if validation_errors:
            return OperationResult.validation_error_result(validation_errors)

        try:
            # Get invoice
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if not invoice:
                return OperationResult.error_result("فاکتور یافت نشد.")

            # Create item
            item = InvoiceItem(
                invoice_number=invoice_number,
                item_name=item_name,
                item_qty=item_qty,
                item_price=item_price,
                officiality=officiality,
                judiciary_seal=judiciary_seal,
                foreign_affairs_seal=foreign_affairs_seal,
                remarks=remarks
            )

            # Add item to invoice
            invoice.add_item(item)

            # Save updated invoice
            saved_invoice = self.invoice_repository.save(invoice)
            return OperationResult.success_result("آیتم با موفقیت به فاکتور اضافه شد!", saved_invoice)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_invoice_by_number(self, invoice_number: int) -> OperationResult:
        """Get an invoice by number."""
        try:
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if invoice:
                return OperationResult.success_result("فاکتور یافت شد.", invoice)
            else:
                return OperationResult.error_result("فاکتور یافت نشد.")
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def update_invoice_payment_status(self, invoice_number: int, payment_status: PaymentStatus) -> OperationResult:
        """Update the payment status of an invoice."""
        try:
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if not invoice:
                return OperationResult.error_result("فاکتور پیدا نشد.")

            invoice.payment_status = payment_status
            updated_invoice = self.invoice_repository.save(invoice)
            return OperationResult.success_result("وضعیت پرداخت به‌روزرسانی شد!", updated_invoice)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def update_invoice_delivery_status(self, invoice_number: int, delivery_status: DeliveryStatus) -> OperationResult:
        """Update the delivery status of an invoice."""
        try:
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if not invoice:
                return OperationResult.error_result("فاکتور پیدا نشد.")

            invoice.delivery_status = delivery_status
            updated_invoice = self.invoice_repository.save(invoice)
            return OperationResult.success_result("وضعیت تحویل به‌روزرسانی شد!", updated_invoice)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_unpaid_invoices(self) -> OperationResult:
        """Get all unpaid invoices."""
        try:
            invoices = self.invoice_repository.get_unpaid_invoices()
            return OperationResult.success_result("فاکتورهای پرداخت نشده بازیابی شدند.", invoices)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_pending_delivery_invoices(self) -> OperationResult:
        """Get all invoices with pending delivery status."""
        try:
            invoices = self.invoice_repository.get_pending_delivery_invoices()
            return OperationResult.success_result("فاکتورهای در انتظار تحویل بازیابی شدند.", invoices)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def calculate_invoice_totals(self, invoice_number: int) -> OperationResult:
        """Calculate various totals for an invoice based on its items."""
        try:
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if not invoice:
                return OperationResult.error_result("فاکتور یافت نشد.")

            total_items_price = sum(item.total_price for item in invoice.items)
            total_items = len(invoice.items)
            total_official_docs = sum(item.officiality for item in invoice.items)
            total_judiciary_docs = sum(item.judiciary_seal for item in invoice.items)
            total_foreign_docs = sum(item.foreign_affairs_seal for item in invoice.items)
            total_pages = sum(item.item_qty for item in invoice.items)

            totals = InvoiceTotals(
                total_items_price=total_items_price,
                total_items=total_items,
                total_official_docs=total_official_docs,
                total_judiciary_docs=total_judiciary_docs,
                total_foreign_docs=total_foreign_docs,
                total_pages=total_pages
            )

            return OperationResult.success_result("محاسبات با موفقیت انجام شد.", totals)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def update_invoice_totals_from_items(self, invoice_number: int) -> OperationResult:
        """Update invoice totals based on its items."""
        try:
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if not invoice:
                return OperationResult.error_result("فاکتور پیدا نشد.")

            # Recalculate totals
            invoice.recalculate_totals()

            # Save updated invoice
            updated_invoice = self.invoice_repository.save(invoice)
            return OperationResult.success_result("مجموع فاکتور به‌روزرسانی شد!", updated_invoice)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def delete_invoice_item(self, invoice_number: int, item_id: int) -> OperationResult:
        """Delete an invoice item."""
        try:
            invoice = self.invoice_repository.get_by_number(invoice_number)
            if not invoice:
                return OperationResult.error_result("فاکتور یافت نشد.")

            success = invoice.remove_item(item_id)
            if not success:
                return OperationResult.error_result("آیتم یافت نشد.")

            # Save updated invoice
            updated_invoice = self.invoice_repository.save(invoice)
            return OperationResult.success_result("آیتم با موفقیت حذف شد!", updated_invoice)

        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def search_invoices(self, criteria: InvoiceSearchCriteria) -> OperationResult:
        """Search invoices based on criteria."""
        try:
            invoices = self.invoice_repository.search(criteria)
            return OperationResult.success_result("جستجو با موفقیت انجام شد.", invoices)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)

    def get_all_invoices(self) -> OperationResult:
        """Get all invoices."""
        try:
            invoices = self.invoice_repository.get_all()
            return OperationResult.success_result("فاکتورها با موفقیت بازیابی شدند.", invoices)
        except SQLAlchemyError as e:
            error_message = translate_sqlite_error(e)
            return OperationResult.error_result(error_message)


class PricingService:
    """Business logic service for pricing calculations."""

    def __init__(self, service_service: ServiceService):
        self.service_service = service_service

    def calculate_service_price(self, service_name: str, quantity: int,
                                use_dynamic_price_1: bool = False,
                                use_dynamic_price_2: bool = False) -> OperationResult:
        """Calculate price for a service based on quantity and pricing rules."""
        service_result = self.service_service.get_service_by_name(service_name)
        if not service_result.success:
            return service_result

        service = service_result.data
        base_price = service.base_price

        # Apply dynamic pricing if requested
        if use_dynamic_price_1 and service.dynamic_price_1:
            base_price = service.dynamic_price_1
        elif use_dynamic_price_2 and service.dynamic_price_2:
            base_price = service.dynamic_price_2

        total_price = base_price * quantity

        price_info = {
            'base_price': base_price,
            'quantity': quantity,
            'total_price': total_price,
            'service_name': service_name,
            'dynamic_price_used': use_dynamic_price_1 or use_dynamic_price_2
        }

        return OperationResult.success_result("قیمت محاسبه شد.", price_info)

    def apply_discount(self, total_amount: int, discount_percentage: float = 0,
                       discount_amount: int = 0) -> OperationResult:
        """Apply discount to total amount."""
        try:
            if discount_percentage < 0 or discount_percentage > 100:
                return OperationResult.error_result("درصد تخفیف باید بین 0 تا 100 باشد.")

            if discount_amount < 0:
                return OperationResult.error_result("مبلغ تخفیف نمی‌تواند منفی باشد.")

            final_discount = discount_amount
            if discount_percentage > 0:
                final_discount += int(total_amount * discount_percentage / 100)

            if final_discount > total_amount:
                return OperationResult.error_result("تخفیف نمی‌تواند بیشتر از مبلغ کل باشد.")

            discounted_amount = total_amount - final_discount

            discount_info = {
                'original_amount': total_amount,
                'discount_percentage': discount_percentage,
                'discount_amount': discount_amount,
                'total_discount': final_discount,
                'final_amount': discounted_amount
            }

            return OperationResult.success_result("تخفیف اعمال شد.", discount_info)

        except Exception as e:
            return OperationResult.error_result(f"خطا در محاسبه تخفیف: {str(e)}")


class ReportService:
    """Business logic service for generating reports."""

    def __init__(self, invoice_service: InvoiceService, customer_service: CustomerService):
        self.invoice_service = invoice_service
        self.customer_service = customer_service

    def generate_customer_report(self, customer_national_id: str) -> OperationResult:
        """Generate a report for a specific customer."""
        try:
            # Get customer info
            customer_result = self.customer_service.get_customer_by_national_id(customer_national_id)
            if not customer_result.success:
                return customer_result

            customer = customer_result.data

            # Get customer's invoices
            criteria = InvoiceSearchCriteria(national_id=customer_national_id)
            invoices_result = self.invoice_service.search_invoices(criteria)
            if not invoices_result.success:
                return invoices_result

            invoices = invoices_result.data

            # Calculate statistics
            total_invoices = len(invoices)
            total_amount = sum(invoice.final_amount for invoice in invoices)
            paid_invoices = [inv for inv in invoices if inv.is_paid()]
            unpaid_invoices = [inv for inv in invoices if not inv.is_paid()]
            delivered_invoices = [inv for inv in invoices if inv.is_delivered()]

            report = {
                'customer': customer,
                'total_invoices': total_invoices,
                'total_amount': total_amount,
                'paid_invoices_count': len(paid_invoices),
                'unpaid_invoices_count': len(unpaid_invoices),
                'delivered_invoices_count': len(delivered_invoices),
                'pending_amount': sum(inv.get_pending_amount() for inv in unpaid_invoices),
                'latest_invoices': sorted(invoices, key=lambda x: x.issue_date, reverse=True)[:5]
            }

            return OperationResult.success_result("گزارش مشتری تولید شد.", report)

        except Exception as e:
            return OperationResult.error_result(f"خطا در تولید گزارش: {str(e)}")

    def generate_financial_summary(self, date_from: date = None, date_to: date = None) -> OperationResult:
        """Generate financial summary report."""
        try:
            criteria = InvoiceSearchCriteria(date_from=date_from, date_to=date_to)
            invoices_result = self.invoice_service.search_invoices(criteria)
            if not invoices_result.success:
                return invoices_result

            invoices = invoices_result.data

            total_revenue = sum(inv.final_amount for inv in invoices if inv.is_paid())
            pending_revenue = sum(inv.get_pending_amount() for inv in invoices)
            total_invoices = len(invoices)
            paid_invoices = len([inv for inv in invoices if inv.is_paid()])

            summary = {
                'total_invoices': total_invoices,
                'paid_invoices': paid_invoices,
                'unpaid_invoices': total_invoices - paid_invoices,
                'total_revenue': total_revenue,
                'pending_revenue': pending_revenue,
                'average_invoice_value': total_revenue / paid_invoices if paid_invoices > 0 else 0,
                'date_range': {
                    'from': date_from,
                    'to': date_to
                }
            }

            return OperationResult.success_result("خلاصه مالی تولید شد.", summary)

        except Exception as e:
            return OperationResult.error_result(f"خطا در تولید خلاصه مالی: {str(e)}")


class BusinessRulesService:
    """Service for implementing complex business rules."""

    def __init__(self):
        pass

    def can_delete_customer(self, customer: Customer, invoice_service: InvoiceService) -> OperationResult:
        """Check if a customer can be deleted based on business rules."""
        try:
            # Check if customer has any invoices
            criteria = InvoiceSearchCriteria(national_id=customer.national_id)
            invoices_result = invoice_service.search_invoices(criteria)

            if not invoices_result.success:
                return invoices_result

            invoices = invoices_result.data

            if invoices:
                unpaid_invoices = [inv for inv in invoices if not inv.is_paid()]
                if unpaid_invoices:
                    return OperationResult.error_result(
                        f"نمی‌توان مشتری را حذف کرد. {len(unpaid_invoices)} فاکتور پرداخت نشده دارد."
                    )

                # If all invoices are paid, allow deletion with warning
                return OperationResult.success_result(
                    f"مشتری {len(invoices)} فاکتور پرداخت شده دارد. آیا مطمئن هستید؟"
                )

            return OperationResult.success_result("مشتری قابل حذف است.")

        except Exception as e:
            return OperationResult.error_result(f"خطا در بررسی قوانین کسب‌وکار: {str(e)}")

    def can_modify_invoice(self, invoice: Invoice) -> OperationResult:
        """Check if an invoice can be modified based on business rules."""
        try:
            if invoice.is_paid():
                return OperationResult.error_result("فاکتور پرداخت شده قابل تغییر نیست.")

            if invoice.is_delivered():
                return OperationResult.error_result("فاکتور تحویل داده شده قابل تغییر نیست.")

            return OperationResult.success_result("فاکتور قابل تغییر است.")

        except Exception as e:
            return OperationResult.error_result(f"خطا در بررسی قوانین کسب‌وکار: {str(e)}")

    def calculate_payment_due_date(self, invoice: Invoice, payment_terms_days: int = 30) -> date:
        """Calculate payment due date based on business rules."""
        from datetime import timedelta
        return invoice.issue_date + timedelta(days=payment_terms_days)

    def is_invoice_overdue(self, invoice: Invoice, payment_terms_days: int = 30) -> bool:
        """Check if an invoice is overdue."""
        if invoice.is_paid():
            return False

        due_date = self.calculate_payment_due_date(invoice, payment_terms_days)
        return date.today() > due_date
