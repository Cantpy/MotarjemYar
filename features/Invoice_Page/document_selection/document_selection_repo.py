# features/Invoice_Page/document_selection/document_selection_repo.py

from sqlalchemy.orm import Session
from shared.orm_models.services_models import ServicesModel, ServiceDynamicFee, FixedPricesModel, OtherServicesModel
from features.Invoice_Page.document_selection.document_selection_models import (Service, DynamicPrice,
                                                                                FixedPrice)


class DocumentSelectionRepository:
    """
    Stateless _repository for document selection page data operations.
    Requires a session to be passed into each method.
    """

    def get_all_services(self, session: Session) -> list[Service]:
        """Fetches and unifies services from all database tables."""
        all_services = []

        # 1. Fetch from ServicesModel (ترجمه رسمی)
        for db_s in session.query(ServicesModel).all():
            dyn_prices = [
                DynamicPrice(id=df.id, service_id=db_s.id, name=df.name, unit_price=df.unit_price)
                for df in db_s.dynamic_fees
            ]
            all_services.append(Service(
                id=db_s.id,
                name=db_s.name,
                type="ترجمه رسمی",
                base_price=db_s.base_price or 0,
                dynamic_prices=dyn_prices
            ))

        # 2. Fetch from FixedPricesModel (تعرفه ثابت)
        for db_f in session.query(FixedPricesModel).all():
            all_services.append(FixedPrice(
                id=db_f.id,
                name=db_f.name,
                price=db_f.price,
                is_default=db_f.is_default
            ))

        # 3. Fetch from OtherServicesModel (خدمات دیگر)
        for db_o in session.query(OtherServicesModel).all():
            all_services.append(Service(
                id=db_o.id,
                name=db_o.name,
                type="خدمات دیگر",
                base_price=db_o.price
            ))

        return all_services

    def get_calculation_fees(self, session: Session) -> list[FixedPrice]:
        """
        Fetches the specific fixed prices required for the calculation dialog,
        filtered by is_default=True, and maps them to FixedPrice entities.
        """
        # The database query remains the same
        db_fees = session.query(FixedPricesModel).filter_by(is_default=1).all()

        # --- FIX: Map the DB results to our clean application model ---
        app_fees = [
            FixedPrice(
                id=fee.id,
                name=fee.name,
                price=fee.price,
                is_default=fee.is_default
            ) for fee in db_fees
        ]
        return app_fees
