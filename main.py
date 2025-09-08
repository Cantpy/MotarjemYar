import sys
from core.application_manager import ApplicationManager


if __name__ == "__main__":
    # 1. Create the manager
    manager = ApplicationManager()

    # 2. Start the application and get the exit code
    exit_code = manager.start_application()

    # 3. Exit gracefully
    sys.exit(exit_code)
