# shared/mock_data/populate_invoices.py

import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta
import jdatetime

from ..orm_models.invoices_models import IssuedInvoiceModel
from ..orm_models.customer_models import CustomerModel
from ..orm_models.users_models import UsersModel


def populate_invoices_db(invoices_session: Session, customers_session: Session, users_session: Session):
    """Populates Invoices.db with historical and dashboard-targeted data."""
    if invoices_session.query(IssuedInvoiceModel).first():
        return  # Data already exists

    print("Populating Invoices.db with mock invoices...")

    # --- Fetch dependencies from other databases ---
    all_customers = customers_session.query(CustomerModel).all()
    all_users = users_session.query(UsersModel).all()

    if not all_customers or not all_users:
        print("[WARNING] Cannot create invoices without customers or users. Skipping invoice population.")
        return

    # Filter users by role
    clerks = [u for u in all_users if u.role == 'clerk']
    translators = [u for u in all_users if u.role == 'translator']

    if not clerks or not translators:
        print("[WARNING] No clerks or translators found in Users.db. Invoice creation might be limited.")
        return

    invoices = []
    today = date.today()
    today_j = jdatetime.date.today()

    # --- A) Historical data for reports (last 3 years) ---
    for i in range(300):
        customer = random.choice(all_customers)
        clerk = random.choice(clerks)
        translator = random.choice(translators)
        issue_d = today - relativedelta(months=random.randint(1, 35), days=random.randint(0, 28))
        total_amount = random.randint(800000, 5000000)

        invoices.append(IssuedInvoiceModel(
            invoice_number=1400000 + i,
            name=customer.name,
            national_id=customer.national_id,
            phone=customer.phone,
            issue_date=issue_d,
            delivery_date=issue_d + timedelta(days=7),
            translator=translator.display_name,
            total_items=random.randint(1, 8),
            total_amount=total_amount,
            final_amount=total_amount,
            total_translation_price=int(total_amount * 0.8),
            payment_status=1 if random.random() > 0.15 else 0,
            delivery_status=4,
            total_judiciary_count=random.randint(0, 2),
            total_foreign_affairs_count=random.randint(0, 1),
            username=clerk.username
        ))

    # --- B) Targeted data for Dashboard ---
    print("Injecting targeted data for dashboard widgets...")

    # Fallbacks to prevent crashes if specific users are not found
    top_translator = next((t for t in translators if 'رضایی' in t.display_name), translators[0])
    second_translator = next((t for t in translators if 'حسینی' in t.display_name), translators[1])
    top_clerk = next((c for c in clerks if 'کارمند' in c.display_name), clerks[0])

    # Invoices for Top Performers this month
    for i in range(4):
        issue_d = today_j.replace(day=random.randint(1, today_j.day)).togregorian()
        invoices.append(IssuedInvoiceModel(
            invoice_number=1403200 + i,
            name=random.choice(all_customers).name,
            national_id=random.choice(all_customers).national_id,
            phone='09123456789',
            issue_date=issue_d,
            delivery_date=issue_d + timedelta(days=5),
            translator=top_translator.display_name,
            username=top_clerk.username,
            total_items=random.randint(3, 15),  # High document count
            total_amount=1500000,
            final_amount=1500000,
            total_translation_price=1200000,
            payment_status=1,
            delivery_status=1
        ))

    # --- Action Queue Data ---
    invoices.append(IssuedInvoiceModel(
        invoice_number=1403301,
        name=random.choice(all_customers).name,
        national_id=random.choice(all_customers).national_id,
        phone='09123456789',
        issue_date=today - timedelta(days=4),
        delivery_date=today - timedelta(days=1),
        translator=second_translator.display_name,
        total_amount=950000,
        final_amount=950000,
        total_translation_price=800000,
        payment_status=1,
        delivery_status=2,
        total_items=5,
        username=top_clerk.username  # Overdue
    ))

    invoices.append(IssuedInvoiceModel(
        invoice_number=1403302,
        name=random.choice(all_customers).name,
        national_id=random.choice(all_customers).national_id,
        phone='09121234567',
        issue_date=today - timedelta(days=3),
        delivery_date=today,
        translator=top_translator.display_name,
        total_amount=2100000,
        final_amount=2100000,
        total_translation_price=1800000,
        payment_status=0,
        delivery_status=3,
        total_items=12,
        username=top_clerk.username  # Due today, unpaid
    ))

    # --- Commit to DB ---
    invoices_session.add_all(invoices)
    invoices_session.commit()
    print("✅ Invoices.db successfully populated.")
