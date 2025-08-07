import sys
from features.Login import LoginWidget
from PySide6.QtWidgets import QApplication
# from modules.application_manager import CheckpointTimer, ApplicationManager
from features.MainWindow_gaming import MainWindow

# def main():
#     """Main entry point with timing"""
#     try:
#         # Create timer before anything else
#         main_timer = CheckpointTimer()
#         main_timer.checkpoint("main() function started")
#
#         app_manager = ApplicationManager()
#         main_timer.checkpoint("ApplicationManager created")
#
#         exit_code = app_manager.start_application()
#         main_timer.checkpoint("Application execution completed")
#
#         main_timer.summary()
#         app_manager.cleanup()
#         sys.exit(exit_code)
#     except Exception as e:
#         print(f"Fatal error: {e}")
#         sys.exit(1)


# def main():
#     """Main entry point from Login Widget"""
#     try:
#         app = QApplication(sys.argv)
#         app_manager = LoginWidget()
#         app_manager.show()
#         sys.exit(app.exec())
#
#     except Exception as e:
#         print(f"Fatal error: {e}")
#         sys.exit(1)


def main():
    """Main entry point from MainWindow_gaming"""
    try:
        app = QApplication(sys.argv)
        app_manager = MainWindow(app_manager=None)
        app_manager.show()
        sys.exit(app.exec())

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
