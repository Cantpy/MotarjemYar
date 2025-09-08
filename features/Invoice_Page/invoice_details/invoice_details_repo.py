from sqlalchemy import select, func
from sqlalchemy.orm import Session

from features.Invoice_Page.invoice_details.invoice_details_models import OfficeInfo

from shared.orm_models.invoices_models import IssuedInvoiceModel
from shared.orm_models.users_models import TranslationOfficeDataModel


class InvoiceDetailsRepository:
    """

    """
    def get_next_invoice_number(self, invoice_session: Session) -> int:
        """"""
        # Find the max invoice number and add 1
        max_num = invoice_session.execute(select(func.max(IssuedInvoiceModel.invoice_number))).scalar_one_or_none()
        return (max_num or 0) + 1

    def get_office_info(self, users_session: Session) -> OfficeInfo:
        """"""
        db_office = users_session.query(TranslationOfficeDataModel).first()
        if db_office:
            return OfficeInfo(
                name=db_office.name, reg_no=db_office.reg_no, representative=db_office.representative,
                address=db_office.address, phone=db_office.phone, email=db_office.email,
                socials=db_office.other_media
            )
        return OfficeInfo()  # Return empty object if not found
