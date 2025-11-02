# core/database_init.py

from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from pathlib import Path
from config.config import DATABASE_BASES, DATABASE_PATHS


class DatabaseInitializer:
    """
    Initializes all application databases and returns a dictionary of Engine objects.
    Supports both file-based databases for production/development and
    in-memory databases for fast, isolated testing.
    """

    def setup_file_databases(self, absolute_paths: dict) -> dict[str, Engine]:
        """
        Creates SQLite database files, initializes schemas, and returns a
        dictionary of configured SQLAlchemy Engine objects.
        """
        # Create the dictionary of database URLs from the file paths
        db_urls = {name: f"sqlite:///{path}" for name, path in absolute_paths.items()}

        # Ensure parent directories exist for all file-based databases
        for path in absolute_paths.values():
            Path(path).parent.mkdir(parents=True, exist_ok=True)

        return self._initialize_engines(db_urls)

    def setup_memory_databases(self) -> dict[str, Engine]:
        """
        Creates in-memory SQLite databases and returns a dictionary of
        configured SQLAlchemy Engine objects. Ideal for testing.
        """
        # Create a dictionary of in-memory database URLs
        memory_urls = {name: 'sqlite:///:memory:' for name in DATABASE_BASES.keys()}
        return self._initialize_engines(memory_urls, connect_args={"check_same_thread": False})

    def _initialize_engines(self, db_urls: dict, connect_args: dict = None) -> dict[str, Engine]:
        """
        Private helper that takes database URLs and creates all engines and schemas.
        """
        engines: dict[str, Engine] = {}
        connect_args = connect_args or {}

        for name, url in db_urls.items():
            if not url:
                raise ValueError(f"Database URL for '{name}' not found.")

            # Create the SQLAlchemy engine for this specific database
            engine = create_engine(url, connect_args=connect_args)
            engines[name] = engine

            # Look up the correct SQLAlchemy Base and create tables
            base = DATABASE_BASES.get(name)
            if base:
                base.metadata.create_all(engine)
            else:
                print(f"Warning: No SQLAlchemy Base found for database '{name}'. Schema not created.")

        print(f"{len(engines)} database engines initialized successfully.")
        return engines
