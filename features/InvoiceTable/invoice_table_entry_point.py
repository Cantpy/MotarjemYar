import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from invoice_table_controller import MainController
from shared import return_resource


def main():
    """
    The main entry point of the application.
    It sets up the main window and integrates the invoice table feature.
    """
    app = QApplication(sys.argv)

    # Define database paths
    invoices_db_path = return_resource('databases', 'invoices.db')
    users_db_path = return_resource('databases', 'users.db')

    # 1. The main application window (as the parent for the view)
    main_window = QMainWindow()
    main_window.setWindowTitle("Invoice Management System")
    main_window.setGeometry(100, 100, 1200, 800)

    # 2. Instantiate the MainController, passing the main window as the parent for the view
    main_controller = MainController(
        invoices_db_url=f"sqlite:///{invoices_db_path}",
        users_db_url=f"sqlite:///{users_db_path}",
        parent_widget=main_window
    )

    # 3. Get the view widget from the controller
    invoice_widget = main_controller.get_widget()

    # 4. Set the widget as the central content of the main window
    main_window.setCentralWidget(invoice_widget)

    # 5. Tell the controller to load the initial data
    main_controller.load_initial_data()

    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    # Add dummy helper if not present, for standalone execution
    import os

    if not os.path.exists("helpers"):
        os.makedirs("helpers")
    if not os.path.exists("databases"):
        os.makedirs("databases")
    with open("helpers/__init__.py", "w") as f:
        pass
    with open("helpers/resources.py", "w") as f:
        f.write("import os\n\n")
        f.write("def return_resource(*args):\n")
        f.write("    return os.path.join(*args)\n")

    main()
