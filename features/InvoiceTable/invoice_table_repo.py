from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from features.InvoiceTable.invoice_table_models import (
    InvoiceData, InvoiceSummary
)
from shared.orm_models.invoices_models import BaseInvoices, IssuedInvoiceModel, InvoiceItemModel
from shared.orm_models.users_models import BaseUsers, UsersModel, UserProfileModel
import logging
from shared import return_resource


logger = logging.getLogger(__name__)

invoices_db_path = return_resource('databases', 'invoices.db')
users_db_path = return_resource('databases', 'users.db')


class DatabaseRepository:
    """Repository class for database operations using SQLAlchemy ORM"""

    def __init__(self, invoices_db_url: str = invoices_db_path, users_db_url: str = users_db_path):
        """Initialize database connections"""
        self.invoices_engine = create_engine(invoices_db_url)
        self.users_engine = create_engine(users_db_url)

        # Create sessionmakers
        self.InvoicesSession = sessionmaker(bind=self.invoices_engine)
        self.UsersSession = sessionmaker(bind=self.users_engine)

        # Create tables if they don't exist
        BaseInvoices.metadata.create_all(self.invoices_engine)
        BaseUsers.metadata.create_all(self.users_engine)


class InvoiceRepository(DatabaseRepository):
    """Repository for invoice-related database operations"""

    def get_all_invoices(self) -> List[InvoiceData]:
        """Retrieve all invoices from database"""
        try:
            with self.InvoicesSession() as session:
                invoices = session.query(IssuedInvoiceModel).all()
                return [invoice.to_dataclass() for invoice in invoices]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving invoices: {e}")
            return []

    def get_invoice_by_number(self, invoice_number: str) -> Optional[InvoiceData]:
        """Retrieve specific invoice by number"""
        try:
            with self.InvoicesSession() as session:
                invoice = session.query(IssuedInvoiceModel).filter(
                    IssuedInvoiceModel.invoice_number == invoice_number
                ).first()
                return invoice.to_dataclass() if invoice else None
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving invoice {invoice_number}: {e}")
            return None

    def update_invoice(self, invoice_number: str, updates: Dict[str, Any]) -> bool:
        """Update invoice data"""
        try:
            with self.InvoicesSession() as session:
                invoice = session.query(IssuedInvoiceModel).filter(
                    IssuedInvoiceModel.invoice_number == invoice_number
                ).first()

                if not invoice:
                    return False

                for key, value in updates.items():
                    if hasattr(invoice, key):
                        setattr(invoice, key, value)

                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating invoice {invoice_number}: {e}")
            return False

    def delete_invoices(self, invoice_numbers: List[str]) -> bool:
        """Delete multiple invoices"""
        try:
            with self.InvoicesSession() as session:
                deleted_count = session.query(IssuedInvoiceModel).filter(
                    IssuedInvoiceModel.invoice_number.in_(invoice_numbers)
                ).delete(synchronize_session=False)

                session.commit()
                return deleted_count > 0
        except SQLAlchemyError as e:
            logger.error(f"Error deleting invoices: {e}")
            return False

    def get_document_count(self, invoice_number: str) -> int:
        """Get document count for specific invoice"""
        try:
            with self.InvoicesSession() as session:
                total_docs = 0

                items = session.query(InvoiceItemModel).filter(
                    InvoiceItemModel.invoice_number == invoice_number
                ).all()

                for item in items:
                    total_docs += item.get_document_count()  # sums item_qty

                return total_docs
        except SQLAlchemyError as e:
            logger.error(f"Error getting document count for {invoice_number}: {e}")
            return 0

    def get_all_document_counts(self) -> Dict[str, int]:
        """Get document counts for all invoices"""
        try:
            with self.InvoicesSession() as session:
                document_counts = {}

                # Get all invoice items
                items = session.query(InvoiceItemModel).all()

                for item in items:
                    if item.invoice_number not in document_counts:
                        document_counts[item.invoice_number] = 0
                    document_counts[item.invoice_number] += item.get_document_count()

                return document_counts
        except SQLAlchemyError as e:
            logger.error(f"Error getting document counts: {e}")
            return {}

    def update_pdf_path(self, invoice_number: str, new_path: str) -> bool:
        """Update PDF file path for invoice"""
        return self.update_invoice(invoice_number, {"pdf_file_path": new_path})

    def update_translator(self, invoice_number: str, translator_name: str) -> bool:
        """Update translator for invoice"""
        return self.update_invoice(invoice_number, {"translator": translator_name})

    def get_invoice_summary(self) -> Optional[InvoiceSummary]:
        """Get summary statistics of invoices"""
        try:
            with self.InvoicesSession() as session:
                # Total count
                total_count = session.query(func.count(IssuedInvoiceModel.id)).scalar()

                # Total amount
                total_amount = session.query(func.sum(IssuedInvoiceModel.total_amount)).scalar() or 0

                # Translator statistics
                translator_stats = session.query(
                    IssuedInvoiceModel.translator,
                    func.count(IssuedInvoiceModel.id)
                ).filter(
                    IssuedInvoiceModel.translator.isnot(None),
                    IssuedInvoiceModel.translator != 'نامشخص'
                ).group_by(IssuedInvoiceModel.translator).all()

                return InvoiceSummary(
                    total_count=total_count,
                    total_amount=total_amount,
                    translator_stats=translator_stats
                )
        except SQLAlchemyError as e:
            logger.error(f"Error getting invoice summary: {e}")
            return None

    def export_invoices_data(self, invoice_numbers: List[str]) -> List[Dict[str, Any]]:
        """Export invoice data for given invoice numbers"""
        try:
            with self.InvoicesSession() as session:
                invoices = session.query(IssuedInvoiceModel).filter(
                    IssuedInvoiceModel.invoice_number.in_(invoice_numbers)
                ).all()

                return [
                    {
                        'invoice_number': inv.invoice_number,
                        'name': inv.name,
                        'national_id': inv.national_id,
                        'phone': inv.phone,
                        'issue_date': inv.issue_date,
                        'delivery_date': inv.delivery_date,
                        'translator': inv.translator,
                        'total_amount': inv.total_amount
                    }
                    for inv in invoices
                ]
        except SQLAlchemyError as e:
            logger.error(f"Error exporting invoice data: {e}")
            return []


