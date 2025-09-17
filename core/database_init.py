from sqlalchemy import create_engine
from pathlib import Path
from shared.session_provider import SessionProvider
from config.config import DATABASE_BASES


class DatabaseInitializer:
    def setup_file_databases(self, absolute_paths: dict) -> SessionProvider:
        return self._initialize_databases(absolute_paths, is_memory=False)

    def setup_memory_databases(self) -> SessionProvider:
        memory_urls = {name: 'sqlite:///:memory:' for name in DATABASE_BASES.keys()}
        return self._initialize_databases(memory_urls, is_memory=True)

    def _initialize_databases(self, db_config: dict, is_memory: bool) -> SessionProvider:
        engines = {}  # This will store the created ENGINE OBJECTS

        for name, base in DATABASE_BASES.items():
            path_or_url = db_config.get(name)
            if not path_or_url:
                raise ValueError(f"Database config for '{name}' not found.")

            db_url = path_or_url if is_memory else f"sqlite:///{path_or_url}"

            if not is_memory:
                Path(path_or_url).parent.mkdir(parents=True, exist_ok=True)

            connect_args = {"check_same_thread": False} if is_memory else {}

            # Create the engine and STORE THE OBJECT in our dictionary
            engine = create_engine(db_url, connect_args=connect_args)
            engines[name] = engine

            base.metadata.create_all(engine)

        print("Database engines and schemas initialized successfully.")

        # --- THE FIX ---
        # Pass the dictionary of fully-formed ENGINE OBJECTS to the provider.
        return SessionProvider(engines)
