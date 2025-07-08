# -*- coding: utf-8 -*-

from typing import List, Dict, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, date
from features.InvoicePage import (Customer, Service, IssuedInvoice, InvoiceItem, DatabaseManager, FixedPrice,
                                  OtherService)


class InvoiceBackend:
    """Backend service for managing invoice operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    # Customer operations
    def get_all_customers(self) -> List[Customer]:
        """Retrieve all customers from the database."""
        with self.db_manager.get_customers_session() as session:
            return session.query(Customer).all()

    def get_customer_by_national_id(self, national_id: str) -> Optional[Customer]:
        """Find a customer by their national ID."""
        with self.db_manager.get_customers_session() as session:
            return session.query(Customer).filter(Customer.national_id == national_id).first()

    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Find a customer by their phone number."""
        with self.db_manager.get_customers_session() as session:
            return session.query(Customer).filter(Customer.phone == phone).first()

    def get_customer_by_name(self, name: str) -> Optional[Customer]:
        """Find a customer by their name."""
        with self.db_manager.get_customers_session() as session:
            return session.query(Customer).filter(Customer.name == name).first()

    def save_customer(self, national_id: str, name: str, phone: str, address: str,
                      telegram_id: str = None, email: str = None, passport_image: str = None) -> Tuple[bool, str]:
        """
        Save a new customer to the database.
        Returns (success, message)
        """
        try:
            with self.db_manager.get_customers_session() as session:
                customer = Customer(
                    national_id=national_id,
                    name=name,
                    phone=phone,
                    address=address,
                    telegram_id=telegram_id,
                    email=email,
                    passport_image=passport_image
                )
                session.add(customer)
                session.commit()
                return True, "مشتری با موفقیت ذخیره شد!"
        except IntegrityError:
            return False, "کد ملی یا شماره تلفن تکراری است."
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def delete_customer(self, national_id: str) -> Tuple[bool, str]:
        """
        Delete a customer by national ID.
        Returns (success, message)
        """
        try:
            with self.db_manager.get_customers_session() as session:
                customer = session.query(Customer).filter(Customer.national_id == national_id).first()
                if not customer:
                    return False, "مشتری با این کد ملی پیدا نشد."

                customer_name = customer.name
                session.delete(customer)
                session.commit()
                return True, f"مشتری {customer_name} با موفقیت حذف شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def get_customer_suggestions(self, field: str) -> List[str]:
        """Get unique values for autocomplete suggestions."""
        try:
            with self.db_manager.get_customers_session() as session:
                if field == "name":
                    results = session.query(Customer.name).distinct().all()
                elif field == "phone":
                    results = session.query(Customer.phone).distinct().all()
                elif field == "national_id":
                    results = session.query(Customer.national_id).distinct().all()
                else:
                    return []

                return [result[0] for result in results if result[0]]
        except SQLAlchemyError:
            return []

    # Service operations
    def get_all_services(self) -> List[Service]:
        """Retrieve all services from the database."""
        with self.db_manager.get_services_session() as session:
            return session.query(Service).all()

    def get_service_by_name(self, name: str) -> Optional[Service]:
        """Find a service by name."""
        with self.db_manager.get_services_session() as session:
            return session.query(Service).filter(Service.name == name).first()

    def get_service_names(self) -> List[str]:
        """Get all service names for autocomplete."""
        try:
            with self.db_manager.get_services_session() as session:
                results = session.query(Service.name).all()
                return [result[0] for result in results]
        except SQLAlchemyError:
            return []

    def get_service_base_price(self, service_name: str) -> int:
        """Get the base price of a service."""
        service = self.get_service_by_name(service_name)
        return service.base_price if service else 0

    def get_service_dynamic_price_1(self, service_name: str) -> Optional[int]:
        """Get the first dynamic price of a service."""
        service = self.get_service_by_name(service_name)
        return service.dynamic_price_1 if service else None

    def get_service_dynamic_price_2(self, service_name: str) -> Optional[int]:
        """Get the second dynamic price of a service."""
        service = self.get_service_by_name(service_name)
        return service.dynamic_price_2 if service else None

    def get_service_dynamic_price_name_1(self, service_name: str) -> Optional[str]:
        """Get the first dynamic price name of a service."""
        service = self.get_service_by_name(service_name)
        return service.dynamic_price_name_1 if service else None

    def get_service_dynamic_price_name_2(self, service_name: str) -> Optional[str]:
        """Get the second dynamic price name of a service."""
        service = self.get_service_by_name(service_name)
        return service.dynamic_price_name_2 if service else None

    # Fixed Price operations
    def get_all_fixed_prices(self) -> List[FixedPrice]:
        """Retrieve all fixed prices from the database."""
        with self.db_manager.get_services_session() as session:
            return session.query(FixedPrice).all()

    def get_fixed_price_by_name(self, name: str) -> Optional[FixedPrice]:
        """Find a fixed price by name."""
        with self.db_manager.get_services_session() as session:
            return session.query(FixedPrice).filter(FixedPrice.name == name).first()

    # Other Service operations
    def get_all_other_services(self) -> List[OtherService]:
        """Retrieve all other services from the database."""
        with self.db_manager.get_services_session() as session:
            return session.query(OtherService).all()

    def get_other_service_by_name(self, name: str) -> Optional[OtherService]:
        """Find an other service by name."""
        with self.db_manager.get_services_session() as session:
            return session.query(OtherService).filter(OtherService.name == name).first()

    # Invoice operations
    def get_current_invoice_number(self) -> int:
        """Get the next available invoice number."""
        try:
            with self.db_manager.get_invoices_session() as session:
                last_invoice = session.query(IssuedInvoice).order_by(IssuedInvoice.invoice_number.desc()).first()
                return last_invoice.invoice_number + 1 if last_invoice else 1000
        except SQLAlchemyError:
            return 1000

    def create_invoice(self, invoice_number: int, name: str, national_id: str, phone: str,
                       issue_date: date, delivery_date: date, translator: str,
                       total_amount: int = 0, total_translation_price: int = 0,
                       advance_payment: int = 0, discount_amount: int = 0,
                       force_majeure: int = 0, final_amount: int = 0,
                       source_language: str = None, target_language: str = None,
                       remarks: str = None, username: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create a new invoice.
        Returns (success, message, invoice_id)
        """
        try:
            with self.db_manager.get_invoices_session() as session:
                invoice = IssuedInvoice(
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
                session.add(invoice)
                session.commit()
                return True, "فاکتور با موفقیت ایجاد شد!", invoice.id
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}", None

    def add_invoice_item(self, invoice_number: int, item_name: str, item_qty: int,
                         item_price: int, officiality: int = 0,
                         judiciary_seal: int = 0, foreign_affairs_seal: int = 0,
                         remarks: str = None) -> Tuple[bool, str]:
        """
        Add an item to an invoice.
        Returns (success, message)
        """
        try:
            with self.db_manager.get_invoices_session() as session:
                invoice_item = InvoiceItem(
                    invoice_number=invoice_number,
                    item_name=item_name,
                    item_qty=item_qty,
                    item_price=item_price,
                    officiality=officiality,
                    judiciary_seal=judiciary_seal,
                    foreign_affairs_seal=foreign_affairs_seal,
                    remarks=remarks
                )
                session.add(invoice_item)
                session.commit()
                return True, "آیتم با موفقیت به فاکتور اضافه شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def get_invoice_items(self, invoice_number: int) -> List[InvoiceItem]:
        """Get all items for a specific invoice by invoice number."""
        try:
            with self.db_manager.get_invoices_session() as session:
                return session.query(InvoiceItem).filter(InvoiceItem.invoice_number == invoice_number).all()
        except SQLAlchemyError:
            return []

    def get_invoice_by_number(self, invoice_number: int) -> Optional[IssuedInvoice]:
        """Get an invoice by invoice number."""
        try:
            with self.db_manager.get_invoices_session() as session:
                return session.query(IssuedInvoice).filter(IssuedInvoice.invoice_number == invoice_number).first()
        except SQLAlchemyError:
            return None

    def update_invoice_total(self, invoice_number: int, total_amount: int,
                             total_translation_price: int = None, final_amount: int = None) -> Tuple[bool, str]:
        """Update the total amounts of an invoice."""
        try:
            with self.db_manager.get_invoices_session() as session:
                invoice = session.query(IssuedInvoice).filter(IssuedInvoice.invoice_number == invoice_number).first()
                if not invoice:
                    return False, "فاکتور پیدا نشد."

                invoice.total_amount = total_amount
                if total_translation_price is not None:
                    invoice.total_translation_price = total_translation_price
                if final_amount is not None:
                    invoice.final_amount = final_amount

                session.commit()
                return True, "مجموع فاکتور به‌روزرسانی شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def delete_invoice_item(self, item_id: int) -> Tuple[bool, str]:
        """Delete an invoice item."""
        try:
            with self.db_manager.get_invoices_session() as session:
                item = session.query(InvoiceItem).filter(InvoiceItem.id == item_id).first()
                if not item:
                    return False, "آیتم پیدا نشد."

                session.delete(item)
                session.commit()
                return True, "آیتم با موفقیت حذف شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def update_invoice_payment_status(self, invoice_number: int, payment_status: int) -> Tuple[bool, str]:
        """Update the payment status of an invoice."""
        try:
            with self.db_manager.get_invoices_session() as session:
                invoice = session.query(IssuedInvoice).filter(IssuedInvoice.invoice_number == invoice_number).first()
                if not invoice:
                    return False, "فاکتور پیدا نشد."

                invoice.payment_status = payment_status
                session.commit()
                return True, "وضعیت پرداخت به‌روزرسانی شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def update_invoice_delivery_status(self, invoice_number: int, delivery_status: int) -> Tuple[bool, str]:
        """Update the delivery status of an invoice."""
        try:
            with self.db_manager.get_invoices_session() as session:
                invoice = session.query(IssuedInvoice).filter(IssuedInvoice.invoice_number == invoice_number).first()
                if not invoice:
                    return False, "فاکتور پیدا نشد."

                invoice.delivery_status = delivery_status
                session.commit()
                return True, "وضعیت تحویل به‌روزرسانی شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"

    def get_unpaid_invoices(self) -> List[IssuedInvoice]:
        """Get all unpaid invoices."""
        try:
            with self.db_manager.get_invoices_session() as session:
                return session.query(IssuedInvoice).filter(IssuedInvoice.payment_status == 0).all()
        except SQLAlchemyError:
            return []

    def get_pending_delivery_invoices(self) -> List[IssuedInvoice]:
        """Get all invoices with pending delivery status."""
        try:
            with self.db_manager.get_invoices_session() as session:
                return session.query(IssuedInvoice).filter(IssuedInvoice.delivery_status.in_([0, 1, 2, 3])).all()
        except SQLAlchemyError:
            return []

    def calculate_invoice_totals(self, invoice_number: int) -> Dict[str, int]:
        """Calculate various totals for an invoice based on its items."""
        items = self.get_invoice_items(invoice_number)

        total_items_price = sum(item.item_qty * item.item_price for item in items)
        total_items = len(items)
        total_official_docs = sum(item.officiality for item in items)
        total_judiciary_docs = sum(item.judiciary_seal for item in items)
        total_foreign_docs = sum(item.foreign_affairs_seal for item in items)
        total_pages = sum(item.item_qty for item in items)

        return {
            'total_items_price': total_items_price,
            'total_items': total_items,
            'total_official_docs': total_official_docs,
            'total_judiciary_docs': total_judiciary_docs,
            'total_foreign_docs': total_foreign_docs,
            'total_pages': total_pages
        }

    def update_invoice_totals_from_items(self, invoice_number: int) -> Tuple[bool, str]:
        """Update invoice totals based on its items."""
        try:
            totals = self.calculate_invoice_totals(invoice_number)

            with self.db_manager.get_invoices_session() as session:
                invoice = session.query(IssuedInvoice).filter(IssuedInvoice.invoice_number == invoice_number).first()
                if not invoice:
                    return False, "فاکتور پیدا نشد."

                invoice.total_amount = totals['total_items_price']
                invoice.total_translation_price = totals['total_items_price']
                invoice.total_official_docs_count = totals['total_official_docs']
                invoice.total_unofficial_docs_count = totals['total_items'] - totals['total_official_docs']
                invoice.total_pages_count = totals['total_pages']
                invoice.total_judiciary_count = totals['total_judiciary_docs']
                invoice.total_foreign_affairs_count = totals['total_foreign_docs']
                invoice.total_additional_doc_count = totals['total_items']

                # Calculate final amount (total - discount - advance + force_majeure)
                invoice.final_amount = (invoice.total_amount - invoice.discount_amount -
                                        invoice.advance_payment + invoice.force_majeure)

                session.commit()
                return True, "مجموع فاکتور به‌روزرسانی شد!"
        except SQLAlchemyError as e:
            return False, f"خطای پایگاه داده: {str(e)}"


class ValidationService:
    """Service for validating input data."""

    @staticmethod
    def validate_customer_data(name: str, phone: str, national_id: str, address: str) -> Dict[str, str]:
        """
        Validate customer input data.
        Returns a dictionary with field names as keys and error messages as values.
        """
        errors = {}

        if not name.strip():
            errors['name'] = "نام مشتری نباید خالی باشد."

        if not (phone.isdigit() and 10 <= len(phone) <= 11):
            errors['phone'] = "شماره تلفن مشتری باید ۱۰ تا ۱۱ رقم باشد."

        if not (national_id.isdigit() and len(national_id) == 10):
            errors['national_id'] = "کد ملی مشتری باید ۱۰ رقم باشد."

        if not address.strip():
            errors['address'] = "آدرس مشتری نباید خالی باشد."

        return errors

    @staticmethod
    def validate_service_name(service_name: str) -> bool:
        """Validate service name is not empty."""
        return bool(service_name.strip())

    @staticmethod
    def validate_numeric_input(value: str, field_name: str) -> Tuple[bool, str, int]:
        """
        Validate numeric input for integer fields.
        Returns (is_valid, error_message, parsed_value)
        """
        try:
            parsed_value = int(value)
            if parsed_value < 0:
                return False, f"{field_name} نمی‌تواند منفی باشد.", 0
            return True, "", parsed_value
        except (ValueError, TypeError):
            return False, f"{field_name} باید یک عدد معتبر باشد.", 0

    @staticmethod
    def validate_invoice_data(name: str, national_id: str, phone: str, translator: str) -> Dict[str, str]:
        """
        Validate invoice input data.
        Returns a dictionary with field names as keys and error messages as values.
        """
        errors = {}

        if not name.strip():
            errors['name'] = "نام نباید خالی باشد."

        if not (national_id.isdigit() and len(national_id) == 10):
            errors['national_id'] = "کد ملی باید ۱۰ رقم باشد."

        if not (phone.isdigit() and 10 <= len(phone) <= 11):
            errors['phone'] = "شماره تلفن باید ۱۰ تا ۱۱ رقم باشد."

        if not translator.strip():
            errors['translator'] = "نام مترجم نباید خالی باشد."

        return errors

    @staticmethod
    def validate_invoice_item_data(item_name: str, item_qty: str, item_price: str) -> Dict[str, str]:
        """
        Validate invoice item input data.
        Returns a dictionary with field names as keys and error messages as values.
        """
        errors = {}

        if not item_name.strip():
            errors['item_name'] = "نام آیتم نباید خالی باشد."

        try:
            qty = int(item_qty)
            if qty <= 0:
                errors['item_qty'] = "تعداد باید بزرگتر از صفر باشد."
        except (ValueError, TypeError):
            errors['item_qty'] = "تعداد باید یک عدد معتبر باشد."

        try:
            price = int(item_price)
            if price < 0:
                errors['item_price'] = "قیمت نمی‌تواند منفی باشد."
        except (ValueError, TypeError):
            errors['item_price'] = "قیمت باید یک عدد معتبر باشد."

        return errors

    @staticmethod
    def validate_payment_status(status: int) -> bool:
        """Validate payment status (0 or 1)."""
        return status in [0, 1]

    @staticmethod
    def validate_delivery_status(status: int) -> bool:
        """Validate delivery status (0, 1, 2, 3, or 4)."""
        return status in [0, 1, 2, 3, 4]

    @staticmethod
    def validate_boolean_field(value: int) -> bool:
        """Validate boolean fields (0 or 1)."""
        return value in [0, 1]