# -*- coding: utf-8 -*-
"""
Database Utilities - Diagnose and manage database table creation issues
"""
import os
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.orm import sessionmaker
import io
import re

try:
    from shared.entities.common_sqlalchemy_bases import *
    print("Successfully imported Base, CustomerModel, CompanionModel")
except ImportError as e:
    print(f"Import error: {e}")
    Base = None
    CustomerModel = None
    CompanionModel = None

from shared import return_resource

customers_database = return_resource('databases', 'customers.db')


def diagnose_imported_models():
    """Diagnose what models are being imported and registered with Base."""
    print("=== Model Import Diagnosis ===")

    if Base is None:
        print("ERROR: Base is None - check imports")
        return

    print(f"Base class: {Base}")
    print(f"Base registry: {Base.registry}")

    # Check what tables are registered with Base
    print("\nTables registered with Base:")
    for table_name, table in Base.metadata.tables.items():
        print(f"  - {table_name}: {table}")
        print(f"    Columns: {[col.name for col in table.columns]}")

    print(f"\nTotal tables in Base.metadata: {len(Base.metadata.tables)}")

    # Check what classes are mapped
    print("\nMapped classes:")
    try:
        for mapper in Base.registry.mappers:
            print(f"  - {mapper.class_.__name__} -> {mapper.local_table.name}")
    except Exception as e:
        print(f"Error getting mappers: {e}")


def diagnose_database_file():
    """Diagnose the actual database file."""
    print("=== Database File Diagnosis ===")

    if os.path.exists(customers_database):
        print(f"Database file exists: {customers_database}")
        print(f"File size: {os.path.getsize(customers_database)} bytes")
    else:
        print(f"Database file does not exist: {customers_database}")
        return

    try:
        engine = create_engine(f'sqlite:///{customers_database}', echo=False)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        print(f"Total tables: {len(tables)}")

        for table_name in tables:
            print(f"\nTable: {table_name}")
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)

            print(f"  Columns ({len(columns)}):")
            for col in columns:
                print(f"    - {col['name']}: {col['type']} {'(PK)' if col.get('primary_key') else ''}")

            print(f"  Indexes ({len(indexes)}):")
            for idx in indexes:
                print(f"    - {idx['name']}: {idx['column_names']}")

            print(f"  Foreign Keys ({len(foreign_keys)}):")
            for fk in foreign_keys:
                print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

    except Exception as e:
        print(f"Error inspecting database: {e}")


def clean_database():
    """Remove the database file to start fresh."""
    print("=== Cleaning Database ===")

    if os.path.exists(customers_database):
        try:
            os.remove(customers_database)
            print(f"Database file removed: {customers_database}")
        except Exception as e:
            print(f"Error removing database: {e}")
    else:
        print("Database file does not exist - nothing to clean")


def create_minimal_tables():
    """Create only the CustomerModel and CompanionModel tables."""
    print("=== Creating Minimal Tables ===")

    try:
        engine = create_engine(f'sqlite:///{customers_database}', echo=True)

        if CustomerModel is None or CompanionModel is None:
            print("ERROR: Models not imported correctly")
            return False

        # Method 1: Create individual tables
        print("Creating tables individually...")
        CustomerModel.__table__.create(engine, checkfirst=True)
        CompanionModel.__table__.create(engine, checkfirst=True)

        print("Tables created successfully")

        # Verify what was created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")

        return True

    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


def create_tables_with_metadata():
    """Create tables using specific metadata (alternative approach)."""
    print("=== Creating Tables with Custom Metadata ===")

    try:
        engine = create_engine(f'sqlite:///{customers_database}', echo=True)

        # Create new metadata with only our tables
        metadata = MetaData()

        # Reflect only our specific tables if they exist in the models
        if CustomerModel is not None:
            customer_table = CustomerModel.__table__.tometadata(metadata)
            print(f"Added customer table: {customer_table.name}")

        if CompanionModel is not None:
            companion_table = CompanionModel.__table__.tometadata(metadata)
            print(f"Added companion table: {companion_table.name}")

        # Create only these tables
        metadata.create_all(engine)

        print("Tables created with custom metadata")

        # Verify what was created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")

        return True

    except Exception as e:
        print(f"Error creating tables with metadata: {e}")
        return False


def create_tables_with_sql():
    """Create tables using raw SQL (last resort)."""
    print("=== Creating Tables with Raw SQL ===")

    try:
        engine = create_engine(f'sqlite:///{customers_database}', echo=True)

        # Raw SQL for customers table
        customer_sql = """
        CREATE TABLE IF NOT EXISTS customers (
            national_id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20) NOT NULL UNIQUE,
            telegram_id VARCHAR(50),
            email VARCHAR(255),
            address TEXT,
            passport_image VARCHAR(255)
        );
        """

        # Raw SQL for companions table
        companion_sql = """
        CREATE TABLE IF NOT EXISTS companions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_national_id VARCHAR(10),
            name VARCHAR(255) NOT NULL,
            national_id VARCHAR(10),
            phone VARCHAR(20),
            ui_number INTEGER,
            FOREIGN KEY (customer_national_id) REFERENCES customers(national_id) ON DELETE CASCADE
        );
        """

        with engine.connect() as conn:
            conn.execute(text(customer_sql))
            conn.execute(text(companion_sql))
            conn.commit()

        print("Tables created with raw SQL")

        # Verify what was created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Created tables: {tables}")

        return True

    except Exception as e:
        print(f"Error creating tables with SQL: {e}")
        return False


def find_problematic_models():
    """Try to identify what's causing extra tables to be created."""
    print("=== Finding Problematic Models ===")

    if Base is None:
        print("Base is None - cannot analyze")
        return

    # Check all imported modules for SQLAlchemy models
    import sys

    print("Checking imported modules...")
    for name, module in list(sys.modules.items()):
        if module is None:
            continue

        try:
            # Check if module has SQLAlchemy models
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (hasattr(attr, '__table__') and
                        hasattr(attr, '__tablename__') and
                        hasattr(attr, 'metadata')):
                    print(f"Found model {attr_name} in {name}: table '{attr.__tablename__}'")
        except Exception:
            continue


def main():
    """Main diagnosis and repair function."""
    print("Database Diagnosis and Repair Tool")
    print("=" * 50)

    # Step 1: Diagnose imports
    diagnose_imported_models()
    print("\n" + "=" * 50 + "\n")

    # Step 2: Check existing database
    diagnose_database_file()
    print("\n" + "=" * 50 + "\n")

    # Step 3: Find problematic models
    find_problematic_models()
    print("\n" + "=" * 50 + "\n")

    # Offer repair options
    print("Repair Options:")
    print("1. Clean database and create minimal tables")
    print("2. Create tables with custom metadata")
    print("3. Create tables with raw SQL")
    print("4. Just clean the database")
    print("5. Exit without changes")

    choice = input("\nEnter your choice (1-5): ").strip()

    if choice == "1":
        clean_database()
        create_minimal_tables()
    elif choice == "2":
        clean_database()
        create_tables_with_metadata()
    elif choice == "3":
        clean_database()
        create_tables_with_sql()
    elif choice == "4":
        clean_database()
    elif choice == "5":
        print("Exiting without changes")
    else:
        print("Invalid choice")

    print("\n" + "=" * 50)
    print("Final database state:")
    diagnose_database_file()


if __name__ == "__main__":
    main()
