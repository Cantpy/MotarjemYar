# shared/testing/conftest.py

import pytest
from collections import namedtuple
from sqlalchemy import Engine

from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder

TestAppContext = namedtuple('TestAppContext', ['qtbot', 'engines'])


@pytest.fixture(scope="function")
def app_context(qtbot):
    """
    A pytest fixture that provides a fully initialized application context
    for an integration test. It uses a fresh in-memory database for each test.

    Yields:
        TestAppContext: An object containing the qtbot and a dict of all engines.
    """
    # 1. Initialize in-memory databases
    initializer = DatabaseInitializer()
    all_engines = initializer.setup_memory_databases()

    # 2. Seed data
    seeder = DatabaseSeeder(engines=all_engines)
    seeder.seed_initial_data()

    # 3. Yield the context to the test function
    yield TestAppContext(qtbot=qtbot, engines=all_engines)

    # 4. Teardown (if any) happens here automatically after the test finishes.
    # For in-memory DBs, nothing is needed.
