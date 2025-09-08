import bcrypt
from shared.session_provider import SessionProvider
from shared.orm_models.users_models import UsersModel, UserProfileModel


class DatabaseSeeder:
    """
    Responsible for populating the databases with initial or default data.
    """

    def __init__(self, session_provider: SessionProvider):
        self.session_provider = session_provider

    def seed_initial_data(self):
        """
        Public method to run all data seeding operations.
        """
        print("Seeding initial application data...")
        self._seed_default_user()
        # You could add other seeding methods here in the future,
        # e.g., self._seed_default_services()
        print("Data seeding complete.")

    def _seed_default_user(self):
        """Creates a default 'testuser' for development and testing."""
        # Use the session provider to get the correct session
        session = self.session_provider.users()
        try:
            # Check if the user already exists
            user_exists = session.query(UsersModel).filter_by(username="testuser").first()
            if not user_exists:
                # Best practice: Don't hardcode passwords.
                # In a real app, this would come from a config file or environment variable.
                password = "password123"
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                new_user = UsersModel(username="testuser", password_hash=hashed_password, role="translator", active=1)
                session.add(new_user)
                session.flush()  # Flush to get the new_user.id before commit

                new_profile = UserProfileModel(
                    user_id=new_user.id,
                    full_name="کاربر آزمایشی",
                    role_fa="مترجم"
                )
                session.add(new_profile)
                session.commit()
                print("Default user 'testuser' created.")
        except Exception as e:
            print(f"Error seeding default user: {e}")
            session.rollback()
        finally:
            session.close()
