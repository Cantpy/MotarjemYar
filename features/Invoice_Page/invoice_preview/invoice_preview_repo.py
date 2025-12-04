# features/Invoice_Page/invoice_preview/invoice_preview_repo.py

"""
Repository for handling database operations related to invoice preview and issuance.
"""

from sqlalchemy import update, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional

from shared.orm_models.business_models import IssuedInvoiceModel, InvoiceItemModel, EditedInvoiceModel


# --- Repository for Data Export ---
class InvoicePreviewRepository:
    """
    Handles database operations for exporting invoice data.
    """
    def issue_invoice(self, session: Session,
                      invoice_orm: IssuedInvoiceModel,
                      items_orm: List[InvoiceItemModel],
                      edit_logs: Optional[List[EditedInvoiceModel]] = None) -> tuple[bool, str]:
        """
        Saves a new invoice, its items, and any associated edit logs
        to the database in a single transaction.
        """
        try:
            # Check if the invoice already exists to overwrite it (This logic is for the first issue)
            existing_invoice = session.query(IssuedInvoiceModel).filter_by(
                invoice_number=invoice_orm.invoice_number
            ).first()

            if existing_invoice:
                session.delete(existing_invoice)
                session.flush()

            # Add the new invoice and its items
            session.add(invoice_orm)
            session.add_all(items_orm)

            # If there are edit logs, add them to the session as well
            if edit_logs:
                session.add_all(edit_logs)

            session.commit()
            return True, "فاکتور با موفقیت صادر و در پایگاه داده ثبت شد."

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error during invoice issue: {e}")
            return False, f"خطا در ثبت فاکتور در پایگاه داده: {e}"

    def get_invoice_path(self, session: Session, invoice_number: str) -> str | None:
        """Retrieves the saved file path for a given invoice number."""
        try:
            invoice = session.query(IssuedInvoiceModel).filter_by(invoice_number=invoice_number).first()
            return invoice.pdf_file_path if invoice else None
        except SQLAlchemyError as e:
            print(f"Database error while getting path: {e}")
            return None

    def update_invoice_path(self, session: Session, invoice_number: str, file_path: str) -> bool:
        """Updates or overwrites the file path for a given invoice number."""
        try:
            stmt = (
                update(IssuedInvoiceModel)
                .where(IssuedInvoiceModel.invoice_number == invoice_number)
                .values(pdf_file_path=file_path)
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            print(f"Database error while updating path: {e}")
            session.rollback()
            return False

    def get_issued_invoice(self, session: Session, invoice_number: str) -> IssuedInvoiceModel | None:
        return session.query(IssuedInvoiceModel).filter_by(invoice_number=invoice_number).first()

    def get_issued_invoice_with_items(self, session: Session, invoice_number: str) -> IssuedInvoiceModel | None:
        """
        Fetches a single invoice and eagerly loads its associated items
        in a single, efficient query.
        """
        return (
            session.query(IssuedInvoiceModel)
            .options(joinedload(IssuedInvoiceModel.items))
            .filter_by(invoice_number=invoice_number)
            .first()
        )

    def get_latest_invoice_version(self, session: Session, base_invoice_number: str) -> IssuedInvoiceModel | None:
        """

        Finds the most recent version of an invoice by a base number
        (e.g., for base 'INV-101', it finds 'INV-101-v3' over 'INV-101-v2').
        """
        return (
            session.query(IssuedInvoiceModel)
            .filter(IssuedInvoiceModel.invoice_number.like(f"{base_invoice_number}%"))
            .order_by(desc(IssuedInvoiceModel.invoice_number))
            .first()
        )
