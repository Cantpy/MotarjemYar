# features/Invoice_Table/invoice_table_repo.py

import getpass
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional

from features.Invoice_Table.invoice_table_models import InvoiceSummary
from shared.orm_models.invoices_models import (IssuedInvoiceModel, InvoiceItemModel, DeletedInvoiceModel,
                                               InvoiceItemData, InvoiceData, EditedInvoiceModel, EditedInvoiceData,
                                               DeletedInvoiceData)
from shared.orm_models.users_models import UsersModel, UserProfileModel
from shared.orm_models.services_models import ServicesModel, ServiceDynamicPrice


class InvoiceRepository:
    """Repository for invoice-related database operations."""

    # ─────────────────────────────── Retrieval ─────────────────────────────── #

    def get_all_invoices(self, session: Session) -> list[InvoiceData]:
        """Retrieve all issued invoices."""
        try:
            invoices = session.query(IssuedInvoiceModel).all()
            return [invoice.to_dataclass() for invoice in invoices]
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to retrieve all invoices: {e}")
            return []

    def get_invoice_by_number(self, session: Session, invoice_number: str) -> Optional[InvoiceData]:
        """Retrieve a specific invoice by its number."""
        try:
            invoice = (
                session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.invoice_number == invoice_number)
                .one_or_none()
            )
            return invoice.to_dataclass() if invoice else None
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to get invoice {invoice_number}: {e}")
            return None

    def get_invoice_and_items(
        self, session: Session, invoice_number: str
    ) -> tuple[Optional[InvoiceData], list[InvoiceItemData]]:
        """Retrieve an invoice and its items together."""
        try:
            invoice_orm = (
                session.query(IssuedInvoiceModel)
                .filter_by(invoice_number=invoice_number)
                .one_or_none()
            )

            if not invoice_orm:
                return None, []

            items_orm = (
                session.query(InvoiceItemModel)
                .filter_by(invoice_number=invoice_number)
                .all()
            )

            return (
                invoice_orm.to_dataclass(),
                [item.to_dataclass() for item in items_orm],
            )
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to fetch invoice and items for {invoice_number}: {e}")
            return None, []

    # ─────────────────────────────── Services & Prices ─────────────────────────────── #

    def get_services_and_dynamic_prices(
        self, session: Session, service_ids: set[int], dynamic_price_ids: set[int]
    ) -> tuple[dict[int, str], dict[int, str]]:
        """Batch-fetch service and dynamic price names from the services database."""
        try:
            service_map = {}
            dynamic_price_map = {}

            if service_ids:
                services = (
                    session.query(ServicesModel)
                    .filter(ServicesModel.id.in_(service_ids))
                    .all()
                )
                service_map = {s.id: s.name for s in services}

            if dynamic_price_ids:
                dynamic_prices = (
                    session.query(ServiceDynamicPrice)
                    .filter(ServiceDynamicPrice.id.in_(dynamic_price_ids))
                    .all()
                )
                dynamic_price_map = {dp.id: dp.name for dp in dynamic_prices}

            return service_map, dynamic_price_map
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to fetch services or dynamic prices: {e}")
            return {}, {}

    # ─────────────────────────────── Update Operations ─────────────────────────────── #

    def update_invoice(self, session: Session, invoice_number: str, updates: dict[str, object]) -> bool:
        """Update a specific invoice."""
        try:
            invoice = (
                session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.invoice_number == invoice_number)
                .one_or_none()
            )

            if not invoice:
                return False

            for key, value in updates.items():
                if hasattr(invoice, key):
                    setattr(invoice, key, value)

            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"[ERROR] Failed to update invoice {invoice_number}: {e}")
            return False

    def update_pdf_path(self, session: Session, invoice_number: str, new_path: str) -> bool:
        """Update PDF file path."""
        return self.update_invoice(session, invoice_number, {"pdf_file_path": new_path})

    def update_translator(self, session: Session, invoice_number: str, translator_name: str) -> bool:
        """Update translator."""
        return self.update_invoice(session, invoice_number, {"translator": translator_name})

    # ─────────────────────────────── Deletion (Soft) ─────────────────────────────── #

    def delete_invoice(self, session: Session, invoice_number: str, deleted_by_user: str) -> bool:
        """
        Moves a single invoice to the deleted_invoices table instead of permanently deleting it.
        This is an atomic operation for one invoice.
        """
        try:
            # Step 1: Retrieve the full invoice object to be deleted
            invoice_to_delete = session.query(IssuedInvoiceModel).filter(
                IssuedInvoiceModel.invoice_number == invoice_number
            ).first()

            if not invoice_to_delete:
                print(f"Invoice {invoice_number} not found for deletion.")
                return False

            # Step 2: Create a DeletedInvoiceModel instance
            # --- UPDATED: Now copies all new financial fields ---
            deleted_invoice = DeletedInvoiceModel(
                invoice_number=invoice_to_delete.invoice_number,
                name=invoice_to_delete.name,
                national_id=invoice_to_delete.national_id,
                phone=invoice_to_delete.phone,
                issue_date=invoice_to_delete.issue_date,
                delivery_date=invoice_to_delete.delivery_date,
                translator=invoice_to_delete.translator,
                total_items=invoice_to_delete.total_items,
                total_amount=invoice_to_delete.total_amount,
                total_translation_price=invoice_to_delete.total_translation_price,
                total_certified_copy_price=invoice_to_delete.total_certified_copy_price,
                total_registration_price=invoice_to_delete.total_registration_price,
                total_confirmation_price=invoice_to_delete.total_confirmation_price,
                total_additional_issues_price=invoice_to_delete.total_additional_issues_price,
                advance_payment=invoice_to_delete.advance_payment,
                discount_amount=invoice_to_delete.discount_amount,
                emergency_cost=invoice_to_delete.emergency_cost,
                final_amount=invoice_to_delete.final_amount,
                payment_status=invoice_to_delete.payment_status,
                delivery_status=invoice_to_delete.delivery_status,
                source_language=invoice_to_delete.source_language,
                target_language=invoice_to_delete.target_language,
                username=invoice_to_delete.username,
                pdf_file_path=invoice_to_delete.pdf_file_path,
                remarks=invoice_to_delete.remarks,
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by_user
            )
            session.add(deleted_invoice)

            # Step 3: Delete the original invoice
            session.delete(invoice_to_delete)

            # Step 4: Commit the transaction for this single invoice
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error moving invoice {invoice_number} to deleted table: {e}")
            return False

    # ─────────────────────────────── Aggregations ─────────────────────────────── #

    def get_document_count(self, session: Session, invoice_number: str) -> int:
        """Get total quantity of documents for an invoice."""
        try:
            count = (
                session.query(func.sum(InvoiceItemModel.quantity))
                .filter(InvoiceItemModel.invoice_number == invoice_number)
                .scalar()
            )
            return count or 0
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to count documents for {invoice_number}: {e}")
            return 0

    def get_all_document_counts(self, session: Session) -> dict[str, int]:
        """Get document counts for all invoices."""
        try:
            results = (
                session.query(
                    InvoiceItemModel.invoice_number,
                    func.sum(InvoiceItemModel.quantity),
                )
                .group_by(InvoiceItemModel.invoice_number)
                .all()
            )
            return {inv_num: count for inv_num, count in results}
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to get all document counts: {e}")
            return {}

    # ─────────────────────────────── Summaries & Exports ─────────────────────────────── #

    def get_invoice_summary(self, session: Session) -> Optional[InvoiceSummary]:
        """Generate general statistics for invoices."""
        try:
            total_count = session.query(func.count(IssuedInvoiceModel.id)).scalar() or 0
            total_amount = session.query(func.sum(IssuedInvoiceModel.total_amount)).scalar() or 0

            translator_stats = [
                (translator, count)
                for translator, count in session.query(
                    IssuedInvoiceModel.translator, func.count(IssuedInvoiceModel.id)
                )
                .filter(
                    IssuedInvoiceModel.translator.isnot(None),
                    IssuedInvoiceModel.translator != "نامشخص",
                )
                .group_by(IssuedInvoiceModel.translator)
                .all()
            ]

            return InvoiceSummary(
                total_count=total_count,
                total_amount=total_amount,
                translator_stats=translator_stats,
            )
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to get invoice summary: {e}")
            return None

    def export_invoices_data(self, session: Session, invoice_numbers: list[str]) -> list[dict[str, object]]:
        """Export simplified invoice data."""
        try:
            invoices = (
                session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.invoice_number.in_(invoice_numbers))
                .all()
            )
            return [
                {
                    "invoice_number": inv.invoice_number,
                    "name": inv.name,
                    "national_id": inv.national_id,
                    "phone": inv.phone,
                    "issue_date": inv.issue_date,
                    "delivery_date": inv.delivery_date,
                    "translator": inv.translator,
                    "total_amount": inv.total_amount,
                }
                for inv in invoices
            ]
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to export invoices: {e}")
            return []

    # ─────────────────────────────── Edit History ─────────────────────────────── #

    def add_invoice_edits(self, session: Session, edits: list[EditedInvoiceData]) -> bool:
        """Adds a batch of edit history records to the database."""
        try:
            orm_edits = [
                EditedInvoiceModel(
                    invoice_number=edit.invoice_number,
                    edited_field=edit.edited_field,
                    old_value=edit.old_value,
                    new_value=edit.new_value,
                    edited_by=edit.edited_by,
                    edited_at=edit.edited_at,
                    remarks=edit.remarks
                )
                for edit in edits
            ]
            session.bulk_save_objects(orm_edits)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"[ERROR] Failed to add invoice edit history: {e}")
            return False

    def get_edit_history_by_invoice_number(self, session: Session, invoice_number: str) -> list[EditedInvoiceData]:
        """Retrieves all edit history for a specific invoice, ordered by date."""
        try:
            history_orm = (
                session.query(EditedInvoiceModel)
                .filter(EditedInvoiceModel.invoice_number == invoice_number)
                .order_by(EditedInvoiceModel.edited_at.desc())
                .all()
            )
            return [item.to_dataclass() for item in history_orm]
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to retrieve edit history for {invoice_number}: {e}")
            return []

    def get_all_deleted_invoices(self, session: Session) -> list[DeletedInvoiceData]:
        """Retrieve all deleted invoices, ordered by deletion date."""
        try:
            invoices = (
                session.query(DeletedInvoiceModel)
                .order_by(DeletedInvoiceModel.deleted_at.desc())
                .all()
            )
            return [invoice.to_dataclass() for invoice in invoices]
        except SQLAlchemyError as e:
            print(f"[ERROR] Failed to retrieve deleted invoices: {e}")
            return []


