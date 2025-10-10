# shared/_session_provider.py

from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Optional

from features.Login.auth_file_repo import AuthFileRepository
from shared.dtos.auth_dtos import SessionDataDTO


class SessionProvider:
    """
    A 'dumb' dependency container that holds pre-configured database engines
    and provides session makers on demand.
    """

    def __init__(self, engines: dict[str, Engine]):
        """
        Initializes the provider with a dictionary of fully-created
        SQLAlchemy Engine objects.
        """
        self._engines = engines

        # Create a session maker for each engine
        self.invoices = self._create_session_maker('invoices')
        self.customers = self._create_session_maker('customers')
        self.services = self._create_session_maker('services')
        self.payroll = self._create_session_maker('payroll')
        self.users = self._create_session_maker('users')
        self.expenses = self._create_session_maker('expenses')
        self.info_page = self._create_session_maker('info_page')
        self.workspace = self._create_session_maker('workspace')

    def _create_session_maker(self, name: str) -> sessionmaker:
        """Helper to create a session maker from a stored engine."""
        engine = self._engines.get(name)  # This will now be a REAL Engine object
        if not engine:
            raise ValueError(f"Engine '{name}' was not provided during initialization.")

        return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ManagedSessionProvider:
    """
    A provider that offers a managed, transactional session scope.
    This is the recommended provider for all business logic.
    """
    def __init__(self, engine: Engine):
        """
        Initializes the provider with a single, specific engine.
        """
        # Create a single session factory for this specific database
        self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @contextmanager
    def __call__(self) -> Session:
        """
        Provides a transactional scope via a services manager.
        Automatically handles commit, rollback, and closing.
        Usage:
            with _session_provider() as session:
                _repo.do_work(session)
        """
        session = self._session_factory()
        print("[DEBUG] Managed session opened.")
        try:
            yield session
            # If the 'with' block completes without errors, we commit.
            session.commit()
            print("[DEBUG] Managed session committed successfully.")
        except Exception:
            # If any error occurs, we roll back.
            print("[DEBUG] An error occurred. Rolling back session.")
            session.rollback()
            raise # Re-raise the exception to notify the caller
        finally:
            # Always close the session.
            print("[DEBUG] Managed session closed.")
            session.close()


class SessionManager:
    """
    Singleton-style manager to access the current session from anywhere.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._auth_repo = AuthFileRepository()
            cls._instance._session_data = None
        return cls._instance

    def get_session(self) -> Optional[SessionDataDTO]:
        """
        Loads the current session data if not cached.
        """
        if self._session_data is None:
            self._session_data = self._auth_repo.load_session()
        return self._session_data

    def refresh(self) -> None:
        """
        Reloads the session data from disk (useful after login).
        """
        self._session_data = self._auth_repo.load_session()

    def clear(self) -> None:
        """
        Clears the cached session (useful after logout).
        """
        self._session_data = None
