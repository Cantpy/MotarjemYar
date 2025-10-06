# core/database_seeder.py

import bcrypt
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from shared.orm_models.users_models import UsersModel, UserProfileModel
from shared.orm_models.services_models import FixedPricesModel, ServicesModel

from features.Services.tab_manager.tab_manager_logic import ExcelImportLogic
from features.Services.documents.documents_logic import ServicesLogic
from features.Services.documents.documents_repo import ServiceRepository
from features.Services.other_services.other_services_logic import OtherServicesLogic
from features.Services.other_services.other_services_repo import OtherServicesRepository

from shared import get_resource_path
from shared.session_provider import ManagedSessionProvider


class DatabaseSeeder:
    """
    Responsible for populating the databases with initial or default data.
    """
    def __init__(self, engines: dict[str, Engine]):
        self.engines = engines

    def seed_initial_data(self, is_demo_mode: bool = False):
        print("Seeding initial application data...")
        if is_demo_mode:
            self._seed_default_user()
        self._seed_fixed_prices()
        self._seed_services_from_excel()
        print("Data seeding complete.")

    def _seed_services_from_excel(self):
        """
        Seeds the services database from a predefined Excel file.
        This process is idempotent and will not run if data already exists.
        """
        print("Checking if services seeding is required...")
        services_engine = self.engines.get('services')
        if not services_engine:
            print("Warning: 'services' engine not found. Skipping Excel seeding.")
            return

        managed_services_engine = ManagedSessionProvider(services_engine)
        Session = sessionmaker(bind=services_engine)
        session = Session()

        try:
            # 1. Idempotency Check: Don't seed if data already exists
            service_count = session.query(ServicesModel).count()
            if service_count > 0:
                print("Services table already populated. Skipping seeding from Excel.")
                return

            # 2. Locate the Excel file
            # This path assumes the 'core' directory is one level down from the project root
            excel_path = get_resource_path("assets", "services_datasheet.xlsx")
            if not excel_path.exists():
                print(f"Warning: Initial services file not found at '{excel_path}'. Skipping.")
                return

            print(f"Seeding services from '{excel_path}'...")

            # 3. Instantiate the dependency chain
            services_repo = ServiceRepository()
            other_services_repo = OtherServicesRepository()

            # Your logic classes need a session factory, so we pass the Session class
            services_logic = ServicesLogic(repo=services_repo, services_engine=managed_services_engine)
            other_services_logic = OtherServicesLogic(repository=other_services_repo,
                                                      services_engine=managed_services_engine)

            importer = ExcelImportLogic(services_logic, other_services_logic)

            # 4. Run the import
            results = importer.import_from_excel_file(str(excel_path))

            # 5. Log the results
            for sheet, result in results.items():
                if result.failed_count > 0:
                    print(f"  - WARNING on sheet '{sheet}': {result.failed_count} rows failed to import.")
                    for error in result.errors:
                        print(f"    - ERROR: {error}")
                else:
                    print(f"  - Sheet '{sheet}': {result.success_count} services successfully seeded.")

        except Exception as e:
            print(f"FATAL: An error occurred during service seeding from Excel: {e}")
        finally:
            session.close()

    def _seed_fixed_prices(self):
        """Seeds fixed prices into the appropriate database."""
        services_engine = self.engines.get('services')
        if not services_engine:
            print("Warning: 'services' engine not found. Skipping fixed prices seeding.")
            return

        Session = sessionmaker(bind=services_engine)
        session = Session()

        fixed_prices = [
            {"name": "کپی برابر اصل", "price": 5000},
            {"name": "ثبت در سامانه", "price": 30000},
            {"name": "مهر دادگستری", "price": 150000},
            {"name": "مهر امور خارجه", "price": 15000},
            {"name": "نسخه اضافی", "price": 12000},
        ]

        try:
            existing_names = {fp.name for fp in session.query(FixedPricesModel.name).all()}
            added = 0

            for fp in fixed_prices:
                if fp["name"] not in existing_names:
                    new_price = FixedPricesModel(name=fp["name"], price=fp["price"])
                    session.add(new_price)
                    added += 1

            if added > 0:
                session.commit()
                print(f"{added} fixed prices added successfully.")
            else:
                print("No new fixed prices to add (already seeded).")

        except Exception as e:
            print(f"Error seeding fixed prices: {e}")
            session.rollback()
        finally:
            session.close()

    def _seed_default_user(self):
        """Creates a default 'testuser' for development and testing in demo mode."""
        print("Demo mode enabled: Seeding 'testuser'...")
        users_engine = self.engines.get('users')
        if not users_engine:
            print("Warning: 'users' engine not found. Skipping user seeding.")
            return

        Session = sessionmaker(bind=users_engine)
        session = Session()

        try:
            user_exists = session.query(UsersModel).filter_by(username="testuser").first()
            if not user_exists:
                password = "password123"
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                new_user = UsersModel(username="testuser", password_hash=hashed_password, role="translator", active=1)
                session.add(new_user)
                session.flush()

                new_profile = UserProfileModel(user_id=new_user.id, full_name="کاربر آزمایشی", role_fa="مترجم")
                session.add(new_profile)
                session.commit()
                print("Default user 'testuser' created.")
        except Exception as e:
            print(f"Error seeding default user: {e}")
            session.rollback()
        finally:
            session.close()