class UserRepository:
    """Repository for user-related database operations"""

    def get_translator_names(self, session: Session) -> list[str]:
        """Get list of translator names"""
        translator_names = ["نامشخص"]

        try:
            # Get active translators with their profiles
            translators = session.query(UsersModel).join(UserProfileModel).filter(
                UsersModel.role == 'translator',
                UsersModel.active == True,
                UserProfileModel.full_name.isnot(None)
            ).all()

            for translator in translators:
                if translator.profile and translator.profile.full_name:
                    translator_names.append(translator.profile.full_name)
        except SQLAlchemyError as e:
            print(f"Error loading translator names: {e}")
            # Fallback names
            translator_names.extend(["مریم", "علی", "رضا"])

        return translator_names

    def get_user_by_username(self, session: Session, username: str) -> dict[str, object] | None:
        """Get user data by username"""
        try:
            user = session.query(UsersModel).filter(UsersModel.username == username).first()
            if user:
                return {
                    'username': user.username,
                    'role': user.role,
                    'active': user.active,
                    'full_name': user.profile.full_name if user.profile else None
                }
            return None
        except SQLAlchemyError as e:
            print(f"Error getting user {username}: {e}")
            return None

    def create_user(self, session: Session, username: str, role: str, full_name: str = None) -> bool:
        """Create a new user with profile"""
        try:
            # Create user
            user = UsersModel(username=username, role=role)
            session.add(user)
            session.flush()  # To get the user ID

            # Create profile if full_name provided
            if full_name:
                profile = UserProfileModel(username=username, full_name=full_name)
                session.add(profile)

            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f"Error creating user: {e}")
            return False

    def update_user_profile(self, session: Session, username: str, full_name: str) -> bool:
        """Update user profile"""
        try:
            profile = session.query(UserProfileModel).filter(
                UserProfileModel.username == username
            ).first()

            if profile:
                profile.full_name = full_name
            else:
                profile = UserProfileModel(username=username, full_name=full_name)
                session.add(profile)

            session.commit()
            return True
        except SQLAlchemyError as e:
            print(f"Error updating user profile: {e}")
            return False


class RepositoryManager:
    """Manager class to coordinate different repositories"""

    def __init__(self):
        self.invoice_repo = InvoiceRepository()
        self.user_repo = UserRepository()

    def get_invoice_repository(self) -> InvoiceRepository:
        """Get invoice _repository instance"""
        return self.invoice_repo

    def get_user_repository(self) -> UserRepository:
        """Get user _repository instance"""
        return self.user_repo
