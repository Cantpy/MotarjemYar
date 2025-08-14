# document_selection/repo.py
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database_models.services_models import ServicesModel, FixedPricesModel, OtherServicesModel
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_models import (Service, DynamicPrice,
                                                                                        FixedPrice)
from features.Invoice_Page_GAS.document_selection_GAS.document_selection_assets import SERVICES_DATABASE_URL


class DocumentSelectionRepository:
    def __init__(self, db_file=SERVICES_DATABASE_URL):
        self.engine = create_engine(f"sqlite:///{db_file}")
        self.Session = sessionmaker(bind=self.engine)

    def get_all_services(self) -> List[Service]:
        """Fetches and unifies services from all database tables."""
        with self.Session() as session:
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

    def get_calculation_fees(self) -> List[FixedPrice]:
        """
        Fetches the specific fixed prices required for the calculation dialog,
        filtered by is_default=True, and maps them to FixedPrice entities.
        """
        with self.Session() as session:
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
