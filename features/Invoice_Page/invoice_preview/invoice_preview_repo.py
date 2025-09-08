# features/Invoice_Page/invoice_preview/invoice_preview_repo.py

from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import date

from shared.orm_models.invoices_models import IssuedInvoiceModel


# --- Repository for Data Export ---
class InvoicePreviewRepository:
    """Handles database operations for exporting invoice data."""
    def _ensure_dummy_invoice_exists(self, session: Session, invoice_number: str):
        """
        Creates a complete and valid placeholder invoice record
        to satisfy all NOT NULL constraints.
        """
        try:
            exists = session.query(IssuedInvoiceModel).filter_by(invoice_number=invoice_number).first()
            if not exists:
                # Create a record with all required fields populated
                dummy_invoice = IssuedInvoiceModel(
                    invoice_number=invoice_number,
                    name="مشتری نمونه",
                    national_id="0000000000",
                    phone="09000000000",
                    issue_date=date.today(),
                    delivery_date=date.today(),
                    translator="مترجم نمونه",
                    total_amount=1000.0,
                    total_translation_price=1000.0,
                    final_amount=1000.0,
                    pdf_file_path=None  # Path is initially null
                )
                session.add(dummy_invoice)
                session.commit()
        finally:
            session.close()

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
