# core/application_manager.py

"""
The Application Manager serves as the Composition Root for the entire application.
It is responsible for initializing logging, starting the application,
managing database connections, handling the setup wizard,
managing the login flow, transitioning to the main window,
and overseeing the application lifetime.
"""

import sys
import logging
import time

from pathlib import Path
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from PySide6.QtWidgets import QApplication, QWidget, QDialog
from PySide6.QtCore import Qt, Slot

from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder
from config.logging_config import configure_logging
from config.config import DATABASE_PATHS

from features.Setup_Wizard.setup_wizard_factory import SetupWizardFactory
from features.Login.login_window_factory import LoginWindowFactory
from features.Main_Window.main_window_factory import MainWindowFactory

from shared.dtos.auth_dtos import LoggedInUserDTO
from shared.orm_models.license_models import LicenseModel
from shared.orm_models.users_models import UsersModel


# =======================================================================
#  TIMER WITH LOGGER
# =======================================================================

class CheckpointTimer:
    """A simple performance timer that logs timing checkpoints."""
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("startup")
        self.start_time = time.perf_counter()
        self.last_checkpoint = self.start_time
        self.checkpoints = []

    def checkpoint(self, name):
        now = time.perf_counter()
        total = now - self.start_time
        delta = now - self.last_checkpoint
        self.checkpoints.append((name, total, delta))

        self.logger.info(f"[Checkpoint] {name}: total={total:.3f}s delta={delta:.3f}s")
        self.last_checkpoint = now

    def summary(self):
        self.logger.info("=== Startup Timing Summary ===")
        for name, total, delta in self.checkpoints:
            self.logger.info(f"{name}: {total:.3f}s (Δ{delta:.3f}s)")
        if self.checkpoints:
            self.logger.info(f"Total startup time: {self.checkpoints[-1][1]:.3f}s")


# =======================================================================
#  APPLICATION MANAGER (COMPOSITION ROOT)
# =======================================================================

