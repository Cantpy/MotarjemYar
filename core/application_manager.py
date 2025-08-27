from PySide6.QtWidgets import QApplication
import sys
import json
import os
from datetime import datetime
from modules.helper_functions import return_resource, show_error_message_box
from modules.user_context import UserContext
import time

splash_screen_file = return_resource("resources", "Splash Screen.jpg", "Designs")


class CheckpointTimer:
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


# Modified sections of your ApplicationManager class

class ApplicationManager:
    """Manages the application flow including login and main window access"""

    def __init__(self):
        # Initialize timer at the very beginning
        self.timer = CheckpointTimer()
        self.timer.checkpoint("ApplicationManager.__init__ started")

        self.app = None
        self.main_window = None
        self.login_widget = None
        self.setup_wizard = None  # Add setup wizard
        self.current_user = None
        self.current_role = None
        self.splash_screen_file = splash_screen_file

        # Check if we need to use PostgreSQL or SQLite
        self.use_postgresql = self.check_postgresql_config()

        if self.use_postgresql:
            self.db_config = self.load_postgresql_config()
        else:
            self.db_path = return_resource("databases", "users.db")

        self.user_context: UserContext | None = None

        # Your existing palette functions
        self.available_palettes = {
            "بهاری": self.set_spring_palette,
            "تابستان": self.set_summer_palette,
            "پائیزه": self.set_autumn_palette,
            "زمستان": self.set_winter_palette,
            "دراکولا": self.set_dark_palette
        }

        self.timer.checkpoint("ApplicationManager.__init__ completed")

    def check_postgresql_config(self) -> bool:
        """Check if PostgreSQL configuration exists"""
        config_path = "config/database_config.json"
        return os.path.exists(config_path)

    def load_postgresql_config(self) -> dict:
        """Load PostgreSQL configuration"""
        config_path = "config/database_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading PostgreSQL config: {e}")
            return {}

    def is_first_run(self) -> bool:
        """Check if this is the first run requiring setup"""
        from databases.database_provisioning import DatabaseProvisioner
        provisioner = DatabaseProvisioner()
        return provisioner.is_first_run()

    def start_application(self):
        """Initialize and start the application"""
        try:
            self.timer.checkpoint("start_application() called")

            # Create QApplication first
            self.app = QApplication(sys.argv)
            self.app.setStyle("Fusion")
            self.timer.checkpoint("QApplication created and styled")

            # Check if this is first run
            if self.is_first_run():
                self.timer.checkpoint("First run detected, showing setup wizard")
                self.show_first_run_setup()
                return self.app.exec()

            # Setup databases (existing or newly created)
            if self.use_postgresql:
                self.setup_postgresql_connection()
            else:
                self.setup_all_databases()
            self.timer.checkpoint("Databases setup completed")

            # Check for remembered login
            if self.check_auto_login():
                print("user has successfully checked remember me")
                self.timer.checkpoint("Auto-login check completed (success)")

                # Log the login time
                self.log_user_login(self.current_user, status='auto_login_success')
                self.show_splash_and_main_window()
            else:
                print("UsersModel did not check remember me")
                self.timer.checkpoint("Auto-login check completed (failed)")
                self.show_login()

            self.timer.checkpoint("About to start app.exec()")
            return self.app.exec()
        except Exception as e:
            print(f"Error starting application: {e}")
            return 1

    def show_first_run_setup(self):
        """Show the first-run setup wizard"""
        try:
            from modules.setup_wizard import FirstRunSetupWizard

            self.setup_wizard = FirstRunSetupWizard()
            self.setup_wizard.setup_completed.connect(self.on_setup_completed)
            self.setup_wizard.show()

        except Exception as e:
            print(f"Error showing setup wizard: {e}")
            # Fallback to login if setup fails
            self.show_login()

    def on_setup_completed(self, config_data):
        """Handle completion of first-run setup"""
        try:
            self.timer.checkpoint("Setup wizard completed")

            # Setup databases with the new configuration
            if config_data.get('database_type') == 'postgresql':
                self.use_postgresql = True
                self.db_config = config_data.get('database_config', {})
                self.setup_postgresql_connection()
            else:
                self.use_postgresql = False
                self.setup_all_databases()

            self.timer.checkpoint("Post-setup database initialization completed")

            # Close setup wizard
            if self.setup_wizard:
                self.setup_wizard.close()
                self.setup_wizard = None

            # Show login screen
            self.show_login()

        except Exception as e:
            print(f"Error completing setup: {e}")
            self.show_login()

    def setup_postgresql_connection(self):
        """Setup PostgreSQL database connection"""
        try:
            from databases.database_provisioning import DatabaseProvisioner

            provisioner = DatabaseProvisioner()
            provisioner.setup_postgresql_databases(self.db_config)

            # Test connection
            if provisioner.test_postgresql_connection(self.db_config):
                print("PostgreSQL connection established successfully")
                self.timer.checkpoint("PostgreSQL connection established")
            else:
                print("Failed to establish PostgreSQL connection")
                raise Exception("PostgreSQL connection failed")

        except Exception as e:
            print(f"Error setting up PostgreSQL: {e}")
            # Fallback to SQLite
            self.use_postgresql = False
            self.setup_all_databases()

    def setup_all_databases(self):
        """Setup SQLite databases"""
        try:
            from databases.database_provisioning import DatabaseProvisioner

            provisioner = DatabaseProvisioner()
            provisioner.setup_all_databases()

            print("SQLite databases setup completed")
            self.timer.checkpoint("SQLite databases setup completed")

        except Exception as e:
            print(f"Error setting up SQLite databases: {e}")
            raise

    def check_auto_login(self) -> bool:
        """Check if user has auto-login enabled and credentials are valid"""
        try:
            from databases.database_operations import DatabaseOperations

            db_ops = DatabaseOperations()

            if self.use_postgresql:
                conn = db_ops.get_postgresql_connection(self.db_config)
            else:
                conn = db_ops.get_connection(self.db_path)

            if not conn:
                return False

            # Check for remembered credentials
            cursor = conn.cursor()

            if self.use_postgresql:
                cursor.execute("""
                    SELECT username, role FROM users 
                    WHERE remember_me = TRUE AND is_active = TRUE
                    ORDER BY last_login DESC LIMIT 1
                """)
            else:
                cursor.execute("""
                    SELECT username, role FROM users 
                    WHERE remember_me = 1 AND is_active = 1
                    ORDER BY last_login DESC LIMIT 1
                """)

            result = cursor.fetchone()

            if result:
                self.current_user = result[0]
                self.current_role = result[1]
                self.timer.checkpoint(f"Auto-login found for user: {self.current_user}")
                return True

            return False

        except Exception as e:
            print(f"Error checking auto-login: {e}")
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def log_user_login(self, username: str, status: str = 'success'):
        """Log user login attempt"""
        try:
            from databases.database_operations import DatabaseOperations

            db_ops = DatabaseOperations()

            if self.use_postgresql:
                conn = db_ops.get_postgresql_connection(self.db_config)
            else:
                conn = db_ops.get_connection(self.db_path)

            if not conn:
                return

            cursor = conn.cursor()

            if self.use_postgresql:
                cursor.execute("""
                    INSERT INTO login_logs (username, login_time, status)
                    VALUES (%s, %s, %s)
                """, (username, datetime.now(), status))
            else:
                cursor.execute("""
                    INSERT INTO login_logs (username, login_time, status)
                    VALUES (?, ?, ?)
                """, (username, datetime.now().isoformat(), status))

            conn.commit()

        except Exception as e:
            print(f"Error logging user login: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def show_login(self):
        """Show the login widget"""
        try:
            from modules.RBAC import LoginWidget

            self.login_widget = LoginWidget(self.use_postgresql,
                                            self.db_config if self.use_postgresql else self.db_path)
            self.login_widget.login_successful.connect(self.on_login_successful)
            self.login_widget.show()
            self.timer.checkpoint("Login widget displayed")

        except Exception as e:
            print(f"Error showing login widget: {e}")

    def on_login_successful(self, username: str, role: str):
        """Handle successful login"""
        try:
            self.current_user = username
            self.current_role = role

            # Log the successful login
            self.log_user_login(username, 'manual_login_success')

            # Close login widget
            if self.login_widget:
                self.login_widget.close()
                self.login_widget = None

            # Show main application
            self.show_splash_and_main_window()

        except Exception as e:
            print(f"Error handling login success: {e}")

    def show_splash_and_main_window(self):
        """Show splash screen followed by main window"""
        try:
            # Show splash screen first
            splash_widget = self.create_splash_screen()
            splash_widget.show()

            # Process events to ensure splash is visible
            self.app.processEvents()

            # Initialize main window in background
            self.timer.checkpoint("Starting main window initialization")
            self.initialize_main_window()

            # Close splash and show main window
            splash_widget.close()
            self.main_window.show()

            self.timer.checkpoint("Main window displayed")

        except Exception as e:
            print(f"Error showing splash and main window: {e}")

    def create_splash_screen(self):
        """Create and return splash screen widget"""
        try:
            from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPixmap

            splash_widget = QWidget()
            splash_widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            splash_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

            layout = QVBoxLayout(splash_widget)

            if os.path.exists(self.splash_screen_file):
                splash_label = QLabel()
                pixmap = QPixmap(self.splash_screen_file)
                splash_label.setPixmap(pixmap)
                splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(splash_label)
            else:
                # Fallback text splash
                splash_label = QLabel("Loading Application...")
                splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                splash_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
                layout.addWidget(splash_label)

            # Center the splash screen
            splash_widget.resize(400, 300)
            screen_geometry = self.app.primaryScreen().geometry()
            x = (screen_geometry.width() - splash_widget.width()) // 2
            y = (screen_geometry.height() - splash_widget.height()) // 2
            splash_widget.move(x, y)

            return splash_widget

        except Exception as e:
            print(f"Error creating splash screen: {e}")
            # Return a simple widget as fallback
            return QWidget()

    def initialize_main_window(self):
        """Initialize the main application window"""
        try:
            from modules.MainWindow import MainWindow

            # Create user context
            self.user_context = UserContext(
                username=self.current_user,
                role=self.current_role,
                database_config=self.db_config if self.use_postgresql else self.db_path,
                use_postgresql=self.use_postgresql
            )

            # Create main window
            self.main_window = MainWindow(self.user_context)

            # Apply saved theme
            self.apply_saved_theme()

            self.timer.checkpoint("Main window initialized")

        except Exception as e:
            print(f"Error initializing main window: {e}")
            raise

    def apply_saved_theme(self):
        """Apply the user's saved theme preference"""
        try:
            from databases.database_operations import DatabaseOperations

            db_ops = DatabaseOperations()

            if self.use_postgresql:
                conn = db_ops.get_postgresql_connection(self.db_config)
            else:
                conn = db_ops.get_connection(self.db_path)

            if not conn:
                return

            cursor = conn.cursor()

            if self.use_postgresql:
                cursor.execute("""
                    SELECT theme_preference FROM user_preferences
                    WHERE username = %s
                """, (self.current_user,))
            else:
                cursor.execute("""
                    SELECT theme_preference FROM user_preferences
                    WHERE username = ?
                """, (self.current_user,))

            result = cursor.fetchone()

            if result and result[0] in self.available_palettes:
                theme_name = result[0]
                self.available_palettes[theme_name]()
                print(f"Applied saved theme: {theme_name}")
            else:
                # Apply default theme
                self.set_summer_palette(self.app)

        except Exception as e:
            print(f"Error applying saved theme: {e}")
            # Apply default theme on error
            self.set_summer_palette(self.app)
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def cleanup(self):
        """Cleanup resources before application exit"""
        try:
            if self.main_window:
                self.main_window.close()
            if self.login_widget:
                self.login_widget.close()
            if self.setup_wizard:
                self.setup_wizard.close()

            self.timer.checkpoint("Application cleanup completed")

        except Exception as e:
            print(f"Error during cleanup: {e}")

    # Your existing palette methods would go here...
    def set_spring_palette(self, app):
        """Apply spring theme palette"""
        try:
            # Implement your spring palette _logic here
            from modules.palettes import set_spring_palette
            set_spring_palette(app)

        except Exception as e:
            title = "خطا در تنظیم تم بهاری"
            message = ("خطا در تنظیم تم بهاری:\n"
                       f"{str(e)}")
            show_error_message_box(None, title, message)

    def set_summer_palette(self, app):
        """Apply summer theme palette"""
        try:
            from modules.palettes import set_summer_palette
            set_summer_palette(app)

        except Exception as e:
            title = "خطا در تنظیم تم تابستانی"
            message = ("خطا در تنظیم تم تابستانی:\n"
                       f"{str(e)}")
            show_error_message_box(None, title, message)

    def set_autumn_palette(self, app):
        """Apply autumn theme palette"""
        try:
            from modules.palettes import set_autumn_palette
            set_autumn_palette(app)

        except Exception as e:
            title = "خطا در تنظیم تم پاییزی"
            message = ("خطا در تنظیم تم پاییزی:\n"
                       f"{str(e)}")
            show_error_message_box(None, title, message)

    def set_winter_palette(self, app):
        """Apply winter theme palette"""
        try:
            from modules.palettes import set_winter_palette
            set_winter_palette(app)

        except Exception as e:
            title = "خطا در تنظیم تم زمستانی"
            message = ("خطا در تنظیم تم زمستانی:\n"
                       f"{str(e)}")
            show_error_message_box(None, title, message)

    def set_dark_palette(self, app):
        """Apply dark (Dracula) theme palette"""
        try:
            from modules.palettes import set_dark_palette
            set_dark_palette(app)

        except Exception as e:
            title = "خطا در تنظیم تم تاریک"
            message = ("خطา در تنظیم تم تاریک:\n"
                       f"{str(e)}")
            show_error_message_box(None, title, message)
