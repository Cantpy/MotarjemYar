# repo.py

import os
from sqlalchemy import (create_engine, Column, Integer, Text, Date, Float, ForeignKey, Index,
                        CheckConstraint, LargeBinary, Boolean, DateTime, func)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from shared import return_resource
from shared.models.sqlalchemy_models import (IssuedInvoiceModel, InvoiceItemModel, ServicesModel, OtherServicesModel,
                                             UsersModel, UserProfileModel, CustomerModel, CompanionModel,
                                             FixedPricesModel, LoginLogsModel, TranslationOfficeDataModl, Base)

# --- Database Setup ---
# In a real application, these paths would come from a config file.
DB_DIR = "databases"
os.makedirs(DB_DIR, exist_ok=True)

CUSTOMERS_DB_URL = f"sqlite:///{return_resource('databases', 'customers.db')}"
INVOICES_DB_URL = f"sqlite:///{return_resource('databases', 'invoices.db')}"
SERVICES_DB_URL = f"sqlite:///{return_resource('databases', 'services.db')}"
USERS_DB_URL = f"sqlite:///{return_resource('databases', 'users.db')}"

# Create engines for each database
customers_engine = create_engine(CUSTOMERS_DB_URL)
invoices_engine = create_engine(INVOICES_DB_URL)
services_engine = create_engine(SERVICES_DB_URL)
users_engine = create_engine(USERS_DB_URL)

# Session makers
CustomersSession = sessionmaker(bind=customers_engine)
InvoicesSession = sessionmaker(bind=invoices_engine)
ServicesSession = sessionmaker(bind=services_engine)
UsersSession = sessionmaker(bind=users_engine)


# --- Repository for Data Export ---
class InvoiceRepository:
    """Handles database operations for exporting invoice data."""

    def __init__(self):
        # Create tables if they don't exist
        Base.metadata.create_all(invoices_engine)
        Base.metadata.create_all(customers_engine)
        Base.metadata.create_all(users_engine)

    def export_to_excel(self, username: str, file_path: str) -> bool:
        """Exports all invoices for a given user to an Excel file."""
        session = InvoicesSession()
        try:
            query = session.query(IssuedInvoiceModel).filter(IssuedInvoiceModel.username == username)
            df = pd.read_sql(query.statement, session.bind)
            if df.empty:
                return False
            df.to_excel(file_path, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
        finally:
            session.close()
