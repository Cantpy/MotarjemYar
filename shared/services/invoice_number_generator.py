# shared/services/invoice_number_generator.py

import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from shared.session_provider import ManagedSessionProvider

logger = logging.getLogger(__name__)


class InvoiceNumberService:
    """
    Generates unique sequential invoice numbers using a database-side counter.
    Works with both SQLite and PostgreSQL.
    """
    SEQUENCE_NAME = 'invoice_number_seq'

    def __init__(self, invoices_engine):
        self._engine = invoices_engine
        self._is_sequence_initialized = False

    def _initialize_sequence(self):
        """Ensure a persistent counter exists across issued and deleted invoices."""
        if self._is_sequence_initialized:
            return

        with self._engine() as session:
            try:
                dialect = session.bind.dialect.name
                logger.debug(f"Initializing invoice number sequence for dialect: {dialect}")

                # --- Dialect-specific check ---
                if dialect == "postgresql":
                    check_seq_sql = text(f"SELECT to_regclass('{self.SEQUENCE_NAME}')")
                    result = session.execute(check_seq_sql).scalar()
                    seq_exists = result is not None

                elif dialect == "sqlite":
                    check_seq_sql = text(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.SEQUENCE_NAME}'"
                    )
                    result = session.execute(check_seq_sql).scalar()
                    seq_exists = result is not None

                else:
                    raise NotImplementedError(f"Unsupported dialect: {dialect}")

                if seq_exists:
                    self._is_sequence_initialized = True
                    return

                # --- Compute starting value ---
                get_max_id_sql = text("""
                    SELECT MAX(CAST(SUBSTR(invoice_number, 5) AS INTEGER))
                    FROM (
                        SELECT invoice_number FROM issued_invoices
                        UNION ALL
                        SELECT invoice_number FROM deleted_invoices
                    ) AS all_invoices;
                """)
                max_id = session.execute(get_max_id_sql).scalar() or 0
                start_value = max_id + 1

                # --- Create sequence/counter table ---
                if dialect == "postgresql":
                    session.execute(text(f"CREATE SEQUENCE {self.SEQUENCE_NAME} START {start_value}"))
                elif dialect == "sqlite":
                    session.execute(text(f"""
                        CREATE TABLE {self.SEQUENCE_NAME} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            dummy INTEGER
                        )
                    """))
                    # Pre-insert rows to set the counter
                    if start_value > 1:
                        for _ in range(start_value - 1):
                            session.execute(text(f"INSERT INTO {self.SEQUENCE_NAME} (dummy) VALUES (0)"))

                session.commit()
                self._is_sequence_initialized = True
                logger.info(f"Initialized invoice number counter starting at {start_value}.")

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to initialize invoice number sequence: {e}")
                raise

    def get_next_invoice_number(self) -> str:
        """Return next formatted invoice number (INV-XXXX)."""
        self._initialize_sequence()

        with self._engine() as session:
            dialect = session.bind.dialect.name

            if dialect == "postgresql":
                next_val_sql = text(f"SELECT nextval('{self.SEQUENCE_NAME}')")
                next_id = session.execute(next_val_sql).scalar()

            elif dialect == "sqlite":
                # Insert a dummy row to get autoincremented id
                session.execute(text(f"INSERT INTO {self.SEQUENCE_NAME} (dummy) VALUES (0)"))
                next_id = session.execute(
                    text(f"SELECT MAX(id) FROM {self.SEQUENCE_NAME}")
                ).scalar()

            else:
                raise NotImplementedError(f"Unsupported dialect: {dialect}")

            session.commit()
            return f"INV-{next_id:04d}"

