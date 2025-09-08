# features/Invoice_Page/document_selection/document_selection_repo.py

from sqlalchemy.orm import Session
from shared.orm_models.services_models import ServicesModel, FixedPricesModel, OtherServicesModel
from features.Invoice_Page.document_selection.document_selection_models import (Service, DynamicPrice,
                                                                                FixedPrice)


class DocumentSelectionRepository:
    """
    Stateless repository for document selection page data operations.
    Requires a session to be passed into each method.
    """
    def get_all_services(self, session: Session) -> list[Service]:
        """Fetches and unifies services from all database tables."""
        all_services = []
        # 1. Fetch from ServicesModel
        for db_s in session.query(ServicesModel).all():
            dyn_prices = []
            if db_s.dynamic_price_name_1 and db_s.dynamic_price_1 is not None:
                dyn_prices.append(DynamicPrice(name=db_s.dynamic_price_name_1, price=db_s.dynamic_price_1))
            if db_s.dynamic_price_name_2 and db_s.dynamic_price_2 is not None:
                dyn_prices.append(DynamicPrice(name=db_s.dynamic_price_name_2, price=db_s.dynamic_price_2))
            all_services.append(Service(name=db_s.name, type="ترجمه رسمی", base_price=db_s.base_price or 0,
                                        dynamic_prices=dyn_prices))

        # 2. Fetch from OtherServicesModel
        for db_o in session.query(OtherServicesModel).all():
            all_services.append(Service(name=db_o.name, type="خدمات دیگر", base_price=db_o.price))

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
                name=fee.name,
                label_name=fee.label_name or fee.name,
                price=fee.price,
            ) for fee in db_fees
        ]
        return app_fees
