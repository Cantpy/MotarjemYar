# shared/testing/launch_feature.py

import sys
from pathlib import Path
from typing import Type, Dict
from PySide6.QtWidgets import QApplication, QWidget
from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder
from config.config import DATABASE_PATHS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))


def launch_feature_for_ui_test(factory_class: Type,
                               required_engines: Dict[str, str],
                               use_memory_db: bool = True,
                               parent: QWidget = None):
    """
    A generic helper to initialize dependencies and launch a single feature
    for visual inspection or manual UI testing.

    Args:
        factory_class: The Factory class to test (e.g., CustomerInfoFactory).
        required_engines: A dictionary mapping the required database name
                          to the factory's keyword argument name.
                          Example: {'customers': 'customer_engine'}
        use_memory_db: If True, uses fast in-memory databases.
        parent: An optional parent widget for the feature's view.
    """
    app = QApplication.instance() or QApplication(sys.argv)

    print(f"--- Launching Test for: {factory_class.__name__} ---")

    # 1. Initialize databases
    initializer = DatabaseInitializer()
    if use_memory_db:
        print("Using IN-MEMORY databases for test.")
        all_engines = initializer.setup_memory_databases()
    else:
        print("Using FILE-BASED databases for test.")
        # The placeholder is now correctly filled
        all_engines = initializer.setup_file_databases(DATABASE_PATHS)

    # 2. Seed data
    seeder = DatabaseSeeder(engines=all_engines)
    seeder.seed_initial_data()

    # 3. Prepare the specific engines with the CORRECT argument names
    factory_kwargs = {}
    for db_name, arg_name in required_engines.items():
        engine = all_engines.get(db_name)
        if not engine:
            raise RuntimeError(f"Required engine '{db_name}' was not found.")
        factory_kwargs[arg_name] = engine

    # 4. Call the factory with the correctly named keyword arguments and parent
    print(f"Creating controller with arguments: {list(factory_kwargs.keys())}")
    controller = factory_class.create(**factory_kwargs, parent=parent)

    # 5. Get the view and run the application
    main_widget = controller.get_view()
    main_widget.show()

    sys.exit(app.exec())
