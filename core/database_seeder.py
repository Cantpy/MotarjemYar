# core/database_seeder.py

import bcrypt
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from shared.orm_models.users_models import UsersModel, UserProfileModel
from shared.orm_models.services_models import FixedPricesModel


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
        print("Data seeding complete.")

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
