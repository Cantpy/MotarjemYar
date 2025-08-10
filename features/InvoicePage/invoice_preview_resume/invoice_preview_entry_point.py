"""
Example usage of the invoice preview system.
Shows how to integrate all components together.
"""

import sys
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.models.sqlalchemy_models import Base, IssuedInvoiceModel, InvoiceItemModel

# Import the invoice preview components
from features.InvoicePage.invoice_preview_resume.invoice_preview_repo import InvoicePreviewRepository
from features.InvoicePage.invoice_preview_resume.invoice_preview_logic import InvoicePreviewLogic
from features.InvoicePage.invoice_preview_resume.invoice_preview_controller import InvoicePreviewController
from features.InvoicePage.invoice_preview_resume.invoice_preview_view import InvoicePreviewView

from shared import return_resource

invoices_database = return_resource('databases', 'invoices.db')


class InvoicePreviewFactory:
    """Factory class for creating invoice preview instances."""

    def __init__(self, database_url: str):
        """Initialize the factory with database connection."""
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_invoice_preview(self, parent_invoice_widget, username: str) -> InvoicePreviewView:
        """Create a complete invoice preview instance."""
        # Create database session
        session = self.SessionLocal()

        # Create repository
        repository = InvoicePreviewRepository(session)

        # Create business logic layer
        logic = InvoicePreviewLogic(repository)

        # Create controller
        controller = InvoicePreviewController(logic)

        # Create view
        view = InvoicePreviewView(controller, parent_invoice_widget, username)

        return view


def show_invoice_preview(parent_invoice_widget, username: str, database_url: str = f"sqlite:///{invoices_database}"):
    """
    Convenience function to show invoice preview dialog.

    Args:
        parent_invoice_widget: The parent widget containing invoice data
        username: Current user's username
        database_url: Database connection URL

    Returns:
        InvoicePreviewView: The created preview view
    """
    factory = InvoicePreviewFactory(database_url)
    preview_view = factory.create_invoice_preview(parent_invoice_widget, username)

    # Show the dialog
    preview_view.show()

    return preview_view


def load_existing_invoice_preview(invoice_number: int, username: str, database_url: str = "sqlite:///invoices.db"):
    """
    Load and show preview of an existing invoice.

    Args:
        invoice_number: Invoice number to load
        username: Current user's username
        database_url: Database connection URL

    Returns:
        InvoicePreviewView: The created preview view, or None if invoice not found
    """
    factory = InvoicePreviewFactory(database_url)

    # Create components
    session = factory.SessionLocal()
    repository = InvoicePreviewRepository(session)
    logic = InvoicePreviewLogic(repository)
    controller = InvoicePreviewController(logic)

    # Load the invoice
    if controller.load_existing_invoice(invoice_number):
        # Create view without parent widget (since we're loading from DB)
        view = InvoicePreviewView(controller, None, username)
        view.show()
        return view
    else:
        return None


# Example integration with your existing invoice creation widget
class YourExistingInvoiceWidget:
    """Example of how to integrate with your existing invoice widget."""

    def __init__(self):
        self.database_url = "sqlite:///your_invoices.db"
        # ... your existing initialization code

    def show_invoice_preview(self, username: str):
        """Show preview of current invoice."""
        try:
            # Use the convenience function
            preview_view = show_invoice_preview(
                parent_invoice_widget=self,
                username=username,
                database_url=self.database_url
            )

            # Optional: Handle the preview result
            result = preview_view.exec()  # For modal dialog

            return result

        except Exception as e:
            print(f"Error showing invoice preview: {e}")
            return None

    def show_saved_invoice_preview(self, invoice_number: int, username: str):
        """Show preview of a previously saved invoice."""
        try:
            preview_view = load_existing_invoice_preview(
                invoice_number=invoice_number,
                username=username,
                database_url=self.database_url
            )

            if preview_view:
                return preview_view.exec()
            else:
                print(f"Invoice {invoice_number} not found")
                return None

        except Exception as e:
            print(f"Error loading invoice preview: {e}")
            return None

    # Mock methods that should exist in your actual widget
    def get_current_invoice_no(self) -> int:
        """Return current invoice number."""
        return 1001  # Mock value

    @property
    def ui(self):
        """Mock UI property."""

        class MockUI:
            def __init__(self):
                self.full_name_le = MockLineEdit("John Doe")
                self.national_id_le = MockLineEdit("1234567890")
                self.phone_le = MockLineEdit("09123456789")
                self.tableWidget = MockTableWidget()

        return MockUI()


class MockLineEdit:
    """Mock line edit for demonstration."""

    def __init__(self, text: str = ""):
        self._text = text

    def text(self) -> str:
        return self._text


