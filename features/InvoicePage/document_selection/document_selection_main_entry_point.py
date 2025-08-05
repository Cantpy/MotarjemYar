import sys
import sqlite3
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Import our modules
from features.InvoicePage.document_selection.document_selection_repo import DatabaseRepository
from features.InvoicePage.document_selection.document_selection_logic import DocumentLogic, PriceCalculationLogic
from features.InvoicePage.document_selection.document_selection_controller import DocumentSelectionController


def create_sample_database(db_path: str):
    """Create sample database with test data"""
    # Sample SQL data from your schema
    sample_sql = """
        BEGIN TRANSACTION;
        CREATE TABLE IF NOT EXISTS "fixed_prices" (
            "id"	INTEGER NOT NULL,
            "name"	TEXT NOT NULL,
            "price"	INTEGER NOT NULL,
            "is_default"	BOOLEAN NOT NULL,
            "label_name"	TEXT,
            PRIMARY KEY("id"),
            UNIQUE("name")
        );
        CREATE TABLE IF NOT EXISTS "other_services" (
            "id"	INTEGER NOT NULL,
            "name"	TEXT NOT NULL,
            "price"	INTEGER NOT NULL,
            PRIMARY KEY("id"),
            UNIQUE("name")
        );
        CREATE TABLE IF NOT EXISTS "services" (
            "id"	INTEGER NOT NULL,
            "name"	TEXT NOT NULL,
            "base_price"	INTEGER,
            "dynamic_price_name_1"	TEXT,
            "dynamic_price_1"	INTEGER,
            "dynamic_price_name_2"	TEXT,
            "dynamic_price_2"	INTEGER,
            PRIMARY KEY("id")
        );
        INSERT INTO "fixed_prices" VALUES (1,'certified_copy',2250,1,'کپی برابر اصل (هر صفحه)');
        INSERT INTO "fixed_prices" VALUES (2,'judiciary_seal',60000,1,'تاییدیه دادگستری');
        INSERT INTO "fixed_prices" VALUES (3,'foreign_affairs_seal',15000,1,'تاییدیه امور خارجه (هر صفحه)');
        INSERT INTO "fixed_prices" VALUES (4,'official_translation',30000,1,'ثبت در سامانه (امور دفتری)');
        INSERT INTO "fixed_prices" VALUES (5,'additional_issues',12000,1,'نسخه اضافه (هر نسخه)');
        INSERT INTO "other_services" VALUES (1,'پیک',0);
        INSERT INTO "other_services" VALUES (2,'سایر خدمات',0);
        INSERT INTO "other_services" VALUES (3,'امور خارجه',0);
        INSERT INTO "services" VALUES (1,'کارت ملی',54000,NULL,NULL,NULL,NULL);
        INSERT INTO "services" VALUES (2,'شناسنامه',63000,'هر وقایع',9000,NULL,NULL);
        INSERT INTO "services" VALUES (3,'ریز نمرات دبیرستان، پیش دانشگاهی (هرترم)',0,'هر ترم',33000,'هر درس',1350);
        INSERT INTO "services" VALUES (4,'ریزنمرات دانشگاه (هرترم)',0,'هر ترم',36000,'هر درس',1350);
        INSERT INTO "services" VALUES (5,'کارت معافیت',54000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (6,'ابلاغیه، اخطار قضایی',72000,'هر سطر متن',5400,NULL,0);
        INSERT INTO "services" VALUES (7,'توصیه نامه تحصیلی (بعد از تحصیلات سوم راهنمایی)',66000,'هر سطر متن',2700,NULL,0);
        INSERT INTO "services" VALUES (8,'جواز اشتغال به کار',54000,'هر سطر متن',2700,NULL,0);
        INSERT INTO "services" VALUES (9,'حکم بازنشستگی',54000,'هر سطر توضیحات',2700,NULL,0);
        INSERT INTO "services" VALUES (10,'دفترچه بیمه',75000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (11,'دیپلم پایان تحصیلات متوسطه یا پیش دانشگاهی',75000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (12,'ریزنمرات دبستان، راهنمایی (هر سال)',66000,'هر درس',1350,NULL,0);
        INSERT INTO "services" VALUES (13,'سند تلفن همراه',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (14,'فیش مستمری',66000,'هر آیتم ریالی',900,NULL,0);
        INSERT INTO "services" VALUES (15,'کارت بازرگانی هوشمند',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (16,'کارت عضویت نظام مهندسی',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (17,'کارت نظام پزشکی',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (18,'کارت واکسیناسیون',66000,'هر تزریق',900,NULL,0);
        INSERT INTO "services" VALUES (19,'کارت پایان خدمت',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (20,'گزارش ورود و خروج از کشور',66000,'هر تردد',1350,NULL,0);
        INSERT INTO "services" VALUES (21,'گواهی اشتغال به تحصیل',66000,'هر سطر متن',2700,NULL,0);
        INSERT INTO "services" VALUES (22,'گواهی تجرد، تولّد، فوت',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (23,'گواهینامه رانندگی',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (24,'گواهی ریزنمرات دانشگاهی',66000,'هر سطر توضیحات',4500,NULL,0);
        INSERT INTO "services" VALUES (25,'گواهی عدم خسارت خودرو',66000,'هر سطر متن',4500,NULL,0);
        INSERT INTO "services" VALUES (26,'گواهی عدم سوءپیشینه (غیرفرمی)',64800,'هر سطر متن',4500,NULL,0);
        INSERT INTO "services" VALUES (27,'گواهی عدم سوءپیشینه (فرمی)',72000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (28,'گذرنامه',84000,'هر پرفراژ',4500,NULL,0);
        INSERT INTO "services" VALUES (29,'دانشنامه کاردانی، کارشناسی، کارشناسی ارشد، دکترا',108000,NULL,0,NULL,0);
        INSERT INTO "services" VALUES (30,'گواهی فنی و حرفه ای',108000,NULL,0,NULL,0);
        COMMIT;
"""

    # Create database file if it doesn't exist
    if not Path(db_path).exists():
        print(f"Creating sample database at: {db_path}")

        conn = sqlite3.connect(db_path)
        conn.executescript(sample_sql)
        conn.close()

        print("Sample database created successfully!")
    else:
        print(f"Database already exists at: {db_path}")


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.controller = None
        self.setup_ui()
        self.setup_logic()

    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("سیستم مدیریت اسناد و قیمت‌گذاری")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('فایل')

        # New invoice action
        new_action = QAction('فاکتور جدید', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_invoice)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('خروج', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('نمایش')

        # Show summary action
        summary_action = QAction('خلاصه فاکتور', self)
        summary_action.setShortcut('Ctrl+S')
        summary_action.triggered.connect(self.show_summary)
        view_menu.addAction(summary_action)

        # Refresh action
        refresh_action = QAction('بروزرسانی', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)

    def setup_logic(self):
        """Setup business logic and controllers"""
        try:
            # Create database
            db_path = "services.db"
            create_sample_database(db_path)

            # Initialize repository
            repository = DatabaseRepository(f"sqlite:///{db_path}")

            # Initialize logic components
            document_logic = DocumentLogic(repository)
            price_logic = PriceCalculationLogic(document_logic)

            # Initialize controller
            self.controller = DocumentSelectionController(document_logic, price_logic, self)

            # Create and set main view
            main_view = self.controller.create_view(self)
            layout = QVBoxLayout(self.centralWidget())
            layout.addWidget(main_view)

            print("Application initialized successfully!")

        except Exception as e:
            print(f"Error initializing application: {e}")
            sys.exit(1)

    def new_invoice(self):
        """Create new invoice (clear current)"""
        if self.controller:
            self.controller._on_clear_requested()

    def show_summary(self):
        """Show invoice summary"""
        if self.controller:
            self.controller.show_invoice_summary()

    def refresh_data(self):
        """Refresh application data"""
        if self.controller:
            self.controller.refresh_autocomplete()
            print("Data refreshed!")

    def closeEvent(self, event):
        """Handle application close event"""
        if self.controller:
            self.controller.cleanup()
        event.accept()


def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("سیستم مدیریت اسناد")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Document Management System")

    # Set right-to-left layout for Persian UI
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Print startup message
    print("=== سیستم مدیریت اسناد و قیمت‌گذاری ===")
    print("Application started successfully!")
    print("Database: services.db")
    print("UI Language: Persian (RTL)")
    print("=========================================")

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