class UserRepository(DatabaseRepository):
    """Repository for user-related database operations"""

    def get_translator_names(self) -> List[str]:
        """Get list of translator names"""
        translator_names = ["نامشخص"]

        try:
            with self.UsersSession() as session:
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
            logger.error(f"Error loading translator names: {e}")
            # Fallback names
            translator_names.extend(["مریم", "علی", "رضا"])

        return translator_names

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data by username"""
        try:
            with self.UsersSession() as session:
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
            logger.error(f"Error getting user {username}: {e}")
            return None

    def create_user(self, username: str, role: str, full_name: str = None) -> bool:
        """Create a new user with profile"""
        try:
            with self.UsersSession() as session:
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
            logger.error(f"Error creating user: {e}")
            return False

    def update_user_profile(self, username: str, full_name: str) -> bool:
        """Update user profile"""
        try:
            with self.UsersSession() as session:
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
            logger.error(f"Error updating user profile: {e}")
            return False


class RepositoryManager:
    """Manager class to coordinate different repositories"""

    def __init__(self, invoices_db_url: str = invoices_db_path, users_db_url: str = users_db_path):
        self.invoice_repo = InvoiceRepository(invoices_db_url, users_db_url)
        self.user_repo = UserRepository(invoices_db_url, users_db_url)

    def get_invoice_repository(self) -> InvoiceRepository:
        """Get invoice repository instance"""
        return self.invoice_repo

    def get_user_repository(self) -> UserRepository:
        """Get user repository instance"""
        return self.user_repo
