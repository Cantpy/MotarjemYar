# main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# --- Placeholder for your database setup ---
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# --- This is for demonstration ---
from shared.database_models.invoices_models import BaseInvoices
from shared.database_models.customer_models import BaseCustomers
from shared.database_models.services_models import BaseServices
from shared.database_models.user_models import BaseUsers

BaseInvoices.metadata.create_all(bind=engine)
BaseUsers.metadata.create_all(bind=engine)
BaseServices.metadata.create_all(bind=engine)
BaseCustomers.metadata.create_all(bind=engine)
# (You should add some dummy data here to see reports on launch)
# --- End of placeholder ---

from features.Reports.reports_view import ReportsView
from features.Reports.reports_controller import ReportsController
from features.Reports.reports_logic import ReportsLogic
from features.Reports.reports_repo import ReportsRepo
from file_exporter import FileExporter


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set a default font that supports Persian
    default_font = QFont("Tahoma", 11)
    app.setFont(default_font)

    # Load stylesheet
    style_sheet_path = Path("styles.qss")
    if style_sheet_path.exists():
        with open(style_sheet_path, "r") as f:
            app.setStyleSheet(f.read())

    # --- Dependency Injection ---
    db_session = SessionLocal()
    reports_repo = ReportsRepo(session=db_session)
    reports_logic = ReportsLogic(repo=reports_repo)
    file_exporter = FileExporter()
    reports_view = ReportsView()
    controller = ReportsController(view=reports_view, logic=reports_logic, exporter=file_exporter)

    reports_view.resize(1200, 700)  # Give it a nice default size
    reports_view.show()

    # Run a default report on startup for demonstration
    controller.update_all_reports()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
