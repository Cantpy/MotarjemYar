from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from shared.database_models.invoices_models import IssuedInvoiceModel
from shared.database_models.user_models import TranslationOfficeDataModel
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_models import OfficeInfo
from features.Invoice_Page_GAS.invoice_details_GAS.invoice_details_assets import INVOICES_DB_URL, USERS_DB_URL


class InvoiceDetailsRepository:
    def __init__(self):
        self.inv_engine = create_engine(f"sqlite:///{INVOICES_DB_URL}")
        self.usr_engine = create_engine(f"sqlite:///{USERS_DB_URL}")
        self.InvSession = sessionmaker(bind=self.inv_engine)
        self.UsrSession = sessionmaker(bind=self.usr_engine)

    def get_next_invoice_number(self) -> int:
        with self.InvSession() as session:
            # Find the max invoice number and add 1
            max_num = session.execute(select(func.max(IssuedInvoiceModel.invoice_number))).scalar_one_or_none()
            return (max_num or 0) + 1

    def get_office_info(self) -> OfficeInfo:
        with self.UsrSession() as session:
            db_office = session.query(TranslationOfficeDataModel).first()
            if db_office:
                return OfficeInfo(
                    name=db_office.name, reg_no=db_office.reg_no, representative=db_office.representative,
                    address=db_office.address, phone=db_office.phone, email=db_office.email
                )
            return OfficeInfo()  # Return empty object if not found
