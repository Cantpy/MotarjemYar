# shared/mock_data/populate_services.py

from sqlalchemy.orm import Session
from ..orm_models.services_models import ServicesModel, FixedPricesModel


def populate_services_db(services_session: Session):
    """Populates the Services.db with mock services and fixed prices."""
    if services_session.query(ServicesModel).first():
        return  # Data already exists

    print("Populating Services.db with mock services...")

    # --- Standard Translation Services ---
    service_names = [
        "ترجمه شناسنامه", "ترجمه کارت ملی", "ترجمه سند ازدواج",
        "ترجمه مدرک تحصیلی", "ترجمه گواهینامه", "ترجمه سند ملکی",
        "ترجمه ریز نمرات", "ترجمه روزنامه رسمی"
    ]
    services = [ServicesModel(name=name) for name in service_names]
    services_session.add_all(services)

    # --- Fixed Prices for Seals (Crucial for Report Calculations) ---
    seal_prices = [
        FixedPricesModel(
            name="مهر دادگستری",
            price=80000,
            is_default=True,
            label_name='judiciary_seal'
        ),
        FixedPricesModel(
            name="مهر وزارت امور خارجه",
            price=150000,
            is_default=True,
            label_name='foreign_affairs_seal'
        )
    ]
    services_session.add_all(seal_prices)

    services_session.commit()
