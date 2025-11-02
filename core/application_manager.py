# core/application_manager.py

import sys
import time

from pathlib import Path
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from PySide6.QtWidgets import QApplication, QWidget, QDialog
from PySide6.QtCore import Qt, Slot

from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder
from config.config import DATABASE_PATHS

from features.Setup_Wizard.setup_wizard_factory import SetupWizardFactory
from features.Login.login_window_factory import LoginWindowFactory
from features.Main_Window.main_window_factory import MainWindowFactory

from shared.dtos.auth_dtos import LoggedInUserDTO
from shared.orm_models.license_models import LicenseModel
from shared.orm_models.users_models import UsersModel


class CheckpointTimer:
    """A simple performance timer for tracking startup."""
    def __init__(self):
        self.start_time = time.perf_counter()
        self.last_checkpoint = self.start_time
        self.checkpoints = []

    def checkpoint(self, name):
        now = time.perf_counter()
        since_start = now - self.start_time
        since_last = now - self.last_checkpoint
        self.checkpoints.append((name, since_start, since_last))
        print(f"[Checkpoint] {name}: {since_start:.3f}s total, {since_last:.3f}s since last")
        self.last_checkpoint = now

    def summary(self):
        print("\n=== Startup Timing Summary ===")
        for name, total, delta in self.checkpoints:
            print(f"{name}: {total:.3f}s (Δ{delta:.3f}s)")
        print(f"Total startup time: {self.checkpoints[-1][1]:.3f}s")


