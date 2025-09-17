import sys
import time
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from pathlib import Path

# --- 1. Import the Core Infrastructure and High-Level Components ---
from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder
from shared.session_provider import SessionProvider
from config.config import DATABASE_PATHS

# --- 2. Import the FACTORIES for each major feature ---
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

    This class is responsible for:
    1. Initializing core services like databases.
    2. Managing the high-level application flow (e.g., login -> main window).
    3. Using factories to construct the application's features.
    """

    def __init__(self):
        self.timer = CheckpointTimer()
        self.timer.checkpoint("AppManager.__init__")

        # --- Application-level state placeholders ---
        self.app: QApplication = None
        self.session_provider: SessionProvider = None
        # The manager only needs to know about the currently active top-level controller
        self.active_controller = None

    def start_application(self) -> int:
        """
        The main entry point to initialize and run the entire application.
        """
        self.timer.checkpoint("start_application()")
        self.app = QApplication(sys.argv)
        self.timer.checkpoint("QApplication created")

        # --- STEP 1: RESOLVE PATHS AND INITIALIZE INFRASTRUCTURE ---

        # This is the single, stable anchor point for all file resources.
        # It assumes app_manager.py is in a 'core' directory one level
        # below the project root.
        PROJECT_ROOT = Path(__file__).resolve().parent.parent

        # Construct foolproof, absolute paths for the databases.
        database_absolute_paths = {
            name: str(PROJECT_ROOT / path) for name, path in DATABASE_PATHS.items()
        }

        initializer = DatabaseInitializer()
        is_demo_mode = "--demo" in self.app.arguments()

        if is_demo_mode:
            self.session_provider = initializer.setup_memory_databases()
        else:
            self.session_provider = initializer.setup_file_databases(database_absolute_paths)

        self.timer.checkpoint("Database schemas initialized & SessionProvider created")

        # --- STEP 2: SEED INITIAL DATA ---
        seeder = DatabaseSeeder(self.session_provider)
        seeder.seed_initial_data()
        self.timer.checkpoint("Database seeding complete")

        # --- STEP 3: HANDLE APPLICATION LOGIC (AUTO-LOGIN) ---
        temp_login_controller = LoginWindowFactory.create(self.session_provider)
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

        # Use the factory to create the entire, fully-wired login feature
        self.active_controller = LoginWindowFactory.create(self.session_provider)
        self.active_controller.login_successful.connect(self.on_login_successful)

        # Connect the final success signal from the _view to our transition method
        login_view = self.active_controller.get_view()

        login_view.show()
        self.timer.checkpoint("Login window displayed")

    def on_login_successful(self, username: str, role: str):
        """Handles the transition after a successful manual login."""
        self.timer.checkpoint(f"Manual login success for '{username}'")

        # Clean up the login window before transitioning
        if self.active_controller:
            self.active_controller.get_view().close()
            self.active_controller = None # Release the reference

        self.transition_to_main_window(username, role)

    def transition_to_main_window(self, username: str, role: str):
        """Shows a splash screen, then creates and shows the main window feature."""
        splash = self._create_splash_screen()
        splash.show()
        self.app.processEvents()  # Ensure splash is drawn before heavy work
        self.timer.checkpoint("Splash screen shown")

        # Use the factory to create the entire, fully-wired main window feature
        self.active_controller = MainWindowFactory.create(self.session_provider, username)

        # Pass the logged-in user's data to the main window for initialization
        self.active_controller.initialize_with_user(username)

        # Get the _view from the controller and show it
        main_view = self.active_controller.get_view()
        splash.close()
        main_view.show()
        self.timer.checkpoint("Main window displayed")

    def _create_splash_screen(self) -> QWidget:
        """Creates and returns a simple splash screen widget."""
        # This helper method's implementation is good, no changes needed.
        # It's purely UI and self-contained.
        # ... (your splash screen code) ...
        splash_widget = QWidget()  # Placeholder
        splash_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        splash_widget.resize(400, 300)
        return splash_widget
