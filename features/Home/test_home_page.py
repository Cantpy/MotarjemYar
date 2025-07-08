#!/usr/bin/env python3
"""
Test script for the home page components.
"""
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer

from features.Home import HomePageController


class TestMainWindow(QMainWindow):
    """Test main window for the home page."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Home Page Test")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create home page controller
        self.home_controller = HomePageController(self)
        layout.addWidget(self.home_controller)

        # Set up cleanup on close
        self.destroyed.connect(self.cleanup)

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'home_controller'):
            self.home_controller.cleanup()

    def closeEvent(self, event):
        """Handle window close event."""
        self.cleanup()
        event.accept()


def main():
    """Main function to run the test."""
    app = QApplication(sys.argv)

    # Create and show the main window
    window = TestMainWindow()
    window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
