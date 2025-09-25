# core/application_manager.py

import sys
import time
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from pathlib import Path
from sqlalchemy import Engine

from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder
from config.config import DATABASE_PATHS

from features.Login.login_window_factory import LoginWindowFactory
from features.Main_Window.main_window_factory import MainWindowFactory


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

        PROJECT_ROOT = Path(__file__).resolve().parent.parent
        database_absolute_paths = {
            name: str(PROJECT_ROOT / path) for name, path in DATABASE_PATHS.items()
        }

        initializer = DatabaseInitializer()
        is_demo_mode = "--demo" in self.app.arguments()

        if is_demo_mode:
            self.engines = initializer.setup_memory_databases()
        else:
            self.engines = initializer.setup_file_databases(database_absolute_paths)

        self.timer.checkpoint("Database engines initialized")

        # The seeder takes the dictionary of engines
        seeder = DatabaseSeeder(self.engines)
        seeder.seed_initial_data()
        self.timer.checkpoint("Database seeding complete")

        users_engine = self.engines.get('users')
        if not users_engine:
            raise RuntimeError("The 'users' database engine is required but was not found.")

        temp_login_controller = LoginWindowFactory.create(engine=users_engine)
        auto_login_successful, user_dto = temp_login_controller._logic.check_and_auto_login()

        if auto_login_successful and user_dto:
            self.timer.checkpoint(f"Auto-login success for '{user_dto.username}'")
            self.transition_to_main_window(user_dto.username, user_dto.role)
        else:
            self.timer.checkpoint("Auto-login failed or not enabled")
            self.show_login()

        # --- STEP 4: START THE EVENT LOOP ---
        self.timer.checkpoint("Starting app event loop")
        exit_code = self.app.exec()
        self.timer.summary()
        return exit_code

    def show_login(self):
        """Creates and shows the login window feature using its factory."""
        self.timer.checkpoint("show_login()")

        users_engine = self.engines.get('users')
        if not users_engine:
            # In a real app, you might show an error dialog here
            raise RuntimeError("Cannot show login window: 'users' database engine is missing.")

        self.active_controller = LoginWindowFactory.create(engine=users_engine)
        self.active_controller.login_successful.connect(self.on_login_successful)

        login_view = self.active_controller.get_view()
        login_view.show()
        self.timer.checkpoint("Login window displayed")

    def on_login_successful(self, username: str, role: str):
        """Handles the transition after a successful manual login."""
        self.timer.checkpoint(f"Manual login success for '{username}'")
        if self.active_controller:
            self.active_controller.get_view().close()
            self.active_controller = None
        self.transition_to_main_window(username, role)

    def transition_to_main_window(self, username: str, role: str):
        """Shows a splash screen, then creates and shows the main window feature."""
        splash = self._create_splash_screen()
        splash.show()
        self.app.processEvents()
        self.timer.checkpoint("Splash screen shown")

        self.active_controller = MainWindowFactory.create(engines=self.engines, username=username)

        self.active_controller.initialize_with_user(username)

        main_view = self.active_controller.get_view()
        splash.close()
        main_view.show()
        self.timer.checkpoint("Main window displayed")

    def _create_splash_screen(self) -> QWidget:
        # This implementation is fine.
        splash_widget = QWidget()
        splash_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        splash_widget.resize(400, 300)
        return splash_widget
