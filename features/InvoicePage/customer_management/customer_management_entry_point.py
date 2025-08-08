#!/usr/bin/env python3
"""
Customer Management System - Main Entry Point

This module provides the main entry point for the customer management system.
It sets up the database connection, initializes the repository, logic, and controller,
and launches the customer management dialog.

Usage:
    python main.py

Requirements:
    - PySide6
    - SQLAlchemy
    - A configured database with the appropriate tables
"""

import sys
import os
from pathlib import Path
from typing import Tuple

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import our modules
from features.InvoicePage.customer_management.customer_management_repo import CustomerRepository
from features.InvoicePage.customer_management.customer_management_logic import CustomerLogic
from features.InvoicePage.customer_management.customer_management_controller import CustomerManagementController

from shared import return_resource

customers_database = return_resource('databases', 'customers.db')
invoices_database = return_resource('databases', 'invoices.db')


def setup_databases() -> Tuple[sessionmaker, sessionmaker]:
    """
    Setup connections for two separate databases: customers.db and invoices.db.

    Returns:
        Tuple[sessionmaker, sessionmaker]: Session factories for each database.
    """
    # Default database URL - modify this according to your setup
    # Examples:
    # SQLite: 'sqlite:///customers.db'
    # PostgreSQL: 'postgresql://user:password@localhost/dbname'
    # MySQL: 'mysql+pymysql://user:password@localhost/dbname'

    # Define your two SQLite database paths
    customers_database_url = os.getenv("CUSTOMERS_DATABASE_URL", f"sqlite:///{customers_database}")
    invoices_database_url = os.getenv("INVOICES_DATABASE_URL", f"sqlite:///{invoices_database}")

    try:
        # Create engines
        customers_engine = create_engine(customers_database_url, echo=False, pool_pre_ping=True)
        invoices_engine = create_engine(invoices_database_url, echo=False, pool_pre_ping=True)

        # Create session factories
        customer_session = sessionmaker(bind=customers_engine)
        invoice_session = sessionmaker(bind=invoices_engine)

        # Test connections
        with customer_session() as session:
            session.execute(text("SELECT 1")).fetchone()
        with invoice_session() as session:
            session.execute(text("SELECT 1")).fetchone()

        print("✅ Database connections established:")
        print(f"  • Customers DB: {customers_database_url}")
        print(f"  • Invoices DB:  {invoices_database_url}")

        return customer_session, invoice_session

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise


def setup_application() -> QApplication:
    """
    Setup and configure the Qt application.

    Returns:
        QApplication: Configured Qt application instance
    """
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Customer Management System")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Company")
    app.setOrganizationDomain("yourcompany.com")

    # Set application style and locale settings
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)

    # Set font for Persian/Farsi text support
    from PySide6.QtGui import QFont
    font = QFont("Arial", 9)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    return app


def show_error_dialog(title: str, message: str):
    """Show an error dialog."""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()


def main():
    """Main entry point of the application."""
    try:
        # Setup Qt application
        app = setup_application()

        # Setup database
        customer_session, invoices_session = setup_databases()

        # Create repository, logic, and controller
        repository = CustomerRepository(invoices_session, customer_session)
        logic = CustomerLogic(repository)
        controller = CustomerManagementController(logic)

        # Show the customer management dialog
        controller.show()

        # Start the application event loop
        sys.exit(app.exec())

    except Exception as e:
        error_message = f"Failed to start application: {str(e)}"
        print(error_message)

        # Try to show error dialog if Qt is available
        try:
            if 'app' in locals():
                show_error_dialog("Application Error", error_message)
            else:
                app = QApplication(sys.argv)
                show_error_dialog("Application Error", error_message)
        except:
            pass  # If even the error dialog fails, just print to console

        sys.exit(1)


if __name__ == "__main__":
    main()

# Example usage and configuration
"""
To use this application:

1. Install required dependencies:
   pip install PySide6 SQLAlchemy

2. Set up your database connection by modifying the DATABASE_URL:
   - For SQLite (default): 'sqlite:///customers.db'
   - For PostgreSQL: 'postgresql://user:password@localhost/dbname'
   - For MySQL: 'mysql+pymysql://user:password@localhost/dbname'

3. Ensure your database has the required tables:
   - customers
   - companions  
   - issued_invoices
   - invoice_items

4. Run the application:
   python main.py

Environment Variables:
- DATABASE_URL: Database connection string (optional, defaults to SQLite)

The application will:
- Connect to the database
- Load all customers with their companions and invoice counts
- Provide search functionality across customers and companions
- Allow adding, editing, and deleting customers (with active invoice warnings)
- Show customer relationships and invoice information in an organized table

Note: The add/edit customer functionality shows placeholder dialogs.
In a production environment, you would implement proper customer form dialogs.
"""