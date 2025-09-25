# features/Invoice_Table/invoice_table_repo.py

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from features.Invoice_Table.invoice_table_models import InvoiceData, InvoiceSummary
from shared.orm_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel
from shared.orm_models.users_models import UsersModel, UserProfileModel


class InvoiceRepository:
    """Repository for invoice-related database operations"""

    def get_all_invoices(self, session: Session) -> list[InvoiceData]:
        """Retrieve all invoices from database"""
        try:
            invoices = session.query(IssuedInvoiceModel).all()
            return [invoice.to_dataclass() for invoice in invoices]
        except SQLAlchemyError as e:
            print(f"Error retrieving invoices: {e}")
            return []

    def get_invoice_by_number(self, session: Session, invoice_number: str) -> InvoiceData | None:
        """Retrieve specific invoice by number"""
        try:
            invoice = session.query(IssuedInvoiceModel).filter(
                IssuedInvoiceModel.invoice_number == invoice_number
                ).first()
            return invoice.to_dataclass() if invoice else None
        except SQLAlchemyError as e:
            print(f"Error retrieving invoice {invoice_number}: {e}")
            return None

    def update_invoice(self, session: Session, invoice_number: str, updates: dict[str, object]) -> bool:
        """Update invoice data"""
        try:
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
            print(f"Error updating invoice {invoice_number}: {e}")
            return False

    def delete_invoices(self, session: Session, invoice_numbers: list[str]) -> bool:
        """Delete multiple invoices"""
        try:
            deleted_count = session.query(IssuedInvoiceModel).filter(
                IssuedInvoiceModel.invoice_number.in_(invoice_numbers)
            ).delete(synchronize_session=False)

            session.commit()
            return deleted_count > 0
        except SQLAlchemyError as e:
            print(f"Error deleting invoices: {e}")
            return False

    def get_document_count(self, session: Session, invoice_number: str) -> int:
        """Get document count for specific invoice"""
        try:
            total_docs = 0

            items = session.query(InvoiceItemModel).filter(
                InvoiceItemModel.invoice_number == invoice_number
            ).all()

            for item in items:
                total_docs += item.get_document_count()  # sums item_qty

            return total_docs
        except SQLAlchemyError as e:
            print(f"Error getting document count for {invoice_number}: {e}")
            return 0

    def get_all_document_counts(self, session: Session) -> dict[str, int]:
        """Get document counts for all invoices"""
        try:
            document_counts = {}

            # Get all invoice items
            items = session.query(InvoiceItemModel).all()

            for item in items:
                if item.invoice_number not in document_counts:
                    document_counts[item.invoice_number] = 0
                document_counts[item.invoice_number] += item.get_document_count()

            return document_counts
        except SQLAlchemyError as e:
            print(f"Error getting document counts: {e}")
            return {}

    def update_pdf_path(self, session: Session, invoice_number: str, new_path: str) -> bool:
        """Update PDF file path for invoice"""
        return self.update_invoice(session, invoice_number, {"pdf_file_path": new_path})

    def update_translator(self, session: Session, invoice_number: str, translator_name: str) -> bool:
        """Update translator for invoice"""
        return self.update_invoice(session, invoice_number, {"translator": translator_name})

    def get_invoice_summary(self, session: Session) -> InvoiceSummary | None:
        """Get summary statistics of invoices"""
        try:
            # Total count
            total_count = session.query(func.count(IssuedInvoiceModel.id)).scalar()

            # Total amount
            total_amount = session.query(func.sum(IssuedInvoiceModel.total_amount)).scalar() or 0

            # Translator statistics
            translator_stats = [
                (translator, count) for translator, count in session.query(
                    IssuedInvoiceModel.translator,
                    func.count(IssuedInvoiceModel.id)
                )
                .filter(
                    IssuedInvoiceModel.translator.isnot(None),
                    IssuedInvoiceModel.translator != 'نامشخص'
                )
                .group_by(IssuedInvoiceModel.translator)
                .all()
            ]

            return InvoiceSummary(
                total_count=total_count,
                total_amount=total_amount,
                translator_stats=translator_stats
            )
        except SQLAlchemyError as e:
            print(f"Error getting invoice summary: {e}")
            return None

    def export_invoices_data(self, session: Session, invoice_numbers: list[str]) -> list[dict[str, object]]:
        """Export invoice data for given invoice numbers"""
        try:
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
            print(f"Error exporting invoice data: {e}")
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
