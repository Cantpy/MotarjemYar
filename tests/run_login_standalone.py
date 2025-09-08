import sys
from PySide6.QtWidgets import QApplication

# --- 1. Import the necessary infrastructure components ---
from core.database_init import DatabaseInitializer
from core.database_seeder import DatabaseSeeder

# --- 2. Import the FACTORY for the feature you want to test ---
from features.Login.login_window_factory import LoginWindowFactory


def main():
    """
    A standalone test script for running and debugging the Login feature in isolation.
    This simulates the role of the ApplicationManager.
    """
    app = QApplication(sys.argv)
    print("--- Running Login Feature in Standalone Mode ---")

    # --- SETUP: Simulate the ApplicationManager's startup sequence ---
    # 1. Initialize databases (using file-based for this test)
    initializer = DatabaseInitializer()
    session_provider = initializer.setup_file_databases()

    # 2. Seed the database with the dummy user
    seeder = DatabaseSeeder(session_provider)
    seeder.seed_initial_data()

    # --- EXECUTION: Use the factory to create the login feature ---
    login_controller = LoginWindowFactory.create(session_provider)
    login_view = login_controller.get_view()

    # --- TEST LOGIC: Define what happens on success ---
    def on_login_success(username, role):
        print(f"\n--- STANDALONE TEST: Login Successful! ---")
        print(f"Username: {username}, Role: {role}")
        print("--- In the real app, ApplicationManager would now transition to MainWindow. ---")
        app.quit() # Close the application after successful login

    # Connect the success signal to our test handler
    login_view.login_successful.connect(on_login_success)

    # --- RUN ---
    login_view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
