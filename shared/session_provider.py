from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine


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