class ApplicationManager:
    """
    The Composition Root and main orchestrator for the application.
    Handles: logging, startup, DB initialization, setup wizard,
    login flow, main window transitions, and application lifetime.
    """

    def __init__(self):
        # Configure logging system-wide
        configure_logging()

        self.logger = logging.getLogger("ApplicationManager")
        self.logger.info("Initializing Application Manager...")

        self.timer = CheckpointTimer(self.logger)
        self.timer.checkpoint("AppManager.__init__")

        self.app: QApplication = None
        self.engines: dict[str, Engine] = {}
        self.active_controller = None

    # -------------------------------------------------------------------
    #  START APPLICATION
    # -------------------------------------------------------------------

    def start_application(self) -> int:
        """Main entry point for the entire application."""
        self.timer.checkpoint("start_application()")

        # Create QApplication
        self.app = QApplication(sys.argv)
        self.timer.checkpoint("QApplication created")

        # Hook into app quit
        self.app.aboutToQuit.connect(self.on_app_quit)

        # Step 1: Initialize databases
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        absolute_paths = {name: str(PROJECT_ROOT / path) for name, path in DATABASE_PATHS.items()}

        initializer = DatabaseInitializer()
        is_demo_mode = "--demo" in self.app.arguments()

        try:
            if is_demo_mode:
                self.engines = initializer.setup_memory_databases()
            else:
                self.engines = initializer.setup_file_databases(absolute_paths)
        except Exception as exc:
            self.logger.exception("Database initialization failed.")
            return 1

        self.timer.checkpoint("Database engines initialized")

        # Step 2: Check if setup wizard is needed
        if self._is_setup_required():
            self.timer.checkpoint("Setup required. Launching wizard.")

            if not self.run_setup_wizard():
                self.logger.warning("Setup wizard cancelled by user.")
                return 1

            self.timer.checkpoint("Setup wizard completed.")
        else:
            self.timer.checkpoint("Setup not required. Continuing startup.")

        # Step 3: Seed data (safe)
        try:
            seeder = DatabaseSeeder(self.engines)
            seeder.seed_initial_data(is_demo_mode=is_demo_mode)
        except Exception:
            self.logger.exception("Failed during database seeding.")
            return 1

        self.timer.checkpoint("Database seeding complete")

        # Step 4: Auto-login or show login
        business_engine = self.engines.get("business")
        if not business_engine:
            self.logger.error("Users database engine not found.")
            return 1

        login_controller = LoginWindowFactory.create(engine=business_engine)
        auto_success, user_dto = login_controller._logic.check_and_auto_login()

        if auto_success and user_dto:
            self.logger.info(f"Auto-login success for '{user_dto.username}'")
            login_controller._logic.start_session(user_dto)
            self.transition_to_main_window(user_dto)
        else:
            self.logger.info("Auto-login failed or not enabled.")
            self.show_login()

        # Step 5: Start the Qt event loop
        self.timer.checkpoint("Starting event loop")
        exit_code = self.app.exec()
        self.timer.summary()
        return exit_code

    # -------------------------------------------------------------------
    #  SETUP CHECK
    # -------------------------------------------------------------------

    def _is_setup_required(self) -> bool:
        """Checks if license + admin user exist."""
        license_engine = self.engines.get("licenses")
        business_engine = self.engines.get("business")

        if not license_engine or not business_engine:
            raise RuntimeError("Both 'licenses' and 'users' engines are required.")

        # License check
        LicenseSession = sessionmaker(bind=license_engine)
        session = LicenseSession()
        try:
            has_license = session.query(LicenseModel).first() is not None
        finally:
            session.close()

        # Admin user check
        BusinessSession = sessionmaker(bind=business_engine)
        user_session = BusinessSession()
        try:
            has_admin = (
                user_session.query(UsersModel)
                .filter(UsersModel.role == "admin")
                .first()
                is not None
            )
        finally:
            user_session.close()

        return not has_license or not has_admin

    # -------------------------------------------------------------------
    #  SETUP WIZARD
    # -------------------------------------------------------------------

    def run_setup_wizard(self) -> bool:
        """Run setup wizard modally. True = completed."""
        business_engine = self.engines.get("business")
        license_engine = self.engines.get("licenses")

        controller = SetupWizardFactory.create(
            business_engine=business_engine,
            license_engine=license_engine,
        )

        view = controller.get_view()

        # Prepare wizard (sets first page but does NOT show window)
        if not controller.prepare_wizard():
            self.logger.warning("Setup wizard preparation returned False.")
            return True

        result = view.exec()
        return result == QDialog.DialogCode.Accepted

    # -------------------------------------------------------------------
    #  LOGIN FLOW
    # -------------------------------------------------------------------

    def show_login(self):
        """Create and show login window."""
        self.timer.checkpoint("show_login()")

        business_engine = self.engines.get("business")
        if not business_engine:
            self.logger.error("Users DB engine missing. Cannot show login.")
            return

        self.active_controller = LoginWindowFactory.create(engine=business_engine)
        self.active_controller.login_successful.connect(self.on_login_successful)

        login_view = self.active_controller.get_view()
        login_view.show()

        self.timer.checkpoint("Login window displayed")

    @Slot(LoggedInUserDTO)
    def on_login_successful(self, user_dto: LoggedInUserDTO):
        """After manual login."""
        self.timer.checkpoint(f"Manual login success for '{user_dto.username}'")

        if self.active_controller:
            self.active_controller._logic.start_session(user_dto)
            self.active_controller.get_view().close()
            self.active_controller = None

        self.transition_to_main_window(user_dto)

    # -------------------------------------------------------------------
    #  MAIN WINDOW TRANSITION
    # -------------------------------------------------------------------

    def transition_to_main_window(self, user_dto: LoggedInUserDTO):
        splash = self._create_splash_screen()
        splash.show()
        self.app.processEvents()

        self.timer.checkpoint("Splash screen shown")

        controller = MainWindowFactory.create(
            engines=self.engines,
            username=user_dto.username,
        )
        controller.initialize_with_user(user_dto.username)
        controller.logout_requested.connect(self.on_logout_requested)

        self.active_controller = controller

        main_view = controller.get_view()
        splash.close()
        main_view.show()

        self.timer.checkpoint("Main window displayed")

    # -------------------------------------------------------------------
    #  LOGOUT FLOW
    # -------------------------------------------------------------------

    @Slot()
    def on_logout_requested(self):
        self.timer.checkpoint("Logout requested")

        business_engine = self.engines.get("business")
        if not business_engine:
            self.logger.error("Users engine missing in logout.")
            return

        temp_login = LoginWindowFactory.create(engine=business_engine)
        temp_login._logic.perform_full_logout()

        if self.active_controller:
            self.active_controller.get_view().close()
            self.active_controller = None

        self.timer.checkpoint("Main window closed")
        self.show_login()

    # -------------------------------------------------------------------
    #  SPLASH
    # -------------------------------------------------------------------

    def _create_splash_screen(self) -> QWidget:
        splash = QWidget()
        splash.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        splash.resize(400, 300)
        return splash

    # -------------------------------------------------------------------
    #  APP QUIT
    # -------------------------------------------------------------------

    def on_app_quit(self):
        self.logger.info("Application is closing. Ending session.")

        business_engine = self.engines.get("business")
        if not business_engine:
            self.logger.error("Cannot end session: users engine missing.")
            return

        temp_login = LoginWindowFactory.create(engine=business_engine)
        temp_login._logic.end_session()
