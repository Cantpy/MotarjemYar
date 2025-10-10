# features/Invoice_Page/invoice_details/invoice_details_repo

from sqlalchemy.orm import Session

from features.Invoice_Page.invoice_preview.invoice_preview_models import PreviewOfficeInfo

from shared.orm_models.users_models import TranslationOfficeDataModel


class InvoiceDetailsRepository:
    """
    The stateless and pure database access layer for the invoice details step.
    This class should contain no business logic, only raw data operations.
    """

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
