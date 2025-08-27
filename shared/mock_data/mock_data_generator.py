# shared/mock_data/mock_data_generator.py

import random
from datetime import date, timedelta, datetime
from faker import Faker
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta

# Import all necessary models from your project
from shared.database_models.invoices_models import IssuedInvoiceModel, InvoiceItemModel
from shared.database_models.customer_models import CustomerModel, CompanionModel
from shared.database_models.services_models import ServicesModel, FixedPricesModel
from shared.database_models.expenses_models import ExpenseModel
from shared.database_models.payroll_models import LaborLawConstantsModel, EmployeePayrollProfileModel
from shared.database_models.user_models import UsersModel, LoginLogsModel, UserProfileModel
import jdatetime  # For Jalali date handling

# Use Persian locale for realistic names
fake = Faker('fa_IR')


def create_mock_data(
        invoices_session: Session,
        customers_session: Session,
        services_session: Session,
        expenses_session: Session,
        users_session: Session,
        payroll_session: Session
):
    """
    Populates all databases with a complete and interconnected set of mock data.
    """
    today = date.today()
    today_j = jdatetime.date.today()

    # --- 1. Populate Users and Login Logs ---
    if not users_session.query(UsersModel).first():
        print("Populating Users.db with mock users, profiles, and logs...")
        placeholder_hash = b'$2b$12$...placeholder...'  # Placeholder hash

        # --- FIX 1 & 2: Create users with their corresponding profiles ---
        admin_user = UsersModel(username='admin', password_hash=placeholder_hash, role='admin')
        clerk_user = UsersModel(username='clerk1', password_hash=placeholder_hash, role='clerk')
        # --- FIX 3: Create users for our mock translators ---
        translator1_user = UsersModel(username='rezaei', password_hash=placeholder_hash, role='translator')
        translator2_user = UsersModel(username='hosseini', password_hash=placeholder_hash, role='translator')
        translator3_user = UsersModel(username='mahmoudi', password_hash=placeholder_hash, role='translator')

        users_to_add = [admin_user, clerk_user, translator1_user, translator2_user, translator3_user]
        users_session.add_all(users_to_add)
        users_session.commit()  # Commit to get user IDs

        # Create profiles and link them
        profiles_to_add = [
            UserProfileModel(user_id=admin_user.id, full_name="مدیر سیستم", role_fa="مدیر"),
            UserProfileModel(user_id=clerk_user.id, full_name="کارمند پذیرش", role_fa="کارمند"),
            UserProfileModel(user_id=translator1_user.id, full_name="آقای رضایی", role_fa="مترجم"),
            UserProfileModel(user_id=translator2_user.id, full_name="خانم حسینی", role_fa="مترجم"),
            UserProfileModel(user_id=translator3_user.id, full_name="علی محمودی", role_fa="مترجم")
        ]
        users_session.add_all(profiles_to_add)

        # Create Login Logs
        login_logs = []
        for i in range(25):
            user = random.choice(users_to_add)
            login_time = datetime.now() - timedelta(hours=random.randint(1, 72))
            log = LoginLogsModel(user_id=user.id, login_time=login_time.strftime('%Y-%m-%d %H:%M:%S'),
                                 status=random.choice(['success', 'failed']))
            login_logs.append(log)
        users_session.add_all(login_logs)
        users_session.commit()

    # --- 2. Populate Services and Fixed Prices ---
    if not services_session.query(ServicesModel).first():
        print("Populating Services.db with mock services...")
        service_names = ["ترجمه شناسنامه", "ترجمه کارت ملی", "ترجمه سند ازدواج", "ترجمه مدرک تحصیلی", "ترجمه گواهینامه",
                         "ترجمه سند ملکی"]
        services = [ServicesModel(name=name) for name in service_names]
        services_session.add_all(services)

        # Crucial for report calculations
        seal_prices = [
            FixedPricesModel(name="مهر دادگستری", price=80000, is_default=True, label_name='judiciary_seal'),
            FixedPricesModel(name="مهر وزارت امور خارجه", price=150000, is_default=True,
                             label_name='foreign_affairs_seal')
        ]
        services_session.add_all(seal_prices)
        services_session.commit()

    # --- 3. Populate Customers ---
    customers = customers_session.query(CustomerModel).all()
    if not customers:
        print("Populating Customers.db with mock customers...")
        customers = []
        for _ in range(50):
            customer = CustomerModel(
                name=fake.name(),
                national_id=fake.unique.random_number(digits=10, fix_len=True),
                phone=fake.phone_number()
            )
            customers.append(customer)
        customers_session.add_all(customers)
        customers_session.commit()

        # Add some companions
        companions = [CompanionModel(name=fake.name(), national_id=fake.unique.random_number(digits=10, fix_len=True),
                                     customer_national_id=customers[i].national_id) for i in range(10)]
        customers_session.add_all(companions)
        customers_session.commit()

    # --- 4. Populate Expenses ---
    if not expenses_session.query(ExpenseModel).first():
        print("Populating Expenses.db with mock monthly expenses...")
        expenses = []
        for i in range(36):  # 3 years of expenses
            current_month = today - relativedelta(months=i)
            expenses.append(
                ExpenseModel(name="اجاره دفتر", amount=random.randint(15, 25) * 1000000, expense_date=current_month,
                             category="Rent"))
            expenses.append(
                ExpenseModel(name="حقوق کارمند", amount=random.randint(8, 12) * 1000000, expense_date=current_month,
                             category="Salary"))
            expenses.append(
                ExpenseModel(name="هزینه های جاری", amount=random.randint(2, 5) * 1000000, expense_date=current_month,
                             category="Utilities"))
        expenses_session.add_all(expenses)
        expenses_session.commit()

    # --- 5. Populate Invoices with Historical and Targeted Data ---
    if not invoices_session.query(IssuedInvoiceModel).first():
        print("Populating Invoices.db with mock invoices...")
        invoices = []
        customers = customers_session.query(CustomerModel).all()
        if not customers:
            print("Cannot create invoices without customers. Please run mock data for customers first.")
            return

        # A) Historical data for reports (last 3 years)
        for i in range(300):
            customer = random.choice(customers)
            issue_d = today - relativedelta(months=random.randint(1, 35), days=random.randint(0, 28))
            total_amount = random.randint(800000, 5000000)

            invoices.append(IssuedInvoiceModel(
                invoice_number=1400000 + i,
                name=customer.name,
                national_id=customer.national_id,
                phone=customer.phone,
                issue_date=issue_d,
                delivery_date=issue_d + timedelta(days=7),
                translator=random.choice(["علی رضایی", "مریم حسینی", "علی محمودی"]),
                total_items=random.randint(1, 4),
                total_amount=total_amount,
                final_amount=total_amount,
                total_translation_price=int(total_amount * 0.8),
                payment_status=1 if random.random() > 0.15 else 0,
                delivery_status=4,
                total_judiciary_count=random.randint(0, 2),
                total_foreign_affairs_count=random.randint(0, 1),
                username=random.choice(['clerk1', 'admin'])
            ))

        # --- B) NEW: Targeted data for This Month's Top Performers ---
        print("Injecting targeted data for dashboard top performers...")

        # Define our star performers
        top_translator = "آقای رضایی"
        second_translator = "خانم حسینی"
        other_translator = "علی محمودی"
        top_clerk = "clerk1"
        second_clerk = "admin"

        # Scenario 1: Give the top translator several high-document invoices this month
        for i in range(4):
            customer = random.choice(customers)
            # Ensure the date is within the current Jalali month
            issue_d = today_j.replace(day=random.randint(1, today_j.day)).togregorian()
            invoices.append(IssuedInvoiceModel(
                invoice_number=1403200 + i, name=customer.name, national_id=customer.national_id,
                phone=customer.phone,
                issue_date=issue_d, delivery_date=issue_d + timedelta(days=5),
                translator=top_translator,
                username=top_clerk,  # Created by the top clerk
                total_items=random.randint(3, 5),  # High document count
                total_amount=random.randint(1500000, 4000000), final_amount=random.randint(1500000, 4000000),
                total_translation_price=random.randint(1200000, 3800000),
                payment_status=1, delivery_status=1
            ))

        # Scenario 2: Give the second translator a couple of invoices
        for i in range(2):
            customer = random.choice(customers)
            issue_d = today_j.replace(day=random.randint(1, today_j.day)).togregorian()
            invoices.append(IssuedInvoiceModel(
                invoice_number=1403210 + i, name=customer.name, national_id=customer.national_id,
                phone=customer.phone,
                issue_date=issue_d, delivery_date=issue_d + timedelta(days=6),
                translator=second_translator,
                username=second_clerk,  # Created by the second clerk
                total_items=random.randint(1, 3),  # Lower document count
                total_amount=random.randint(800000, 2000000), final_amount=random.randint(800000, 2000000),
                total_translation_price=random.randint(600000, 1800000),
                payment_status=1, delivery_status=1
            ))

        # Scenario 3: Give another translator one small invoice
        customer = random.choice(customers)
        issue_d = today_j.replace(day=random.randint(1, today_j.day)).togregorian()
        invoices.append(IssuedInvoiceModel(
            invoice_number=1403220, name=customer.name, national_id=customer.national_id, phone=customer.phone,
            issue_date=issue_d, delivery_date=issue_d + timedelta(days=4),
            translator=other_translator,
            username=top_clerk,  # Also created by the top clerk to boost their count
            total_items=1,
            total_amount=900000, final_amount=900000, total_translation_price=750000,
            payment_status=0, delivery_status=0
        ))

        invoices_session.add_all(invoices)
        invoices_session.commit()

    # --- 6. Populate Payroll.db with mock data ---
    if not payroll_session.query(LaborLawConstantsModel).first():
        print("Populating Payroll.db with 1404 constants...")
        constants_1404 = [
            LaborLawConstantsModel(year=1404, name='base_salary', value=71661840),
            LaborLawConstantsModel(year=1404, name='housing_allowance', value=9000000),
            LaborLawConstantsModel(year=1404, name='groceries_allowance', value=14000000),
            LaborLawConstantsModel(year=1404, name='children_allowance_per_child', value=7166184),
            LaborLawConstantsModel(year=1404, name='overtime_rate_multiplier', value=1.4),
            LaborLawConstantsModel(year=1404, name='social_security_employee_rate', value=0.07,
                                   type='Deduction_Rate'),
            LaborLawConstantsModel(year=1404, name='estimated_tax_rate', value=0.10, type='Deduction_Rate'),
        ]
        payroll_session.add_all(constants_1404)

        # Link payroll profiles to existing users
        all_users = users_session.query(UsersModel).all()
        for user in all_users:
            if user.username == 'admin':
                payroll_session.add(
                    EmployeePayrollProfileModel(user_id=user.id, payment_type='Fixed', custom_base_salary=80000000))
            elif user.username == 'clerk1':
                payroll_session.add(
                    EmployeePayrollProfileModel(user_id=user.id, payment_type='Fixed', custom_base_salary=50000000))
            elif user.username == 'rezaei':  # Linked to translator user
                payroll_session.add(
                    EmployeePayrollProfileModel(user_id=user.id, payment_type='Commission', commission_rate=0.25))
            elif user.username == 'hosseini':
                payroll_session.add(
                    EmployeePayrollProfileModel(user_id=user.id, payment_type='Commission', commission_rate=0.30))
            elif user.username == 'mahmoudi':
                payroll_session.add(
                    EmployeePayrollProfileModel(user_id=user.id, payment_type='Commission', commission_rate=0.20))

        payroll_session.commit()

    print("Mock data generation check complete.")