class ApplicationManager:
    """
    The Composition Root and main orchestrator for the application.
    """

    def __init__(self):
        self.timer = CheckpointTimer()
        self.timer.checkpoint("AppManager.__init__")
        self.app: QApplication = None
        self.engines: dict[str, Engine] = {}
        self.active_controller = None

    def start_application(self) -> int:
        """
        The main entry point to initialize and run the entire application.
        """
        self.timer.checkpoint("start_application()")
        self.app = QApplication(sys.argv)
        self.timer.checkpoint("QApplication created")

        # --- STEP 1: INITIALIZE DATABASES ---
        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        database_absolute_paths = {name: str(PROJECT_ROOT / path) for name, path in DATABASE_PATHS.items()}
        initializer = DatabaseInitializer()
        is_demo_mode = "--demo" in self.app.arguments()

        if is_demo_mode:
            self.engines = initializer.setup_memory_databases()
        else:
            self.engines = initializer.setup_file_databases(database_absolute_paths)
        self.timer.checkpoint("Database engines initialized")

        # --- STEP 2: CHECK IF SETUP IS REQUIRED ---
        if self._is_setup_required():
            self.timer.checkpoint("Setup required. Launching wizard...")
            setup_successful = self.run_setup_wizard()
            if not setup_successful:
                print("Setup was cancelled by the user. Exiting application.")
                return 1  # Exit with an error code
            self.timer.checkpoint("Setup wizard completed successfully.")
        else:
            self.timer.checkpoint("Setup not required. Proceeding with normal startup.")

        # --- STEP 3: SEED DATA (NOW SAFEGUARDED) ---
        seeder = DatabaseSeeder(self.engines)
        seeder.seed_initial_data(is_demo_mode=is_demo_mode)
        self.timer.checkpoint("Database seeding complete")

        # --- STEP 4: PROCEED TO LOGIN/MAIN WINDOW ---
        users_engine = self.engines.get('users')
        if not users_engine:
            raise RuntimeError("The 'users' database engine is required but was not found.")

        temp_login_controller = LoginWindowFactory.create(engine=users_engine)
        auto_login_successful, user_dto = temp_login_controller._logic.check_and_auto_login()

        if auto_login_successful and user_dto:
            self.timer.checkpoint(f"Auto-login success for '{user_dto.username}'")
            temp_login_controller._logic.start_session(user_dto)
            self.transition_to_main_window(user_dto)
        else:
            self.timer.checkpoint("Auto-login failed or not enabled")
            self.show_login()

        # --- STEP 5: START THE EVENT LOOP ---
        self.timer.checkpoint("Starting app event loop")
        exit_code = self.app.exec()
        self.timer.summary()
        return exit_code

    def _is_setup_required(self) -> bool:
        """
        Checks if the application is fully configured. A complete setup
        requires BOTH a license AND at least one admin user.
        """
        license_engine = self.engines.get('licenses')
        users_engine = self.engines.get('users')
        if not license_engine or not users_engine:
            raise RuntimeError("Both 'licenses' and 'users' engines are required for setup check.")

        # Check for license existence
        LicenseSession = sessionmaker(bind=license_engine)
        license_session = LicenseSession()
        try:
            license_exists = license_session.query(LicenseModel).first() is not None
        finally:
            license_session.close()

        # Check for admin user existence
        UserSession = sessionmaker(bind=users_engine)
        user_session = UserSession()
        try:
            admin_exists = user_session.query(UsersModel).filter(UsersModel.role == 'admin').first() is not None
        finally:
            user_session.close()

        # If either one is missing, setup is required.
        return not license_exists or not admin_exists

    def run_setup_wizard(self) -> bool:
        """
        Creates and runs the setup wizard modally.
        The application will wait here until the wizard is finished or cancelled.
        Returns True if the wizard was completed, False otherwise.
        """
        users_engine = self.engines.get('users')
        license_engine = self.engines.get('licenses')

        # 1. Create the wizard using the factory
        wizard_controller = SetupWizardFactory.create(
            user_db_engine=users_engine,
            license_db_engine=license_engine
        )

        # 2. Get the view from the controller
        wizard_view = wizard_controller.get_view()

        # 3. Ask the controller to PREPARE the wizard. This sets the start page.
        #    It does NOT show the window.
        needs_run = wizard_controller.prepare_wizard()
        if not needs_run:
            # This is a safeguard; _is_setup_required should prevent this case.
            return True

        # 4. EXECUTE the prepared wizard modally. This is a BLOCKING call.
        #    The code will pause here until the user finishes or cancels.
        result_code = wizard_view.exec()

        # 5. Return True only if the user clicks "Finish".
        return result_code == QDialog.DialogCode.Accepted

    def show_login(self):
        """Creates and shows the login window feature using its factory."""
        self.timer.checkpoint("show_login()")
        users_engine = self.engines.get('users')
        if not users_engine:
            raise RuntimeError("Cannot show login window: 'users' database engine is missing.")

        self.active_controller = LoginWindowFactory.create(engine=users_engine)
        self.active_controller.login_successful.connect(self.on_login_successful)
        login_view = self.active_controller.get_view()
        login_view.show()
        self.timer.checkpoint("Login window displayed")

    @Slot(LoggedInUserDTO)
    def on_login_successful(self, user_dto: LoggedInUserDTO):
        """Handles the transition after a successful manual login."""
        self.timer.checkpoint(f"Manual login success for '{user_dto.username}'")
        if self.active_controller:
            self.active_controller._logic.start_session(user_dto)
            self.active_controller.get_view().close()
            self.active_controller = None
        self.transition_to_main_window(user_dto)

    def transition_to_main_window(self, user_dto: LoggedInUserDTO):
        """Shows a splash screen, then creates and shows the main window feature."""
        splash = self._create_splash_screen()
        splash.show()
        self.app.processEvents()
        self.timer.checkpoint("Splash screen shown")

        self.active_controller = MainWindowFactory.create(engines=self.engines, username=user_dto.username)
        self.active_controller.initialize_with_user(user_dto.username)
        self.active_controller.logout_requested.connect(self.on_logout_requested)

        main_view = self.active_controller.get_view()
        splash.close()
        main_view.show()
        self.timer.checkpoint("Main window displayed")

    @Slot()
    def on_logout_requested(self):
        """
        Handles the full logout process and transitions back to the login screen.
        """
        self.timer.checkpoint("Logout requested by user")

        # 1. Perform the logout logic
        users_engine = self.engines.get('users')
        if not users_engine:
            print("ERROR: Cannot log out, 'users' engine not found.")
            return

        # Create a temporary service to perform the logout actions
        temp_login_controller = LoginWindowFactory.create(engine=users_engine)
        temp_login_controller._logic.perform_full_logout()

        # 2. Close the main window
        if self.active_controller:
            self.active_controller.get_view().close()
            self.active_controller = None
            self.timer.checkpoint("Main window closed")

        # 3. Transition back to the login screen
        self.show_login()

    def _create_splash_screen(self) -> QWidget:
        # This implementation is fine.
        splash_widget = QWidget()
        splash_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        splash_widget.resize(400, 300)
        return splash_widget

    def on_app_quit(self):
        """Slot for when the QApplication is about to quit."""
        print("Application is closing. Ending session.")
        temp_login_controller = LoginWindowFactory.create(engine=self.engines.get('users'))
        temp_login_controller._logic.end_session()
