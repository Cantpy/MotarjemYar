# File: populate_aliases.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.orm_models.services_models import ServicesModel, ServiceAlias, ServiceDynamicPrice, ServiceDynamicPriceAlias

# --- Configuration ---
# Point this to the location of your services database
from shared.assets import SERVICES_DB_URL

# --- 1. DEFINE YOUR ALIASES HERE ---

SERVICE_ALIASES = {
    "کارت ملی": ["ملی", "کارت شناسایی"],
    "شناسنامه": ["ش", "تولد"],
    "گذرنامه": ["پاسپورت", "پاس"],
    "گواهی عدم سوء پیشینه": ["سوء پیشینه", "عدم سو پیشینه", "سوپیشینه"],
    "کارت پایان خدمت": ["پایان خدمت", "خدمت"],
    "مدرک دیپلم": ["دیپلم"],
    "سند ازدواج": ["ازدواج", "عقدنامه"],
    "سند طلاق": ["طلاق"],
    "وکالتنامه": ["وکالت"],
}

DYNAMIC_PRICE_ALIASES = {
    # Key is a tuple: (Service Name, Dynamic Price Name)
    ("ریزنمرات تحصیلی", "تعداد ترم"): ["ترم"],
    ("شناسنامه", "تعداد وقایع"): ["وقایع", "واقعه"],
}

# --- 2. SCRIPT LOGIC (No need to edit below here) ---

def populate_database():
    if not os.path.exists(SERVICES_DB_URL):
        print(f"Error: Database file not found at '{SERVICES_DB_URL}'")
        return

    engine = create_engine(f"sqlite:///{SERVICES_DB_URL}")
    Session = sessionmaker(bind=engine)
    session = Session()

    print("--- Populating Service Aliases ---")
    for service_name, aliases in SERVICE_ALIASES.items():
        # Find the parent service
        service = session.query(ServicesModel).filter_by(name=service_name).first()
        if not service:
            print(f"  [!] Warning: Service '{service_name}' not found. Skipping.")
            continue

        print(f"  [*] Processing '{service_name}'...")
        for alias_text in aliases:
            # Check if alias already exists to prevent duplicates
            exists = session.query(ServiceAlias).filter_by(service_id=service.id, alias=alias_text).first()
            if not exists:
                new_alias = ServiceAlias(service_id=service.id, alias=alias_text)
                session.add(new_alias)
                print(f"    - Added alias: '{alias_text}'")
            else:
                print(f"    - Alias exists: '{alias_text}'")

    print("\n--- Populating Dynamic Price Aliases ---")
    for (service_name, dp_name), aliases in DYNAMIC_PRICE_ALIASES.items():
        # Find the parent dynamic price
        dp = (
            session.query(ServiceDynamicPrice)
            .join(ServicesModel)
            .filter(ServicesModel.name == service_name, ServiceDynamicPrice.name == dp_name)
            .first()
        )
        if not dp:
            print(f"  [!] Warning: Dynamic Price '{dp_name}' for Service '{service_name}' not found. Skipping.")
            continue

        print(f"  [*] Processing '{dp_name}' for '{service_name}'...")
        for alias_text in aliases:
            # Check if alias already exists
            exists = session.query(ServiceDynamicPriceAlias).filter_by(dynamic_price_id=dp.id, alias=alias_text).first()
            if not exists:
                new_alias = ServiceDynamicPriceAlias(dynamic_price_id=dp.id, alias=alias_text)
                session.add(new_alias)
                print(f"    - Added alias: '{alias_text}'")
            else:
                print(f"    - Alias exists: '{alias_text}'")

    session.commit()
    session.close()
    print("\n✅ Alias population complete!")

if __name__ == "__main__":
    populate_database()