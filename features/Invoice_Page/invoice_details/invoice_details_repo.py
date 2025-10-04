# features/Invoice_Page/invoice_details/invoice_details_repo

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from features.Invoice_Page.invoice_preview.invoice_preview_models import PreviewOfficeInfo

from shared.orm_models.invoices_models import IssuedInvoiceModel
from shared.orm_models.users_models import TranslationOfficeDataModel


class InvoiceDetailsRepository:
    """

    """
    def get_next_invoice_number(self, invoice_session: Session) -> str:
        """
        Returns the next invoice number as a string.
        Assumes invoice numbers have a prefix and a numeric suffix, e.g. "INV-0001".
        """

        # Get the maximum invoice number string
        max_num = invoice_session.execute(
            select(func.max(IssuedInvoiceModel.invoice_number))
        ).scalar_one_or_none()

        # If no invoices exist yet, start from default
        if not max_num:
            return "INV-0001"

        # Extract numeric part using regex
        import re
        match = re.search(r'(\d+)$', max_num)
        if not match:
            # If the format doesn't contain numbers, reset numbering
            return f"{max_num}-0001"

        numeric_part = match.group(1)
        prefix = max_num[:match.start()]  # everything before the digits

        # Increment the number and pad with zeros to match length
        next_num = int(numeric_part) + 1
        next_num_str = str(next_num).zfill(len(numeric_part))

        # Combine prefix and incremented number
        return f"{prefix}{next_num_str}"

    def get_office_info(self, users_session: Session) -> PreviewOfficeInfo:
        """"""
        db_office = users_session.query(TranslationOfficeDataModel).first()
        if db_office:
            return PreviewOfficeInfo(
                name=db_office.name,
                reg_no=db_office.reg_no,
                representative=db_office.representative,
                address=db_office.address,
                phone=db_office.phone,
                email=db_office.email,
                website=db_office.website,
                telegram=db_office.telegram,
                whatsapp=db_office.whatsapp,
                logo=db_office.logo
            )
        return PreviewOfficeInfo()
