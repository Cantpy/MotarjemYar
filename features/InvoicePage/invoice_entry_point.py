#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Invoice Application Entry Point
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from features.InvoicePage.invoice_page.invoice_page_view import InvoiceWizardView


def main():
    """Main entry point of the application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("سیستم فاکتور")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Your Company")

    # Set RTL layout direction for Persian
    app.setLayoutDirection(Qt.RightToLeft)

    # Create and show the main window
    window = InvoiceWizardView()
    window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
