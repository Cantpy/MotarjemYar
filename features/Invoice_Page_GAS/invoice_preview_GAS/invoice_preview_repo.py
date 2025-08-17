# repo.py

import os
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import date
from shared.database_models.invoices_models import IssuedInvoiceModel, BaseInvoices
from features.Invoice_Page_GAS.invoice_preview_GAS.invoice_preview_assets import INVOICES_DB_URL


# Create engines for each database
# customers_engine = create_engine(CUSTOMERS_DB_URL)
invoices_engine = create_engine(INVOICES_DB_URL)
# services_engine = create_engine(SERVICES_DB_URL)
# users_engine = create_engine(USERS_DB_URL)

# Session makers
# CustomersSession = sessionmaker(bind=customers_engine)
InvoicesSession = sessionmaker(bind=invoices_engine)
# ServicesSession = sessionmaker(bind=services_engine)
# UsersSession = sessionmaker(bind=users_engine)


# --- Repository for Data Export ---
class InvoiceRepository:
    """Handles database operations for exporting invoice data."""

    def __init__(self):
        # Create tables if they don't exist
        BaseInvoices.metadata.create_all(invoices_engine)
        # Base.metadata.create_all(customers_engine)
        # Base.metadata.create_all(users_engine)

        self._ensure_dummy_invoice_exists("140399")

    def _ensure_dummy_invoice_exists(self, invoice_number: str):
        """
        FIXED: Creates a complete and valid placeholder invoice record
        to satisfy all NOT NULL constraints.
        """
        session = InvoicesSession()
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

    def get_invoice_path(self, invoice_number: str) -> Optional[str]:
        """Retrieves the saved file path for a given invoice number."""
        session = InvoicesSession()
        try:
            invoice = session.query(IssuedInvoiceModel).filter_by(invoice_number=invoice_number).first()
            if invoice and invoice.pdf_file_path:
                return invoice.pdf_file_path
            return None
        except SQLAlchemyError as e:
            print(f"Database error while getting path: {e}")
            return None
        finally:
            session.close()

    def update_invoice_path(self, invoice_number: str, file_path: str) -> bool:
        """Updates or overwrites the file path for a given invoice number."""
        session = InvoicesSession()
        try:
            stmt = (
                update(IssuedInvoiceModel)
                .where(IssuedInvoiceModel.invoice_number == invoice_number)
                .values(pdf_file_path=file_path)
            )
            result = session.execute(stmt)
            session.commit()
            # Check if any row was actually updated
            return result.rowcount > 0
        except SQLAlchemyError as e:
            print(f"Database error while updating path: {e}")
            session.rollback()
            return False
        finally:
            session.close()
