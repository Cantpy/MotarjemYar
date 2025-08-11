"""
Repository layer for Invoice Details using SQLAlchemy ORM.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError

from features.InvoicePage.invoice_details.invoice_details_models import TranslationOfficeInfo, UserInfo
from shared.models.sqlalchemy_models import IssuedInvoiceModel, UsersModel, TranslationOfficeDataModel


class InvoiceDetailsRepository:
    """Repository for invoice details operations."""

    def __init__(self,
                 invoices_db_session: Session,
                 users_db_session: Session):
        """Initialize repository with database session."""
        self.invoices_db_session = invoices_db_session
        self.users_db_session = users_db_session

    def get_next_invoice_number(self) -> str:
        """Get the next invoice number by incrementing the last issued invoice number."""
        try:
            last_invoice = (
                self.invoices_db_session.query(IssuedInvoiceModel)
                .order_by(desc(IssuedInvoiceModel.invoice_number))
                .first()
            )

            if last_invoice:
                return str(last_invoice.invoice_number + 1)
            else:
                return "نامشخص"  # invoice_number not found

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting next invoice number: {str(e)}")

    def get_user_info(self, username: str) -> Optional[UserInfo]:
        """Get user information by username."""
        try:
            user = (
                self.users_db_session.query(UsersModel)
                .filter(UsersModel.username == username)
                .filter(UsersModel.active == 1)
                .first()
            )

            if user:
                return UserInfo(
                    username=user.username,
                    role=user.role,
                    active=bool(user.active),
                    start_date=user.start_date,
                    end_date=user.end_date
                )
            return None

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting user info: {str(e)}")

    def get_translation_office_info(self) -> Optional[TranslationOfficeInfo]:
        """Get translation office information."""
        try:
            office = (
                self.users_db_session.query(TranslationOfficeDataModel)
                .order_by(desc(TranslationOfficeDataModel.updated_at))
                .first()
            )

            if office:
                return TranslationOfficeInfo(
                    name=office.name or "",
                    registration_number=office.reg_no or "",
                    representative=office.representative or "",
                    manager=office.manager or "",
                    address=office.address or "",
                    phone=office.phone or "",
                    website=office.website,
                    whatsapp=office.whatsapp,
                    instagram=office.instagram,
                    telegram=office.telegram,
                    other_media=office.other_media,
                    open_hours=office.open_hours,
                    map_url=office.map_url,
                )
            return None

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting translation office info: {str(e)}")

    def invoice_number_exists(self, invoice_number: str) -> bool:
        """Check if an invoice number already exists."""
        try:
            count = (
                self.invoices_db_session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.invoice_number == int(invoice_number))
                .count()
            )
            return count > 0

        except (SQLAlchemyError, ValueError) as e:
            raise Exception(f"Error checking invoice number existence: {str(e)}")

    def get_user_invoices_count(self, username: str) -> int:
        """Get the count of invoices created by a specific user."""
        try:
            count = (
                self.invoices_db_session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.username == username)
                .count()
            )
            return count

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting user invoices count: {str(e)}")

    def get_total_invoices_count(self) -> int:
        """Get the total count of all invoices."""
        try:
            count = self.invoices_db_session.query(IssuedInvoiceModel).count()
            return count

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting total invoices count: {str(e)}")

    def get_recent_invoices(self, limit: int = 10):
        """Get recent invoices."""
        try:
            invoices = (
                self.invoices_db_session.query(IssuedInvoiceModel)
                .order_by(desc(IssuedInvoiceModel.issue_date))
                .limit(limit)
                .all()
            )
            return invoices

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting recent invoices: {str(e)}")

    def update_translation_office_info(self, office_info: TranslationOfficeInfo) -> bool:
        """Update translation office information."""
        try:
            # Get existing record or create new one
            office = self.users_db_session.query(TranslationOfficeDataModel).first()

            if office:
                # Update existing record
                office.name = office_info.name
                office.reg_no = office_info.registration_number
                office.representative = office_info.representative
                office.manager = office_info.manager
                office.address = office_info.address
                office.phone = office_info.phone
                office.website = office_info.website
                office.whatsapp = office_info.whatsapp
                office.instagram = office_info.instagram
                office.telegram = office_info.telegram
                office.other_media = office_info.other_media
                office.open_hours = office_info.open_hours
                office.map_url = office_info.map_url
                office.updated_at = datetime.now()
            else:
                # Create new record
                office = TranslationOfficeDataModel(
                    name=office_info.name,
                    reg_no=office_info.registration_number,
                    representative=office_info.representative,
                    manager=office_info.manager,
                    address=office_info.address,
                    phone=office_info.phone,
                    website=office_info.website,
                    whatsapp=office_info.whatsapp,
                    instagram=office_info.instagram,
                    telegram=office_info.telegram,
                    other_media=office_info.other_media,
                    open_hours=office_info.open_hours,
                    map_url=office_info.map_url,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.users_db_session.add(office)

            self.users_db_session.commit()
            return True

        except SQLAlchemyError as e:
            self.users_db_session.rollback()
            raise Exception(f"Database error while updating translation office info: {str(e)}")

    def validate_user_permission(self, username: str, required_permissions: list = None) -> bool:
        """Validate if user has required permissions."""
        try:
            user = (
                self.users_db_session.query(UsersModel)
                .filter(UsersModel.username == username)
                .filter(UsersModel.active == 1)
                .first()
            )

            if not user:
                return False

            # If no specific permissions required, just check if user is active
            if not required_permissions:
                return True

            # Check role-based permissions
            allowed_roles = required_permissions
            return user.role in allowed_roles

        except SQLAlchemyError as e:
            raise Exception(f"Database error while validating user permissions: {str(e)}")

    def get_invoice_statistics(self) -> dict:
        """Get invoice statistics."""
        try:
            stats = {
                'total_invoices': self.invoices_db_session.query(IssuedInvoiceModel).count(),
                'paid_invoices': self.invoices_db_session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.payment_status == 1).count(),
                'unpaid_invoices': self.invoices_db_session.query(IssuedInvoiceModel)
                .filter(IssuedInvoiceModel.payment_status == 0).count(),
                'total_revenue': self.invoices_db_session.query(
                    func.sum(IssuedInvoiceModel.final_amount)
                ).scalar() or 0
            }
            return stats

        except SQLAlchemyError as e:
            raise Exception(f"Database error while getting invoice statistics: {str(e)}")
