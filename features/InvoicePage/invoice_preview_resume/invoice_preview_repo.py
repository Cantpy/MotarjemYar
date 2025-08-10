"""
Repository layer for invoice preview data access using SQLAlchemy.
"""

from typing import List, Optional, Dict, Any
import json
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError

from features.InvoicePage.invoice_preview_resume.invoice_preview_models import (InvoiceData,
                                                                                InvoiceItem,
                                                                                InvoiceSummary,
                                                                                InvoiceStatistics)


class InvoicePreviewRepository:
    """Repository for invoice preview database operations."""

    def __init__(self, session: Session):
        self.session = session

    def save_invoice(self, invoice_data: InvoiceData, table_data: List[List[str]]) -> bool:
        """Save or update an invoice in the database."""
        try:
            from shared.models.sqlalchemy_models import IssuedInvoiceModel, InvoiceItemModel  # Import your actual models

            # Check if invoice exists
            existing_invoice = self.session.query(IssuedInvoiceModel).filter_by(
                invoice_number=invoice_data.invoice_number
            ).first()

            if existing_invoice:
                # Update existing invoice
                self._update_invoice_fields(existing_invoice, invoice_data)
            else:
                # Create new invoice
                existing_invoice = IssuedInvoiceModel(
                    invoice_number=invoice_data.invoice_number,
                    name=invoice_data.customer_name,
                    national_id=invoice_data.national_id,
                    phone=invoice_data.phone,
                    issue_date=invoice_data.issue_date,
                    delivery_date=invoice_data.delivery_date,
                    translator=invoice_data.translator,
                    total_amount=invoice_data.total_amount,
                    advance_payment=invoice_data.advance_payment,
                    discount_amount=invoice_data.discount_amount,
                    final_amount=invoice_data.final_amount,
                    source_language=invoice_data.source_language,
                    target_language=invoice_data.target_language,
                    remarks=invoice_data.remarks,
                    username=invoice_data.username,
                    pdf_file_path=invoice_data.pdf_file_path,
                    total_translation_price=invoice_data.summary.total_translation_price,
                    total_official_docs_count=invoice_data.summary.total_official_docs_count,
                    total_unofficial_docs_count=invoice_data.summary.total_unofficial_docs_count,
                    total_pages_count=invoice_data.summary.total_pages_count,
                    total_judiciary_count=invoice_data.summary.total_judiciary_count,
                    total_foreign_affairs_count=invoice_data.summary.total_foreign_affairs_count,
                    total_additional_doc_count=invoice_data.summary.total_additional_doc_count,
                    payment_status=0,  # Default to unpaid
                    delivery_status=0  # Default to not delivered
                )
                self.session.add(existing_invoice)

            # Delete existing items
            self.session.query(InvoiceItemModel).filter_by(
                invoice_number=invoice_data.invoice_number
            ).delete()

            # Add new items from table data
            for row_data in table_data:
                if len(row_data) > 1 and row_data[1].strip():  # Assuming column 1 contains item description
                    item = InvoiceItemModel(
                        invoice_number=invoice_data.invoice_number,
                        item_name=row_data[1],
                        item_qty=int(row_data[2]) if len(row_data) > 2 and row_data[2].strip() else 1,
                        item_price=int(row_data[6]) if len(row_data) > 6 and row_data[6].strip() else 0,
                        officiality=1 if len(row_data) > 1 and 'رسمی' in row_data[1] else 0,
                        judiciary_seal=int(row_data[3]) if len(row_data) > 3 and row_data[3].strip() else 0,
                        foreign_affairs_seal=int(row_data[4]) if len(row_data) > 4 and row_data[4].strip() else 0
                    )
                    self.session.add(item)

            self.session.commit()
            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error in save_invoice: {e}")
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Unexpected error in save_invoice: {e}")
            return False

    def _update_invoice_fields(self, invoice: Any, invoice_data: InvoiceData):
        """Update existing invoice fields."""
        invoice.name = invoice_data.customer_name
        invoice.national_id = invoice_data.national_id
        invoice.phone = invoice_data.phone
        invoice.delivery_date = invoice_data.delivery_date
        invoice.translator = invoice_data.translator
        invoice.total_amount = invoice_data.total_amount
        invoice.advance_payment = invoice_data.advance_payment
        invoice.discount_amount = invoice_data.discount_amount
        invoice.final_amount = invoice_data.final_amount
        invoice.source_language = invoice_data.source_language
        invoice.target_language = invoice_data.target_language
        invoice.remarks = invoice_data.remarks
        invoice.pdf_file_path = invoice_data.pdf_file_path
        invoice.total_translation_price = invoice_data.summary.total_translation_price
        invoice.total_official_docs_count = invoice_data.summary.total_official_docs_count
        invoice.total_unofficial_docs_count = invoice_data.summary.total_unofficial_docs_count
        invoice.total_pages_count = invoice_data.summary.total_pages_count
        invoice.total_judiciary_count = invoice_data.summary.total_judiciary_count
        invoice.total_foreign_affairs_count = invoice_data.summary.total_foreign_affairs_count
        invoice.total_additional_doc_count = invoice_data.summary.total_additional_doc_count

    def load_invoice(self, invoice_number: int) -> Optional[InvoiceData]:
        """Load an invoice from the database."""
        try:
            from shared.models.sqlalchemy_models import IssuedInvoiceModel, InvoiceItemModel

            invoice = self.session.query(IssuedInvoiceModel).filter_by(
                invoice_number=invoice_number
            ).first()

            if not invoice:
                return None

            # Load invoice items
            items = self.session.query(InvoiceItemModel).filter_by(
                invoice_number=invoice_number
            ).all()

            invoice_items = [
                InvoiceItem(
                    item_name=item.item_name,
                    item_qty=item.item_qty,
                    item_price=item.item_price,
                    officiality=item.officiality,
                    judiciary_seal=item.judiciary_seal,
                    foreign_affairs_seal=item.foreign_affairs_seal,
                    remarks=item.remarks
                )
                for item in items
            ]

            summary = InvoiceSummary(
                total_official_docs_count=invoice.total_official_docs_count or 0,
                total_unofficial_docs_count=invoice.total_unofficial_docs_count or 0,
                total_pages_count=invoice.total_pages_count or 0,
                total_judiciary_count=invoice.total_judiciary_count or 0,
                total_foreign_affairs_count=invoice.total_foreign_affairs_count or 0,
                total_additional_doc_count=invoice.total_additional_doc_count or 0,
                total_translation_price=invoice.total_translation_price or 0
            )

            return InvoiceData(
                invoice_number=invoice.invoice_number,
                customer_name=invoice.name,
                national_id=invoice.national_id,
                phone=invoice.phone,
                issue_date=invoice.issue_date,
                delivery_date=invoice.delivery_date,
                translator=invoice.translator,
                total_amount=invoice.total_amount,
                advance_payment=invoice.advance_payment or 0,
                discount_amount=invoice.discount_amount or 0,
                final_amount=invoice.final_amount,
                source_language=invoice.source_language,
                target_language=invoice.target_language,
                remarks=invoice.remarks,
                username=invoice.username,
                pdf_file_path=invoice.pdf_file_path,
                items=invoice_items,
                summary=summary
            )

        except SQLAlchemyError as e:
            print(f"Database error in load_invoice: {e}")
            return None

    def delete_invoice(self, invoice_number: int) -> bool:
        """Delete an invoice from the database."""
        try:
            from shared.models.sqlalchemy_models import IssuedInvoiceModel

            invoice = self.session.query(IssuedInvoiceModel).filter_by(
                invoice_number=invoice_number
            ).first()

            if not invoice:
                return False

            self.session.delete(invoice)
            self.session.commit()
            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error in delete_invoice: {e}")
            return False

    def get_all_invoices_for_user(self, username: str) -> List[Dict[str, Any]]:
        """Get all invoices for a specific user."""
        try:
            from shared.models.sqlalchemy_models import IssuedInvoiceModel

            invoices = self.session.query(IssuedInvoiceModel).filter_by(
                username=username
            ).order_by(desc(IssuedInvoiceModel.issue_date)).all()

            return [
                {
                    'invoice_number': inv.invoice_number,
                    'customer_name': inv.name,
                    'issue_date': inv.issue_date,
                    'total_amount': inv.total_amount,
                    'final_amount': inv.final_amount,
                    'payment_status': inv.payment_status,
                    'delivery_status': inv.delivery_status,
                    'total_official_docs_count': inv.total_official_docs_count,
                    'total_unofficial_docs_count': inv.total_unofficial_docs_count,
                    'total_pages_count': inv.total_pages_count,
                    'total_judiciary_count': inv.total_judiciary_count,
                    'total_foreign_affairs_count': inv.total_foreign_affairs_count,
                    'total_additional_doc_count': inv.total_additional_doc_count,
                    'total_translation_price': inv.total_translation_price
                }
                for inv in invoices
            ]

        except SQLAlchemyError as e:
            print(f"Database error in get_all_invoices_for_user: {e}")
            return []

    def get_invoice_statistics(self, username: str) -> InvoiceStatistics:
        """Get statistics about invoices for a user."""
        try:
            from shared.models.sqlalchemy_models import IssuedInvoiceModel

            result = self.session.query(
                func.count(IssuedInvoiceModel.id).label('total_invoices'),
                func.count(func.case([(IssuedInvoiceModel.payment_status == 0, 1)])).label('draft_invoices'),
                func.count(func.case([(IssuedInvoiceModel.payment_status == 1, 1)])).label('final_invoices'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_amount), 0).label('total_revenue'),
                func.coalesce(func.avg(IssuedInvoiceModel.total_amount), 0).label('average_invoice_amount'),
                func.coalesce(func.sum(IssuedInvoiceModel.advance_payment), 0).label('total_advances'),
                func.coalesce(func.sum(IssuedInvoiceModel.discount_amount), 0).label('total_discounts'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_official_docs_count), 0).label('total_official_docs'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_unofficial_docs_count), 0).label('total_unofficial_docs'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_pages_count), 0).label('total_pages'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_judiciary_count), 0).label('total_judiciary'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_foreign_affairs_count), 0).label('total_foreign_affairs'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_additional_doc_count), 0).label('total_additional_docs'),
                func.coalesce(func.sum(IssuedInvoiceModel.total_translation_price), 0).label('total_translation_revenue')
            ).filter_by(username=username).first()

            if result:
                return InvoiceStatistics(
                    total_invoices=result.total_invoices,
                    draft_invoices=result.draft_invoices,
                    final_invoices=result.final_invoices,
                    total_revenue=float(result.total_revenue),
                    average_invoice_amount=float(result.average_invoice_amount),
                    total_advances=float(result.total_advances),
                    total_discounts=float(result.total_discounts),
                    total_official_docs=result.total_official_docs,
                    total_unofficial_docs=result.total_unofficial_docs,
                    total_pages=result.total_pages,
                    total_judiciary=result.total_judiciary,
                    total_foreign_affairs=result.total_foreign_affairs,
                    total_additional_docs=result.total_additional_docs,
                    total_translation_revenue=float(result.total_translation_revenue)
                )

            return InvoiceStatistics()

        except SQLAlchemyError as e:
            print(f"Database error in get_invoice_statistics: {e}")
            return InvoiceStatistics()

    def update_invoice_status(self, invoice_number: int, payment_status: int = None,
                             delivery_status: int = None) -> bool:
        """Update the status of an invoice."""
        try:
            from shared.models.sqlalchemy_models import IssuedInvoiceModel

            invoice = self.session.query(IssuedInvoiceModel).filter_by(
                invoice_number=invoice_number
            ).first()

            if not invoice:
                return False

            if payment_status is not None:
                invoice.payment_status = payment_status
            if delivery_status is not None:
                invoice.delivery_status = delivery_status

            self.session.commit()
            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Database error in update_invoice_status: {e}")
            return False

    def get_invoice_items(self, invoice_number: int) -> List[InvoiceItem]:
        """Get all items for a specific invoice."""
        try:
            from shared.models.sqlalchemy_models import InvoiceItemModel

            items = self.session.query(InvoiceItemModel).filter_by(
                invoice_number=invoice_number
            ).all()

            return [
                InvoiceItem(
                    item_name=item.item_name,
                    item_qty=item.item_qty,
                    item_price=item.item_price,
                    officiality=item.officiality,
                    judiciary_seal=item.judiciary_seal,
                    foreign_affairs_seal=item.foreign_affairs_seal,
                    remarks=item.remarks
                )
                for item in items
            ]

        except SQLAlchemyError as e:
            print(f"Database error in get_invoice_items: {e}")
            return []

    def get_translation_office_data(self) -> Optional[Dict[str, Any]]:
        """Get translation office information."""
        try:
            from shared.models.sqlalchemy_models import TranslationOfficeDataModl

            office = self.session.query(TranslationOfficeDataModl).first()
            if office:
                return {
                    'name': office.name,
                    'reg_no': office.reg_no,
                    'address': office.address,
                    'phone': office.phone,
                    'website': office.website,
                    'representative': office.representative,
                    'manager': office.manager
                }
            return None

        except SQLAlchemyError as e:
            print(f"Database error in get_translation_office_data: {e}")
            return None

    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        try:
            from shared.models.sqlalchemy_models import UserProfileModel

            profile = self.session.query(UserProfileModel).filter_by(
                username=username
            ).first()

            if profile:
                return {
                    'full_name': profile.full_name,
                    'role_fa': profile.role_fa,
                    'email': profile.email,
                    'phone': profile.phone,
                    'national_id': profile.national_id
                }
            return None

        except SQLAlchemyError as e:
            print(f"Database error in get_user_profile: {e}")
            return None
