# features/Invoice_Page/document_selection/document_selection_repo.py

"""

"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from shared.orm_models.business_models import (ServicesModel, SmartSearchHistoryModel, ServiceDynamicPrice,
                                               FixedPricesModel, OtherServicesModel)
from features.Invoice_Page.document_selection.document_selection_models import Service, FixedPrice, DynamicPrice


class DocumentSelectionRepository:
    """
    Stateless _repository for document selection page data operations.
    Requires a session to be passed into each method.
    """

    def get_all_services(self, session: Session) -> list[Service]:
        """Fetches and unifies services from all database tables."""
        all_services = []

        # 1. Fetch from ServicesModel (ترجمه رسمی)
        query = (
            session.query(ServicesModel)
            .options(
                joinedload(ServicesModel.dynamic_prices).joinedload(ServiceDynamicPrice.aliases),
                joinedload(ServicesModel.aliases)
            )
        )
        for db_s in query.all():

            dyn_prices = []
            for fee in db_s.dynamic_prices:
                # Extract aliases safe-guarding against empty lists
                fee_aliases = [a.alias for a in fee.aliases]

                dyn_prices.append(DynamicPrice(
                    id=fee.id,
                    service_id=db_s.id,
                    name=fee.name,
                    unit_price=fee.unit_price,
                    aliases=fee_aliases
                ))

            aliases = [alias.alias for alias in db_s.aliases]

            all_services.append(Service(
                id=db_s.id,
                name=db_s.name,
                type="ترجمه رسمی",
                base_price=db_s.base_price or 0,
                default_page_count=db_s.default_page_count,
                dynamic_prices=dyn_prices,
                aliases=aliases
            ))

        # 2. Fetch from FixedPricesModel (تعرفه ثابت)
        for db_f in session.query(FixedPricesModel).all():
            all_services.append(FixedPrice(
                id=db_f.id,
                name=db_f.name,
                price=db_f.price,
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
        Fetches the specific fixed prices required for the calculation dialog.
        """
        # The database query remains the same
        db_fees = session.query(FixedPricesModel).all()

        # --- FIX: Map the DB results to our clean application model ---
        app_fees = [
            FixedPrice(
                id=fee.id,
                name=fee.name,
                price=fee.price,
            ) for fee in db_fees
        ]
        return app_fees

    def get_smart_search_history(self, session: Session, limit: int = 100) -> list[str]:
        """
        Fetches the most recently used smart search entries.
        """
        history_items = (
            session.query(SmartSearchHistoryModel)
            .order_by(desc(SmartSearchHistoryModel.created_at))
            .limit(limit)
            .all()
        )
        return [item.entry for item in history_items]

    def add_smart_search_entry(self, session: Session, entry_text: str):
        """
        Adds a new entry to the smart search history, avoiding duplicates.
        """
        # Check if the entry already exists to prevent integrity errors
        exists = session.query(SmartSearchHistoryModel).filter_by(entry=entry_text).first()
        if not exists:
            new_entry = SmartSearchHistoryModel(entry=entry_text)
            session.add(new_entry)

    def get_all_fixed_prices(self, session: Session) -> list[FixedPrice]:
        """Fetches all items from the fixed_prices table."""
        db_items = session.query(FixedPricesModel).order_by(FixedPricesModel.name).all()
        return [
            FixedPrice(id=item.id, name=item.name, price=item.price)
            for item in db_items
        ]

    def update_fixed_prices(self, session: Session, updated_prices: list[FixedPrice]):
        """Updates the price for a list of FixedPrice objects."""
        for fp_update in updated_prices:
            # Find the database object by its ID and update it
            db_fp = session.query(FixedPricesModel).filter_by(id=fp_update.id).first()
            if db_fp:
                db_fp.price = fp_update.price