class MockTableWidget:
    """Mock table widget for demonstration."""

    def __init__(self):
        self._data = [
            ["", "Document Translation", "1", "1", "0", "50000"],
            ["", "Certificate Translation", "2", "0", "1", "30000"],
            ["", "Passport Translation", "1", "1", "1", "25000"],
        ]

    def rowCount(self) -> int:
        return len(self._data)

    def columnCount(self) -> int:
        return 6

    def item(self, row: int, column: int):
        class MockItem:
            def __init__(self, text: str):
                self._text = text

            def text(self) -> str:
                return self._text

        if 0 <= row < len(self._data) and 0 <= column < len(self._data[row]):
            return MockItem(self._data[row][column])
        return MockItem("")


# Example of advanced usage with custom configuration
class AdvancedInvoicePreviewUsage:
    """Example of advanced usage patterns."""

    def __init__(self, database_url: str):
        self.factory = InvoicePreviewFactory(database_url)

    def create_custom_preview(self, parent_widget, username: str, custom_scale: str = "100%"):
        """Create preview with custom scale configuration."""
        # Create components
        session = self.factory.SessionLocal()
        repository = InvoicePreviewRepository(session)
        logic = InvoicePreviewLogic(repository)

        # Get custom scale configuration
        scale_config = logic.get_scale_config(custom_scale)

        controller = InvoicePreviewController(logic)

        # You could modify the controller's scale config here if needed
        controller.scale_config = scale_config

        view = InvoicePreviewView(controller, parent_widget, username)
        return view

    def batch_export_invoices(self, username: str, export_path: str):
        """Example of batch operations."""
        session = self.factory.SessionLocal()
        repository = InvoicePreviewRepository(session)
        logic = InvoicePreviewLogic(repository)

        # Get all user invoices
        invoices = logic.get_user_invoices(username)

        # Prepare export data
        export_data = logic.prepare_export_data(invoices)

        # Export to Excel (you'd need to implement the actual Excel export)
        print(f"Exporting {len(export_data)} invoices to {export_path}")

        session.close()

    def get_user_statistics(self, username: str) -> dict:
        """Get comprehensive user statistics."""
        session = self.factory.SessionLocal()
        repository = InvoicePreviewRepository(session)
        logic = InvoicePreviewLogic(repository)

        stats = logic.get_invoice_statistics(username)
        session.close()

        return {
            'total_invoices': stats.total_invoices,
            'total_revenue': stats.total_revenue,
            'average_amount': stats.average_invoice_amount,
            'total_documents': stats.total_official_docs + stats.total_unofficial_docs,
            'total_pages': stats.total_pages
        }


# Main execution example
def main():
    """Example of how to run the invoice preview system."""
    app = QApplication(sys.argv)

    # Create a mock invoice widget
    mock_invoice_widget = YourExistingInvoiceWidget()

    # Show preview for current invoice
    username = "test_user"
    result = mock_invoice_widget.show_invoice_preview(username)

    # Example of loading existing invoice
    # mock_invoice_widget.show_saved_invoice_preview(1001, username)

    # Example of advanced usage
    advanced_usage = AdvancedInvoicePreviewUsage("sqlite:///test_invoices.db")
    stats = advanced_usage.get_user_statistics(username)
    print("User Statistics:", stats)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# Integration helper functions
def integrate_with_existing_system(existing_invoice_class):
    """
    Helper function to integrate with existing invoice systems.

    Usage:
        @integrate_with_existing_system
        class YourInvoiceClass:
            # your existing code
            pass
    """

    def add_preview_functionality(cls):
        def show_preview(self, username: str, database_url: str = "sqlite:///invoices.db"):
            return show_invoice_preview(self, username, database_url)

        def show_saved_preview(self, invoice_number: int, username: str, database_url: str = "sqlite:///invoices.db"):
            return load_existing_invoice_preview(invoice_number, username, database_url)

        # Add methods to the class
        cls.show_preview = show_preview
        cls.show_saved_preview = show_saved_preview

        return cls

    return add_preview_functionality


# Example of decorator usage
@integrate_with_existing_system
class MyExistingInvoiceWidget:
    """Example of using the integration decorator."""

    def __init__(self):
        # Your existing initialization
        pass

    # Your existing methods...
    def get_current_invoice_no(self):
        return 1001


# Configuration management
class InvoicePreviewConfig:
    """Configuration management for invoice preview system."""

    DEFAULT_DATABASE_URL = "sqlite:///invoices.db"
    DEFAULT_SCALE = "100%"
    DEFAULT_STYLES_PATH = "styles/invoice_preview.qss"

    def __init__(self, **kwargs):
        self.database_url = kwargs.get('database_url', self.DEFAULT_DATABASE_URL)
        self.scale = kwargs.get('scale', self.DEFAULT_SCALE)
        self.styles_path = kwargs.get('styles_path', self.DEFAULT_STYLES_PATH)

    def create_factory(self) -> InvoicePreviewFactory:
        """Create factory with this configuration."""
        return InvoicePreviewFactory(self.database_url)


# Usage with configuration
def create_configured_preview(parent_widget, username: str, config: InvoicePreviewConfig = None):
    """Create preview with custom configuration."""
    if config is None:
        config = InvoicePreviewConfig()

    factory = config.create_factory()
    return factory.create_invoice_preview(parent_widget, username)
