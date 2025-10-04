# features/Invoice_Page/invoice_preview/invoice_preview_repo.py

from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import date

from shared.orm_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel


# --- Repository for Data Export ---
class InvoicePreviewRepository:
    """
    Handles database operations for exporting invoice data.
    """
    def issue_invoice(self, session: Session,
                      invoice_orm: IssuedInvoiceModel,
                      items_orm: list[InvoiceItemModel]) -> tuple[bool, str]:
        """
        Saves a new invoice and its items to the database in a single transaction.
        If an invoice with the same number exists, it will be overwritten.
        """
        try:
            # Check if the invoice already exists to overwrite it
            existing_invoice = session.query(IssuedInvoiceModel).filter_by(
                invoice_number=invoice_orm.invoice_number
            ).first()

            if existing_invoice:
                # The ondelete="CASCADE" in the relationship should handle deleting the old items
                session.delete(existing_invoice)
                # Flush the session to execute the delete command before adding the new one
                session.flush()

            # Add the new invoice and its items
            session.add(invoice_orm)
            session.add_all(items_orm)
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
